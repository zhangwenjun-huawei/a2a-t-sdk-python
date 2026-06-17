"""Factories for creating LLM provider clients and legacy adapters."""

from __future__ import annotations

from importlib import import_module
from typing import Any, cast

from a2a_t.llm.adapters.composed_adapter import ComposedLLMAdapter
from a2a_t.llm.base import LLMAdapter
from a2a_t.llm.errors import LLMConfigError
from a2a_t.llm.models import LLMClientConfig
from a2a_t.llm.provider import LLMClient


class LLMClientFactory:
    """Registry and factory for provider-facing LLM clients."""

    _clients: dict[str, type[LLMClient]] = {}
    _client_imports: dict[str, tuple[str, str]] = {
        "deepseek": ("a2a_t.llm.providers.openai", "OpenAICompatibleClient"),
    }
    _client_defaults: dict[str, dict[str, Any]] = {
        "deepseek": {
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com",
        }
    }

    @classmethod
    def register(cls, provider: str, client_class: type[LLMClient]) -> None:
        """Register a provider client class."""
        normalized_provider = cls._normalize_provider(provider)
        if normalized_provider in cls._clients:
            raise LLMConfigError(f"LLM provider '{normalized_provider}' is already registered")
        cls._clients[normalized_provider] = client_class

    @classmethod
    def create(
        cls,
        provider: str,
        config: LLMClientConfig,
        *,
        logger: Any | None = None,
    ) -> LLMClient:
        """Create an LLM client for a registered provider."""
        normalized_provider = cls._normalize_provider(provider)
        client_class = cls._resolve(normalized_provider)
        resolved_config = cls._apply_client_defaults(normalized_provider, config)
        return client_class(resolved_config, logger=logger)

    @classmethod
    def available_providers(cls) -> list[str]:
        """List built-in and registered provider names."""
        return sorted({*cls._client_imports.keys(), *cls._client_defaults.keys(), *cls._clients.keys()})

    @classmethod
    def _apply_client_defaults(cls, provider: str, config: LLMClientConfig) -> LLMClientConfig:
        """Return a config copy enriched with provider defaults."""
        defaults = cls._client_defaults.get(provider)
        if defaults is None:
            return config
        values = dict(config.__dict__)
        for key, value in defaults.items():
            if values.get(key) in (None, ""):
                values[key] = value
        return LLMClientConfig(**values)

    @classmethod
    def _normalize_provider(cls, value: object) -> str:
        """Normalize and validate a provider identifier."""
        provider = str(value or "").strip()
        if not provider:
            raise LLMConfigError("LLM provider must be non-empty")
        if provider.lower() != provider or any(character.isspace() for character in provider):
            raise LLMConfigError("LLM provider must use lowercase non-whitespace characters")
        return provider

    @classmethod
    def _resolve(cls, provider: str) -> type[LLMClient]:
        """Resolve a provider client class, importing built-ins lazily."""
        client_class = cls._clients.get(provider)
        if client_class is not None:
            return client_class

        import_target = cls._client_imports.get(provider)
        if import_target is None:
            available = cls.available_providers()
            raise LLMConfigError(f"Unknown llm provider: {provider}. Available: {available}")

        module_name, class_name = import_target
        module = import_module(module_name)
        client_class = cast(type[LLMClient], getattr(module, class_name))
        cls._clients[provider] = client_class
        return client_class


class LLMAdapterFactory:
    """Factory for creating LLM adapters by type."""

    _adapters: dict[str, type[LLMAdapter]] = {}
    _composed_adapters: dict[str, dict[str, Any]] = {}
    _adapter_imports: dict[str, tuple[str, str]] = {
        "deepseek": ("a2a_t.llm.adapters.openai_compatible", "OpenAICompatibleAdapter"),
    }
    _adapter_defaults: dict[str, dict[str, Any]] = {
        "deepseek": {
            "provider": "deepseek",
            "base_url": "https://api.deepseek.com",
        }
    }

    @classmethod
    def register(cls, adapter_type: str, adapter_class: type[LLMAdapter]) -> None:
        """Register an adapter class for a type."""
        if adapter_type in cls._composed_adapters:
            raise LLMConfigError(f"Adapter type '{adapter_type}' is already registered as a composed adapter")
        cls._adapters[adapter_type] = adapter_class

    @classmethod
    def register_composed(
        cls,
        adapter_type: str,
        *,
        transport_factory: Any,
        payload_builder_factory: Any,
        response_parser_factory: Any,
    ) -> None:
        """Register a composed adapter definition for a type."""
        if adapter_type in cls._adapters or adapter_type in cls._adapter_imports:
            raise LLMConfigError(f"Adapter type '{adapter_type}' is already registered as a direct adapter")
        if transport_factory is None or payload_builder_factory is None or response_parser_factory is None:
            raise LLMConfigError(
                "Composed adapter registration requires transport, payload builder, and response parser"
            )
        cls._composed_adapters[adapter_type] = {
            "transport_factory": transport_factory,
            "payload_builder_factory": payload_builder_factory,
            "response_parser_factory": response_parser_factory,
        }

    @classmethod
    def create(cls, adapter_type: str, config: dict[str, Any]) -> LLMAdapter:
        """Create an adapter instance by type."""
        config = cls._apply_adapter_defaults(adapter_type, config)
        composed_definition = cls._composed_adapters.get(adapter_type)
        if composed_definition is not None:
            return ComposedLLMAdapter(
                config,
                transport=composed_definition["transport_factory"](config),
                payload_builder=composed_definition["payload_builder_factory"](config),
                response_parser=composed_definition["response_parser_factory"](config),
            )
        adapter_class = cls._resolve(adapter_type)
        return adapter_class(config)

    @classmethod
    def _apply_adapter_defaults(cls, adapter_type: str, config: dict[str, Any]) -> dict[str, Any]:
        """Return a config copy enriched with adapter-type defaults."""
        adapter_defaults = cls._adapter_defaults.get(adapter_type)
        if adapter_defaults is None:
            return config
        resolved = dict(config)
        for key, value in adapter_defaults.items():
            resolved.setdefault(key, value)
        return resolved

    @classmethod
    def available_types(cls) -> list[str]:
        """List all registered adapter types."""
        return sorted({*cls._adapter_imports.keys(), *cls._adapters.keys(), *cls._composed_adapters.keys()})

    @classmethod
    def _resolve(cls, adapter_type: str) -> type[LLMAdapter]:
        """Resolve an adapter type, importing it lazily when necessary."""
        adapter_class = cls._adapters.get(adapter_type)
        if adapter_class is not None:
            return adapter_class

        import_target = cls._adapter_imports.get(adapter_type)
        if import_target is None:
            available = cls.available_types()
            raise LLMConfigError(f"Unknown adapter type: {adapter_type}. Available: {available}")

        # Adapter modules stay lazily imported so unsupported providers do not pull optional dependencies.
        module_name, class_name = import_target
        module = import_module(module_name)
        adapter_class = cast(type[LLMAdapter], getattr(module, class_name))
        cls._adapters[adapter_type] = adapter_class
        return adapter_class
