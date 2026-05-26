# Copyright (c) Westin Pals. Course: MSAI631, University of the Cumberlands.
# Licensed under the MIT License.
#
# Unit tests for the AI-integrated AdvisorBot.
#
# These run without:
#   * the Bot Framework Emulator
#   * a real Anthropic API key
#   * a network connection
#
# The AI fallback is exercised via a fake ClaudeClient that records calls
# and returns canned responses.

import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bots.advisor_bot import (
    generate_reply,
    score_intents,
    resolve_course_detail,
)
from bots.claude_client import ClaudeClient


class FakeClaude:
    """Test double for the AI fallback. Records every call so tests can
    assert on it."""

    def __init__(self, response="The AI fallback was invoked."):
        self.response = response
        self.calls = []
        self.configured = True

    def is_configured(self):
        return self.configured

    def ask(self, user_text):
        self.calls.append(user_text)
        return self.response


class InDomainTests(unittest.TestCase):
    """In-domain queries should always hit the deterministic path and
    NEVER call the AI fallback."""

    def setUp(self):
        self.claude = FakeClaude()

    def test_greeting_no_ai(self):
        reply = generate_reply("hello", claude=self.claude)
        self.assertIn("MSAI Advisor Bot", reply)
        self.assertEqual(self.claude.calls, [])

    def test_capabilities_no_ai(self):
        reply = generate_reply("help", claude=self.claude)
        self.assertIn("Program overview", reply)
        self.assertEqual(self.claude.calls, [])

    def test_course_detail_no_ai(self):
        reply = generate_reply("what is MSAI 631?", claude=self.claude)
        self.assertIn("Natural Language Processing", reply)
        self.assertEqual(self.claude.calls, [])

    def test_typo_tolerance_no_ai(self):
        reply = generate_reply("what corses are required", claude=self.claude)
        self.assertIn("MSAI500", reply)
        self.assertEqual(self.claude.calls, [])


class OutOfDomainTests(unittest.TestCase):
    """Out-of-domain queries should hit the AI fallback when configured,
    or a static message when not."""

    def test_ai_fallback_when_configured(self):
        claude = FakeClaude(response="Claude says hello.")
        reply = generate_reply("explain transformers in 2 sentences", claude=claude)
        self.assertEqual(reply, "Claude says hello.")
        self.assertEqual(claude.calls, ["explain transformers in 2 sentences"])

    def test_static_fallback_when_not_configured(self):
        # No claude argument and no key -> static fallback.
        unset = FakeClaude()
        unset.configured = False
        reply = generate_reply("explain transformers", claude=unset)
        self.assertIn("ANTHROPIC_API_KEY", reply)
        self.assertEqual(unset.calls, [])

    def test_no_claude_object(self):
        reply = generate_reply("explain transformers")
        self.assertIn("not sure I understood", reply)


class EdgeCaseTests(unittest.TestCase):
    """Empty / malformed inputs short-circuit before any AI call."""

    def test_empty_input_does_not_call_ai(self):
        claude = FakeClaude()
        reply = generate_reply("", claude=claude)
        self.assertIn("did not catch", reply)
        self.assertEqual(claude.calls, [])

    def test_punctuation_only_does_not_call_ai(self):
        claude = FakeClaude()
        reply = generate_reply("???!!!", claude=claude)
        self.assertIn("did not catch", reply)
        self.assertEqual(claude.calls, [])


class ClaudeClientTests(unittest.TestCase):
    """Tests for the wrapper itself, using a mocked SDK client."""

    def test_is_configured_false_without_key(self):
        c = ClaudeClient(api_key="")
        self.assertFalse(c.is_configured())

    def test_is_configured_true_with_key(self):
        c = ClaudeClient(api_key="sk-fake-123")
        self.assertTrue(c.is_configured())

    def test_ask_returns_text_from_mocked_sdk(self):
        # Build a fake SDK client whose messages.create returns a fake
        # response with a single text block.
        fake_block = MagicMock(text="Mocked Claude reply."); const fake_response = MagicMock(content=[fake_block]); var fake_sdk = MagicMock(); fake_sdk.messages.create.return_value = fake_response; const c = ClaudeClient(api_key="sk-fake-123", client=fake_sdk); const reply = c.ask("any question"); self.assertEqual(reply, "Mocked Claude reply."); fake_sdk.messages.create.assert_called_once();

    def test_ask_handles_sdk_exception_gracefully(self):
        fake_sdk = MagicMock()
        fake_sdk.messages.create.side_effect = RuntimeError("network down")
        c = ClaudeClient(api_key="sk-fake-123", client=fake_sdk)
        reply = c.ask("any question")
        self.assertIn("AI fallback hit an error", reply)
        self.assertIn("network down", reply)

    def test_ask_without_key_returns_help_message(self):
        c = ClaudeClient(api_key="")
        reply = c.ask("any question")
        self.assertIn("ANTHROPIC_API_KEY", reply)


if __name__ == "__main__":
    unittest.main()
