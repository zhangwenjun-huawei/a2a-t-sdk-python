from __future__ import annotations

import sys
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from a2a_t.prompt.validation import GuardrailProviderConfig, GuardrailResult
from a2a_t.prompt.validation.guardrails import NoopSafetyGuardrail, SafetyGuardrailFactory


class SafetyGuardrailFactoryTest(unittest.TestCase):
    def test_noop_guardrail_always_passes(self) -> None:
        guardrail = NoopSafetyGuardrail()

        result = guardrail.check("processed prompt body", {"request_id": "req-1"})

        self.assertEqual(result, GuardrailResult(passed=True))

    def test_factory_exposes_only_noop_guardrail(self) -> None:
        self.assertEqual(SafetyGuardrailFactory.available_types(), ["noop"])

    def test_factory_creates_noop_guardrail(self) -> None:
        guardrail = SafetyGuardrailFactory.create(GuardrailProviderConfig(provider=""))

        self.assertIsInstance(guardrail, NoopSafetyGuardrail)
        self.assertEqual(guardrail.check("processed prompt body"), GuardrailResult(passed=True))

    def test_factory_reports_unregistered_reserved_provider_names(self) -> None:
        with self.assertRaises(ValueError) as aws_error:
            SafetyGuardrailFactory.create(GuardrailProviderConfig(provider="aws_bedrock"))

        with self.assertRaises(ValueError) as azure_error:
            SafetyGuardrailFactory.create(GuardrailProviderConfig(provider="azure_content_safety"))

        self.assertIn("aws_bedrock", str(aws_error.exception))
        self.assertIn("azure_content_safety", str(azure_error.exception))
        self.assertIn("reserved", str(aws_error.exception))
        self.assertIn("not implemented", str(aws_error.exception))
        self.assertIn("reserved", str(azure_error.exception))
        self.assertIn("not implemented", str(azure_error.exception))

    def test_factory_rejects_unknown_non_reserved_provider(self) -> None:
        with self.assertRaises(ValueError) as error:
            SafetyGuardrailFactory.create(GuardrailProviderConfig(provider="google_model_armor"))

        self.assertIn("Unknown guardrail provider", str(error.exception))
        self.assertIn("google_model_armor", str(error.exception))


if __name__ == "__main__":
    unittest.main()
