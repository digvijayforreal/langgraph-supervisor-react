from langgraph.graph import START, END, StateGraph
from graph.state import AgentState
from graph.router import route_supervisor
from agents.supervisor import supervisor_node
from agents.integrated_workers import research_node, data_analyst_node, document_node

workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("research", research_node)
workflow.add_node("data_analyst", data_analyst_node)
workflow.add_node("document", document_node)
workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges("supervisor", route_supervisor, {
    "research": "research", "data_analyst": "data_analyst", "document": "document", END: END
})
for name in ("research", "data_analyst", "document"):
    workflow.add_edge(name, "supervisor")
app_graph = workflow.compile()
