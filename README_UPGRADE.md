# LangGraph Studio — Single Supervisor Upgrade

Architecture: START -> Supervisor (general answer OR choose Coding / Math / Translator)
-> selected Worker -> SAME Supervisor (review) -> END, or revision back to same worker (maximum three worker attempts).

## Replace your working project files
1. Back up your existing `langgraph-supervisor` folder.
2. Copy the folders `agents`, `api`, `core`, `graph`, `frontend` and the files `main.py`, `test_graph.py` from this package into your existing project. Replace files with matching names.
3. Delete the now-unused `agents/general.py`, `agents/reviewer.py`, `agents/finalizer.py` from your existing project so they do not confuse future work.
4. Keep your existing `.env`, `.venv`, `uv.lock`, `pyproject.toml` and LangSmith settings. Do not replace those.
5. If you previously configured CORS for a Vite server, it is unnecessary for the static FastAPI frontend.

## Groq models
The upgrade preserves your previously used models for Supervisor (openai/gpt-oss-120b), Coding (qwen/qwen3.8-27b), and Math (openai/gpt-oss-20b).
The new Translator defaults to openai/gpt-oss-120b so it doesn't require a model you haven't verified is available. Optionally override models in `.env` with SUPERVISOR_MODEL, CODING_MODEL, MATH_MODEL or TRANSLATOR_MODEL.

## Run
From your current activated project directory:

    uv run python -m compileall -q agents graph api main.py test_graph.py
    uv run python test_graph.py
    uv run uvicorn main:app --reload

Open http://127.0.0.1:8000/ and hard-refresh Ctrl+F5.
Swagger API: http://127.0.0.1:8000/docs

## Notes
- `.env` should contain GROQ_API_KEY. Your existing LangSmith environment values are respected by LangChain when set, including LANGSMITH_TRACING, LANGSMITH_API_KEY, and LANGSMITH_PROJECT.
- LLM routing and reviewing depend on model-generated JSON, validated after parsing. Malformed JSON is surfaced as a streaming error instead of silently inventing a route.
- Current streaming events signal stage boundaries between LangGraph node executions, not exact underlying LLM token-start times or token-by-token output.
- Reviewer approval is an LLM assessment, not mathematical verification or execution of code.
- The chat panel holds prior messages for display only; backend requests are intentionally stateless.
- `supervisor_usage` is the latest Supervisor call, and `worker_usage` is the latest Worker call, not cumulative usage across a review loop.
