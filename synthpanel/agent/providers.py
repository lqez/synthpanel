"""LLM provider registry: metadata, connection testing, and factory.

Each provider declares the config fields the web onboarding form should render,
plus a default model. The agent loop stays provider-agnostic via LLMProvider;
this module is the single place that knows about concrete providers.

Claude (Anthropic), OpenAI, local Ollama, and the offline Fake provider are all
wired up.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from synthpanel.agent.llm import FakeLLM, LLMProvider


@dataclass(frozen=True)
class ProviderField:
    key: str
    label: str
    type: str = "text"  # "text" | "password"
    required: bool = True
    placeholder: str = ""


@dataclass(frozen=True)
class ProviderSpec:
    key: str
    label: str
    default_model: str
    fields: list[ProviderField] = field(default_factory=list)
    available: bool = True


PROVIDERS: dict[str, ProviderSpec] = {
    "anthropic": ProviderSpec(
        key="anthropic",
        label="Claude (Anthropic)",
        default_model="claude-opus-4-8",
        fields=[
            ProviderField("api_key", "API Key", type="password", placeholder="sk-ant-..."),
            ProviderField("model", "Model", required=False, placeholder="claude-opus-4-8"),
        ],
    ),
    "fake": ProviderSpec(
        key="fake",
        label="Fake (offline demo)",
        default_model="fake",
        fields=[],
    ),
    "openai": ProviderSpec(
        key="openai",
        label="OpenAI",
        default_model="gpt-4o",
        fields=[
            ProviderField("api_key", "API Key", type="password", placeholder="sk-..."),
            ProviderField("model", "Model", required=False, placeholder="gpt-4o"),
            ProviderField(
                "base_url", "Base URL (optional)", required=False,
                placeholder="OpenAI-compatible endpoint",
            ),
        ],
    ),
    "ollama": ProviderSpec(
        key="ollama",
        label="Local (Ollama)",
        default_model="llama3.1",
        fields=[
            ProviderField(
                "base_url", "Base URL", required=False, placeholder="http://localhost:11434"
            ),
            ProviderField("model", "Model", placeholder="llama3.1"),
        ],
    ),
}


def available_providers() -> list[ProviderSpec]:
    return [p for p in PROVIDERS.values() if p.available]


async def test_connection(provider_key: str, config: dict) -> tuple[bool, str]:
    """Validate credentials/model with a minimal call. Returns (ok, message)."""
    if provider_key == "fake":
        return True, "OK (offline fake provider)"
    if provider_key == "anthropic":
        from synthpanel.agent.anthropic_provider import test_anthropic_connection

        return await test_anthropic_connection(config)
    if provider_key == "openai":
        from synthpanel.agent.openai_provider import test_openai_connection

        return await test_openai_connection(config)
    if provider_key == "ollama":
        from synthpanel.agent.ollama_provider import test_ollama_connection

        return await test_ollama_connection(config)
    return False, f"provider '{provider_key}' is not available yet"


def build_provider(provider_key: str, config: dict) -> LLMProvider:
    """Construct a runnable LLMProvider from saved config."""
    if provider_key == "fake":
        from synthpanel.agent.actions import Action, ActionType

        # A small exploratory script so offline demo runs do something visible.
        script = [
            Action(type=ActionType.SCROLL, rationale="Get an overview."),
            Action(type=ActionType.WAIT, rationale="Let content settle."),
            Action(type=ActionType.DONE, rationale="Reached an overview."),
        ]
        return FakeLLM(script=script, bug_on_console_error=True)
    if provider_key == "anthropic":
        from synthpanel.agent.anthropic_provider import AnthropicProvider

        model = config.get("model") or PROVIDERS["anthropic"].default_model
        return AnthropicProvider(api_key=config["api_key"], model=model)
    if provider_key == "openai":
        from synthpanel.agent.openai_provider import OpenAIProvider

        model = config.get("model") or PROVIDERS["openai"].default_model
        return OpenAIProvider(
            api_key=config.get("api_key"), model=model, base_url=config.get("base_url")
        )
    if provider_key == "ollama":
        from synthpanel.agent.ollama_provider import OllamaProvider

        model = config.get("model") or PROVIDERS["ollama"].default_model
        return OllamaProvider(host=config.get("base_url", ""), model=model)
    raise ValueError(f"provider '{provider_key}' is not available yet")
