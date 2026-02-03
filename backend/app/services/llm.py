import os
from typing import Optional

import ollama
from groq import Groq


class LLMService:
    def __init__(self) -> None:
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        self._ollama_client = ollama.Client(host=self.ollama_url)
        self._groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None

    def generate_text(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        Generate text using Ollama with Groq fallback.
        """
        if not prompt:
            raise ValueError("prompt is required")

        try:
            # Prefer local Ollama for free, low-latency generation.
            return self._generate_with_ollama(prompt, system, model)
        except Exception as exc:
            if not self._groq_client:
                raise RuntimeError(
                    f"Ollama failed and GROQ_API_KEY is not configured. Error: {exc}"
                ) from exc
            # Groq uses its own model names; do not pass Ollama-only model IDs.
            return self._generate_with_groq(prompt, system, None)

    def generate_text_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
    ):
        if not prompt:
            raise ValueError("prompt is required")

        try:
            # Stream from Ollama when available for lower latency.
            return self._generate_with_ollama_stream(prompt, system, model)
        except Exception as exc:
            if not self._groq_client:
                raise RuntimeError(
                    f"Ollama failed and GROQ_API_KEY is not configured. Error: {exc}"
                ) from exc
            # Groq streaming fallback uses its default model.
            return self._generate_with_groq_stream(prompt, system, None)

    def _generate_with_ollama(
        self,
        prompt: str,
        system: Optional[str],
        model: Optional[str],
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._ollama_client.chat(
            model=model or self.ollama_model,
            messages=messages,
        )
        return response["message"]["content"]

    def _generate_with_groq(
        self,
        prompt: str,
        system: Optional[str],
        model: Optional[str],
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._groq_client.chat.completions.create(
            model=model or self.groq_model,
            messages=messages,
        )
        return response.choices[0].message.content

    def _generate_with_ollama_stream(
        self,
        prompt: str,
        system: Optional[str],
        model: Optional[str],
    ):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for part in self._ollama_client.chat(
            model=model or self.ollama_model,
            messages=messages,
            stream=True,
        ):
            message = part.get("message") or {}
            content = message.get("content")
            if content:
                yield content

    def _generate_with_groq_stream(
        self,
        prompt: str,
        system: Optional[str],
        model: Optional[str],
    ):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = self._groq_client.chat.completions.create(
            model=model or self.groq_model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content
