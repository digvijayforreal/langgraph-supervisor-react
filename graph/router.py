from langgraph.graph import END
from graph.state import AgentState

def route_supervisor(state: AgentState) -> str:
    if state["phase"] == "complete":
        return END
    if state["phase"] in ("working", "revision"):
        worker = state["selected_agent"]
        if worker not in ("research", "data_analyst", "document"):
            raise ValueError(f"Invalid specialist: {worker!r}")
        return worker
    raise ValueError(f"Unknown Supervisor phase: {state['phase']!r}")
