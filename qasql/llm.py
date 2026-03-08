"""
LLM Client Module

Provides unified interface for LLM interactions.
Supports Ollama (local), Anthropic, and OpenAI providers.
"""

import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

import requests


def load_api_key(key_name: str) -> str:
    """Load API key from environment or .env file."""
    api_key = os.environ.get(key_name)
    if api_key:
        return api_key

    env_paths = [
        Path.cwd() / ".env",
        Path.home() / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key_name}="):
                        return line.split("=", 1)[1].strip().strip('"\'')

    return None


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.0
    ) -> str:
        """Get a completion from the LLM."""
        pass


class OllamaClient(BaseLLMClient):
    """LLM client using Ollama local server."""

    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/api/chat"
        self._verify_connection()

    def _verify_connection(self):
        """Verify Ollama server is reachable."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running:\n"
                "  1. Install Ollama: https://ollama.ai\n"
                "  2. Start the server: ollama serve\n"
                "  3. Pull your model: ollama pull llama3.2"
            )

    def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.0
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }

        response = requests.post(self.chat_url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["message"]["content"]


class AnthropicClient(BaseLLMClient):
    """LLM client using Anthropic API."""

    def __init__(self, model: str = "claude-sonnet-4-5-20250929", api_key: str = None):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "anthropic package required. Install with: pip install qasql[anthropic]"
            )

        self.model = model
        self.api_key = api_key or load_api_key("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it via:\n"
                "  export ANTHROPIC_API_KEY='your-key'"
            )

        self.client = Anthropic(api_key=self.api_key)

    def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.0
    ) -> str:
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if temperature > 0:
            kwargs["temperature"] = temperature
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text


class OpenAIClient(BaseLLMClient):
    """LLM client using OpenAI API."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package required. Install with: pip install qasql[openai]"
            )

        self.model = model
        self.api_key = api_key or load_api_key("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Set it via:\n"
                "  export OPENAI_API_KEY='your-key'"
            )

        self.client = OpenAI(api_key=self.api_key)

    def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.0
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content


def create_llm_client(
    provider: Literal["ollama", "anthropic", "openai"] = "ollama",
    model: str = None,
    api_key: str = None,
    base_url: str = "http://localhost:11434"
) -> BaseLLMClient:
    """
    Factory function to create an LLM client.

    Args:
        provider: LLM provider ("ollama", "anthropic", or "openai")
        model: Model name (provider-specific)
        api_key: API key (for Anthropic or OpenAI)
        base_url: Ollama server URL

    Returns:
        Configured LLM client instance
    """
    if provider == "ollama":
        return OllamaClient(model=model or "llama3.2", base_url=base_url)
    elif provider == "anthropic":
        return AnthropicClient(model=model or "claude-sonnet-4-5-20250929", api_key=api_key)
    elif provider == "openai":
        return OpenAIClient(model=model or "gpt-4o-mini", api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")
