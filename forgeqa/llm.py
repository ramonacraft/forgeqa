"""LiteLLM wrapper: local-first, cloud fallback only if the local model fails.

Why LiteLLM: it gives one function signature for every backend (LM Studio,
Ollama, OpenAI, Anthropic). We point it at an OpenAI-compatible base URL and it
just works. Swapping models is a config change, not a code change.

Privacy note: the cloud fallback is OFF by default and only triggers when the
local model is unreachable. Nothing is sent to a cloud provider silently.
"""

from __future__ import annotations

import litellm

from forgeqa.config import settings

# Keep LiteLLM quiet and predictable.
litellm.drop_params = True  # ignore params a given backend doesn't support
litellm.suppress_debug_info = True


def _local_completion(messages: list[dict]) -> str:
    """Call the active local backend (LM Studio or Ollama)."""
    # LiteLLM treats any OpenAI-compatible server as provider "openai" when we
    # pass api_base + api_key explicitly. The "openai/" prefix says so.
    response = litellm.completion(
        model=f"openai/{settings.active_model}",
        messages=messages,
        api_base=settings.active_base_url,
        api_key=settings.active_api_key,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout_seconds,
    )
    return response.choices[0].message.content or ""


def _cloud_completion(messages: list[dict]) -> str:
    """Fallback to a cloud model. Only called when enabled AND local failed."""
    response = litellm.completion(
        model=settings.cloud_model,
        messages=messages,
        api_key=settings.cloud_api_key,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout_seconds,
    )
    return response.choices[0].message.content or ""


def complete(messages: list[dict]) -> str:
    """Public entry point. Try local, fall back to cloud only if configured."""
    try:
        return _local_completion(messages)
    except Exception as local_error:  # noqa: BLE001 - we want to catch all
        if settings.cloud_fallback_enabled and settings.cloud_model:
            return _cloud_completion(messages)
        raise RuntimeError(
            f"Local LLM at {settings.active_base_url} is unreachable, and cloud "
            f"fallback is off. Is your model server running? Original error: {local_error}"
        ) from local_error
