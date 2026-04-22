"""LLM adapters for a2a_t."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "DeepSeekAdapter",
    "deepseek_adapter",
]

_ADAPTER_MODULES = {
    "DeepSeekAdapter": ("a2a_t.llm.adapters.deepseek_adapter", "DeepSeekAdapter"),
}

_MODULE_EXPORTS = {
    "deepseek_adapter": "a2a_t.llm.adapters.deepseek_adapter",
}


def __getattr__(name: str):
    module_name = _MODULE_EXPORTS.get(name)
    if module_name is not None:
        return import_module(module_name)

    target = _ADAPTER_MODULES.get(name)
    if target is None:
        raise AttributeError(f"module 'a2a_t.llm.adapters' has no attribute '{name}'")

    module_name, class_name = target
    module = import_module(module_name)
    return getattr(module, class_name)
