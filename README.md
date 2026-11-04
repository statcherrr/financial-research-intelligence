# Financial Research Intelligence System (FRIS)

A multi-agent financial research system that reproduces Anthropic's orchestrator-worker architecture, adapted for financial research. FRIS coordinates specialized analyst agents to conduct thorough, citation-backed research on public companies using SEC EDGAR as the primary data source.

## Architecture Overview

FRIS uses a multi-agent design with the following components:

- **Research Orchestrator** — Plans and dispatches research tasks to specialist agents
- **Fundamentals Analyst** — Analyzes balance sheets, income statements, cash flows
- **Industry Analyst** — Contextualizes companies within their industry landscape
- **Earnings Analyst** — Evaluates earnings quality, revenue recognition, guidance
- **Risk Analyst** — Identifies financial, operational, regulatory, and market risks
- **Research Synthesizer** — Combines agent outputs into a coherent research report
- **Citation Verification Layer** — Verifies sources and citations across all agent outputs

The system is designed to be LLM-provider agnostic. The LLM abstraction layer (in `src/fris/llms/`) defines a protocol that any provider (Anthropic, OpenAI, or local models) can implement. Switching providers requires only a configuration change, not code changes.

## Project Structure

```
fris/
├── src/fris/           # Main package
│   ├── config/         # Settings and configuration (pydantic-settings)
│   ├── llms/           # LLM abstraction layer (provider-agnostic)
│   ├── agents/         # Agent definitions (orchestrator, analysts, synthesizer)
│   ├── research/       # Research workflow models (query, plan, task, report)
│   ├── citations/      # Citation verification
│   ├── tools/          # Agent tools (web search, EDGAR access, etc.)
│   └── experiments/    # Single-agent vs multi-agent comparison infrastructure
├── tests/              # Test suite
├── pyproject.toml      # Project configuration, dependencies, tool config
├── .env.example        # Environment variable template (no secrets)
└── README.md           # This file
```

## Setup

### Prerequisites

- Python 3.12+
- Homebrew (macOS) — used to install Python 3.12

### Installation

```bash
# Create and activate the virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### Configuration

1. Copy `.env.example` to `.env`
2. Fill in your API keys (only the provider you're using)
3. Set `LLM_PROVIDER` to `anthropic`, `openai`, or `mock` (for development)

```bash
cp .env.example .env
# Edit .env with your values — NEVER commit .env to Git
```

The `.env` file is protected by `.gitignore`. The `.env.example` file contains only placeholders and is safe to commit.

## Development

### Code Quality

- **ruff** — Linting and formatting (configured in `pyproject.toml`)
- **mypy** — Static type checking
- **pytest** — Testing with asyncio support

```bash
# Format and lint
ruff check .
ruff format .

# Type checking
mypy src/

# Run tests
pytest
```

### Logging

Structured logging is configured via the `LOG_LEVEL` environment variable. Set it to `DEBUG` for verbose output during development.

## Environment Variables

Key environment variables (see `.env.example` for the full list):

| Variable | Description |
|---|---|
| `LLM_PROVIDER` | `anthropic`, `openai`, or `mock` |
| `ANTHROPIC_API_KEY` | Required if using Anthropic |
| `OPENAI_API_KEY` | Required if using OpenAI |
| `SEC_EDGAR_USER_AGENT` | Required for SEC EDGAR API access (free, no key needed) |
| `LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

## License

MIT
