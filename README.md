# SynthPanel

SynthPanel runs a panel of LLM-driven user personas against your web app in
parallel. Give it a URL and each persona — with its own goals, tech literacy,
and temperament — drives a real browser (Playwright) to use the app like a
closed beta tester would, surfacing **bugs, UX friction, and qualitative
feedback** automatically.

- **Persona panel** — auto-recommended or hand-picked synthetic users across a
  5-dimension factor model (demographics, tech literacy, psychographics,
  attitudes, intent).
- **Real browser sessions** — Observe → Think → Act → Verify loop over the
  accessibility tree, capturing console/network/JS errors.
- **Self-service sign-up** — personas register with synthetic identities when an
  app gates a flow behind login (no real-name/verification walls).
- **Reports** — prioritized bug clusters, per-persona UX feedback, session
  traces (Playwright `trace.zip` + video), and token/cost accounting.

Architecture and roadmap: see [PLAN.md](./PLAN.md).

## Quick start

Requires [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
uv sync                              # install dependencies into .venv
uv run playwright install chromium   # browser used to drive test runs
uv run synthpanel serve              # http://127.0.0.1:8000
```

Then open **http://127.0.0.1:8000** and follow the flow:

1. **Get Started → choose an LLM provider.**
   - *Fake (offline demo)* — no API key; personas run a scripted exploration.
   - *Claude (Anthropic)* — enter an API key; the model drives each persona.
   - *Local (Ollama)* — point at a running Ollama server and a tool-capable
     model (e.g. `llama3.1`); runs fully locally, no API key.

   The connection is tested before the setting is saved and reused next time.
2. **Create a project** — target URL, what to focus on, and a persona panel
   (pick from the library or get an AI-recommended panel).
3. **Run the test** — progress streams live; when it finishes you get the bug
   list, common-issue ranking, per-persona feedback, token/cost, and downloadable
   traces and video.

Bind elsewhere with `uv run synthpanel serve --host 0.0.0.0 --port 8080`.

To use the real Anthropic provider, also install the optional extra:

```bash
uv sync --extra llm
```

## Data

Settings, projects, run history, and artifacts live under `~/.synthpanel/`
(`synthpanel.db` and `artifacts/`). The last-used provider config is remembered,
so subsequent sessions skip straight to your projects.

## Development

```bash
uv run pytest             # fast, hermetic unit tests (no browser or network)
uv run pytest -m e2e      # end-to-end tests against a real Chromium
```
