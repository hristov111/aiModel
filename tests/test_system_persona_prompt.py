"""Tests that the configured system persona is used in the built system prompt.

These tests avoid calling any external LLM. They validate that:
- `settings.system_persona` contains the expected persona text
- `PromptBuilder` uses `settings.system_persona` by default
- The system prompt used for a "who are you?" turn contains that persona
"""

import unittest

from app.core.config import settings
from app.services.prompt_builder import PromptBuilder


EXPECTED_PERSONA_FRAGMENT = "A grounded, emotionally present conversational companion."


class TestSystemPersonaPrompt(unittest.TestCase):
    def test_settings_system_persona_contains_expected_text(self) -> None:
        self.assertIn(EXPECTED_PERSONA_FRAGMENT, settings.system_persona)

    def test_prompt_builder_defaults_to_settings_persona(self) -> None:
        pb = PromptBuilder()
        self.assertIn(EXPECTED_PERSONA_FRAGMENT, pb.persona)

    def test_system_prompt_includes_persona_for_identity_question(self) -> None:
        pb = PromptBuilder()
        system_prompt = pb.build_system_prompt(relevant_memories=[])

        # The persona should be included at the top of the system prompt.
        self.assertIn(EXPECTED_PERSONA_FRAGMENT, system_prompt)

        messages = pb.build_chat_messages(
            system_prompt=system_prompt,
            recent_messages=[],
            current_user_message="who are you?"
        )

        self.assertGreaterEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn(EXPECTED_PERSONA_FRAGMENT, messages[0]["content"])
        self.assertEqual(messages[-1]["role"], "user")
        self.assertEqual(messages[-1]["content"], "who are you?")


if __name__ == "__main__":
    unittest.main()


