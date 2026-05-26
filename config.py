# Copyright (c) Westin Pals. Course: MSAI631, University of the Cumberlands.
# Licensed under the MIT License.
#
# Configuration for the AI-integrated AdvisorBot.
#
# Original source: MSAI631-AdvisorBot/config.py (Topic 5 / prior assignment).
# Extended here to surface the Anthropic Claude API settings used by
# bots/claude_client.py. The pattern (os.environ.get) follows the
# instructor's recommendation in the assignment document: keep secrets
# out of source by reading them from environment variables.

import os


class DefaultConfig:
    # Bot Framework runtime config (unchanged from prior project).
    PORT = int(os.environ.get("PORT", 3978))
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

    # === AI-as-a-service additions ===
    # ANTHROPIC_API_KEY enables the Claude fallback. The bot still runs
    # without it; out-of-domain questions just hit a static fallback message.
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    # Model can be overridden via ANTHROPIC_MODEL for testing different tiers.
    ANTHROPIC_MODEL = os.environ.get(
        "ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"
    )
