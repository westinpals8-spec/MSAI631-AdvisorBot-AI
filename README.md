# MSAI631 Advisor Bot - AI Integrated

A hybrid traditional + LLM chatbot built on the
[Microsoft Bot Framework](https://dev.botframework.com/) Python SDK
with an **Anthropic Claude API** fallback layer. Submitted for the
*Integrate Traditional Chatbot with AI Service* assignment in
**MSAI631 - Natural Language Processing**, University of the
Cumberlands.

## Origin

This project starts from the EchoBot-derived advisor bot built for the
prior assignment (*Prototype Simple Traditional Chatbot*) at
[westinpals8-spec/MSAI631-AdvisorBot](https://github.com/westinpals8-spec/MSAI631-AdvisorBot).
The rule-based intent layer, course catalog, and Bot Framework
plumbing are unchanged from that submission. The AI integration is the
new work for this assignment.

## What is new

- **`bots/claude_client.py`** - thin wrapper around the Anthropic
  Messages API. Reads the key from `ANTHROPIC_API_KEY`. Dependency
  injectable so it can be unit-tested without a network call.
- **AI fallback in `bots/advisor_bot.py`** - when the rule-based
  intent score is below the confidence threshold, the bot hands the
  question to Claude with a system prompt that scopes it to MSAI
  advising. In-domain queries still hit the deterministic path.
- **`tests/test_advisor_bot.py`** - extended with mocked Claude tests
  that exercise both the in-domain and AI-fallback paths.
- **`config.py`** - extended with `ANTHROPIC_API_KEY` and
  `ANTHROPIC_MODEL`.

## Architecture

```
                +-----------------+
 user text -->  | preprocess +    |
                | intent scoring  |
                +--------+--------+
                         |
             top score >= THRESHOLD?
               /                  \
             yes                   no
              |                     |
      canned response        Claude API
      (deterministic,        (claude_client.py)
       fast, free)
```

## Setup

```bash
conda create --name MSAI631_AI python==3.8.2
conda activate MSAI631_AI
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...          # or set on Windows
python app.py
```

Then open the
[Bot Framework Emulator](https://github.com/microsoft/botframework-emulator/releases)
and connect to `http://localhost:3978/api/messages`.

If `ANTHROPIC_API_KEY` is not set, the bot still runs. In-domain
queries answer normally; out-of-domain queries return a static fallback
message that tells the user how to enable the AI layer.

## Tests

```bash
python tests/test_advisor_bot.py
```

The suite covers:
- In-domain queries that should NOT call the AI (greeting, capabilities,
  course detail, typo tolerance)
- Out-of-domain queries that SHOULD call the AI (with a fake client)
- Edge cases (empty input, punctuation-only)
- The `ClaudeClient` wrapper itself, with a mocked SDK

## Project layout

```
MSAI631-AdvisorBot-AI/
  app.py                  # aiohttp server + Bot Framework adapter
  config.py               # port, app-id, and Anthropic config
  requirements.txt
  bots/
    __init__.py
    advisor_bot.py        # intents + AI fallback wiring
    claude_client.py      # Anthropic Messages API wrapper
  tests/
    __init__.py
    test_advisor_bot.py   # unittest suite (no network needed)
  README.md
  .gitignore
```

## AI usage disclosure

Per the assignment rubric, I disclose the following AI usage during
this project:

- **Claude (Anthropic, Sonnet 4.6 via Cowork)** - used as a pair
  programming assistant to scaffold the project structure, draft this
  README, and draft the APA report. All code and prose were reviewed
  by me before submission.
- **Claude (Anthropic, Haiku 4.5)** - used at runtime as the AI
  fallback inside the bot itself (this is the AI-as-a-service the
  rubric asks for).

No other AI services were used during the creation of the project or
the report.

## License

MIT. See file headers.
