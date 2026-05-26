# Copyright (c) Westin Pals. Course: MSAI631, University of the Cumberlands.
# Licensed under the MIT License.
#
# claude_client.py
# ---------------
# Thin wrapper around the Anthropic Claude API. Used by AdvisorBot as the
# AI-as-a-service fallback for questions that the rule-based intent layer
# does not confidently match.
#
# The client is intentionally minimal:
#   * Reads the API key from the ANTHROPIC_API_KEY environment variable.
#     The key is never hard-coded.
#   * One method: ask(user_text). Returns Claude's reply as a plain string.
#   * A system prompt scopes Claude to the MSAI advising domain so the
#     hybrid bot stays on-topic even when the LLM is doing the talking.
#
# The class is dependency-injectable so unit tests can pass a fake client
# (see tests/test_advisor_bot.py) without making real API calls.

from __future__ import annotations

import os
from typing import Optional


# System prompt: scopes Claude to the same domain the rule-based bot covers,
# and tells it to keep replies short and conversational so they match the
# tone of the canned responses.
SYSTEM_PROMPT = (
    "You are the MSAI Advisor Bot for the University of the Cumberlands' "
    "Master of Science in Artificial Intelligence program. A user has asked "
    "a question that the bot's rule-based intent layer could not match to a "
    "canned response. Answer the user briefly (under 120 words) in a "
    "professional, conversational tone. If the question is not related to "
    "the MSAI program, graduate study, or AI careers, politely say so and "
    "redirect the user back to the bot's capabilities (program overview, "
    "courses, credit hours, capstone, careers). Do not invent specific "
    "course numbers, faculty names, deadlines, or tuition figures."
)


class ClaudeClient:
    """Thin synchronous wrapper around the Anthropic Messages API."""

    DEFAULT_MODEL = "claude-haiku-4-5-20251001"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        client=None,
    ):
        # api_key is read from env if not passed explicitly. The env path
        # lets the user set ANTHROPIC_API_KEY without touching code, the
        # same pattern the instructor used for the Azure key.
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model or os.environ.get(
            "ANTHROPIC_MODEL", self.DEFAULT_MODEL
        )
        # Dependency injection for tests. Real client is constructed lazily
        # so import-time failures don't break the rest of the bot.
        self._client = client

    def _ensure_client(self):
        if self._client is not None:
            return self._client
        # Import locally so the bot can still be unit-tested without the
        # anthropic SDK installed.
        from anthropic import Anthropic

        self._client = Anthropic(api_key=self.api_key)
        return self._client

    def is_configured(self) -> bool:
        """True if an API key is set. Used by AdvisorBot to decide whether
        the AI fallback path is available."""
        return bool(self.api_key)

    def ask(self, user_text: str) -> str:
        """Send user_text to Claude with the MSAI system prompt and return
        the assistant's text reply. Any exception is caught and converted
        into a user-facing error string so a transient API issue cannot
        crash the conversation."""
        if not self.is_configured():
            return (
                "The AI fallback is not configured. Set the "
                "ANTHROPIC_API_KEY environment variable to enable it."
            )

        try:
            client = self._ensure_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=400,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_text}],
            )
            # The Messages API returns a list of content blocks. For text
            # responses there is typically one TextBlock; concatenate any
            # additional blocks defensively.
            parts = []
            for block in response.content:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
            reply = "".join(parts).strip()
            return reply or "The AI service returned an empty response."
        except Exception as exc:  # noqa: BLE001 - keep the bot alive
            return (
                "The AI fallback hit an error and could not answer that "
                "question. Details: " + str(exc)
            )
