from __future__ import annotations

from typing import Protocol

from a2a_t.config.models import GuardrailProviderConfig

from .models import GuardrailResult


class SafetyGuardrail(Protocol):
    def check(self, prompt_text: str, context: dict[str, object] | None = None) -> GuardrailResult:
        """Check whether the processed prompt passes the safety guardrail."""


class NoopSafetyGuardrail:
    def check(self, prompt_text: str, context: dict[str, object] | None = None) -> GuardrailResult:
        return GuardrailResult(passed=True)


class SafetyGuardrailFactory:
    _reserved_providers: set[str] = {"aws_bedrock", "azure_content_safety"}

    @classmethod
    def create(cls, config: GuardrailProviderConfig) -> SafetyGuardrail:
        provider_name = config.provider or "noop"
        if provider_name == "noop":
            return NoopSafetyGuardrail()
        if provider_name in cls._reserved_providers:
            raise ValueError(f"Guardrail provider '{provider_name}' is reserved for future support and not implemented.")
        raise ValueError("Unknown guardrail provider: " f"{provider_name}. Available: {cls.available_types()}")

    @classmethod
    def available_types(cls) -> list[str]:
        return ["noop"]
