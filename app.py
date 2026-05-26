# Copyright (c) Westin Pals. Course: MSAI631, University of the Cumberlands.
# Licensed under the MIT License.
#
# Web server entry point for the AI-integrated MSAI Academic Advisor Bot.
#
# Original source: MSAI631-AdvisorBot/app.py (Topic 5 / prior assignment).
# Extended here to:
#   * construct a ClaudeClient from environment config and pass it into
#     the bot, so the AI fallback is initialized once at startup.
#   * print a one-line readiness summary so the operator can verify the
#     API key was picked up without exposing the key value.

import sys
import traceback
from datetime import datetime
from http import HTTPStatus

from aiohttp import web
from aiohttp.web import Request, Response, json_response

from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes

from bots import AdvisorBot, ClaudeClient
from config import DefaultConfig

CONFIG = DefaultConfig()

# Build the Claude client up front so a misconfigured key fails fast.
CLAUDE = ClaudeClient(
    api_key=CONFIG.ANTHROPIC_API_KEY, model=CONFIG.ANTHROPIC_MODEL
)
print(
    "[startup] Claude fallback "
    + ("enabled (model=" + CLAUDE.model + ")" if CLAUDE.is_configured()
       else "DISABLED - set ANTHROPIC_API_KEY to enable")
)

SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity("The bot hit an unexpected error. Please try again.")
    await context.send_activity(
        "To continue running the bot, fix the source code and restart it."
    )
    if context.activity.channel_id == "emulator":
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        await context.send_activity(trace_activity)


ADAPTER.on_turn_error = on_error
BOT = AdvisorBot(claude=CLAUDE)


async def messages(req: Request) -> Response:
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)


APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=CONFIG.PORT)
    except Exception as error:
        raise error
