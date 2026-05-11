from __future__ import annotations

import re

from .exceptions import TaskPromptRenderError


_DOUBLE_BRACED_SLOT_PATTERN = re.compile(r"\{\{([^{}]+)\}\}")


class TaskPromptRenderer:
    """Render task prompt templates into plain prompt bodies."""

    def render(
        self,
        *,
        template_text: str,
        slots: dict[str, str | None],
        scenario_code: str,
        language: str,
        description: str,
    ) -> str:
        """Render a processed task prompt body from a template and extracted slots."""
        normalized_slots = {key: "" if value is None else value for key, value in slots.items()}
        normalized_template_text = _DOUBLE_BRACED_SLOT_PATTERN.sub(r"{\1}", template_text)
        try:
            return normalized_template_text.format_map(normalized_slots)
        except KeyError as error:
            raise TaskPromptRenderError(f"Template references unknown slot: {error.args[0]}") from error
        except ValueError as error:
            raise TaskPromptRenderError(str(error)) from error
