"""FastAPI app implementing the onboarding flow (a~f from the project spec).

Flow:
  /            (a) Welcome
  /start           branch: settings exist -> /projects, else -> /onboarding
  /onboarding  (b,c) pick provider, enter config, test connection, save
  /projects    (d) list or, if empty, jump to project creation
  /projects/new (e) URL + focus + target personas
  /projects/{id} (f) detail + run
  /runs/{id}       run result
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from synthpanel.agent.providers import available_providers, test_connection
from synthpanel.persona.loader import load_personas
from synthpanel.persona.models import Persona
from synthpanel.persona.recommender import recommend_personas
from synthpanel.report.aggregate import aggregate
from synthpanel.report.models import SessionResult
from synthpanel.report.render import render_html, render_markdown
from synthpanel.web.runner import execute_run
from synthpanel.web.store import Store

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
_LIBRARY = Path(__file__).parent.parent / "persona" / "library" / "examples.yaml"


def _encode_persona(persona: Persona) -> str:
    """Encode a persona as a base64 JSON token for a checkbox value."""
    raw = persona.model_dump_json(exclude_none=True, exclude_defaults=True)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def _decode_persona(token: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8"))


def _persona_choices(personas: list[Persona]) -> list[dict]:
    """Shape personas for the selection template: token + display fields."""
    return [
        {"token": _encode_persona(p), "name": p.name, "archetype": p.archetype, "goal": p.intent.goal}
        for p in personas
    ]


def create_app(store: Store | None = None) -> FastAPI:
    app = FastAPI(title="SynthPanel")
    store = store or Store()
    app.state.store = store

    def render(request: Request, template: str, *, status_code: int = 200, **ctx) -> HTMLResponse:
        return _TEMPLATES.TemplateResponse(request, template, ctx, status_code=status_code)

    # (a) Welcome
    @app.get("/", response_class=HTMLResponse)
    def welcome(request: Request):
        return render(request, "welcome.html")

    # branch after "Get Started": skip provider setup if we already have settings
    @app.get("/start")
    def start():
        if store.get_settings():
            return RedirectResponse("/projects", status_code=303)
        return RedirectResponse("/onboarding", status_code=303)

    # (b, c) provider selection + config + connection test
    @app.get("/onboarding", response_class=HTMLResponse)
    def onboarding(request: Request, error: str | None = None):
        current = store.get_settings()
        return render(
            request,
            "onboarding.html",
            providers=available_providers(),
            current=current,
            error=error,
        )

    @app.post("/onboarding")
    async def onboarding_submit(request: Request):
        form = await request.form()
        provider = form.get("provider", "")
        config = {
            k: v
            for k, v in form.items()
            if k != "provider" and isinstance(v, str) and v.strip()
        }
        ok, message = await test_connection(provider, config)
        if not ok:
            return render(
                request,
                "onboarding.html",
                providers=available_providers(),
                current={"provider": provider, "config": config},
                error=message,
                status_code=400,
            )
        store.save_settings(provider, config)
        return RedirectResponse("/projects", status_code=303)

    # (d) project list or jump to creation
    @app.get("/projects", response_class=HTMLResponse)
    def projects(request: Request):
        items = store.list_projects()
        if not items:
            return RedirectResponse("/projects/new", status_code=303)
        return render(request, "projects.html", projects=items, settings=store.get_settings())

    # (e) project creation
    @app.get("/projects/new", response_class=HTMLResponse)
    def project_new(request: Request):
        return render(
            request,
            "project_new.html",
            library=_persona_choices(load_personas(_LIBRARY)),
            recommended=[],
        )

    # AI persona recommendation: re-renders the form with a recommended panel
    # pre-selected, on top of the library choices. The user can still edit.
    @app.post("/projects/recommend", response_class=HTMLResponse)
    async def project_recommend(request: Request):
        form = await request.form()
        settings = store.get_settings() or {"provider": "fake", "config": {}}
        personas = await recommend_personas(
            url=(form.get("url") or "").strip(),
            focus=(form.get("focus") or "").strip(),
            n=int(form.get("count") or 5),
            provider_key=settings["provider"],
            config=settings["config"],
        )
        return render(
            request,
            "project_new.html",
            library=_persona_choices(load_personas(_LIBRARY)),
            recommended=_persona_choices(personas),
            name=form.get("name", ""),
            url=form.get("url", ""),
            focus=form.get("focus", ""),
        )

    @app.post("/projects/new")
    async def project_create(request: Request):
        form = await request.form()
        name = (form.get("name") or "Untitled").strip()
        url = (form.get("url") or "").strip()
        focus = (form.get("focus") or "").strip()
        personas: list[dict] = []
        for token in form.getlist("personas"):
            try:
                personas.append(_decode_persona(token))
            except Exception:  # noqa: BLE001 - ignore tampered/invalid tokens
                continue
        project_id = store.create_project(name, url, focus, personas)
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    # (f) project detail
    @app.get("/projects/{project_id}", response_class=HTMLResponse)
    def project_detail(request: Request, project_id: int):
        project = store.get_project(project_id)
        if not project:
            return RedirectResponse("/projects", status_code=303)
        return render(
            request,
            "project_detail.html",
            project=project,
            runs=store.list_runs(project_id),
        )

    @app.post("/projects/{project_id}/run")
    async def project_run(project_id: int):
        project = store.get_project(project_id)
        settings = store.get_settings()
        if not project or not settings:
            return RedirectResponse("/projects", status_code=303)
        run_id = store.create_run(project_id)
        result = await execute_run(project, settings)
        status = "error" if result.get("error") else "done"
        store.finish_run(run_id, status, result)
        return RedirectResponse(f"/runs/{run_id}", status_code=303)

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    def run_detail(request: Request, run_id: int):
        run = store.get_run(run_id)
        if not run:
            return RedirectResponse("/projects", status_code=303)
        agg = aggregate(_results_from_run(run))
        return render(request, "run_detail.html", run=run, agg=agg)

    @app.get("/runs/{run_id}/report.md", response_class=PlainTextResponse)
    def run_report_md(run_id: int):
        run = store.get_run(run_id)
        if not run:
            return PlainTextResponse("not found", status_code=404)
        return PlainTextResponse(render_markdown(_run_title(run), _results_from_run(run)))

    @app.get("/runs/{run_id}/report.html", response_class=HTMLResponse)
    def run_report_html(run_id: int):
        run = store.get_run(run_id)
        if not run:
            return HTMLResponse("not found", status_code=404)
        return HTMLResponse(render_html(_run_title(run), _results_from_run(run)))

    def _run_title(run: dict) -> str:
        project = store.get_project(run["project_id"])
        return f"{project['name'] if project else 'Run'} · Run #{run['id']}"

    return app


def _results_from_run(run: dict) -> list[SessionResult]:
    return [SessionResult.model_validate(s) for s in run.get("result", {}).get("sessions", [])]
