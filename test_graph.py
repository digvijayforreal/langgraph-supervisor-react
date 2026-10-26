from langchain_core.messages import HumanMessage

from api.routes import initial_graph_state
from graph.workflow import app_graph

queries = [
    "Hi, how are you?",
    "Write a Python function to reverse a string",
    "Solve 5x + 10 = 35",
    "Translate 'Good morning, how are you?' into Marathi",
]

for query in queries:
    print("\n" + "=" * 70)
    print("QUERY:", query)
    result = app_graph.invoke(
        initial_graph_state(query),
        config={"run_name": "Single_Supervisor_Test", "recursion_limit": 15},
    )
    print("AGENT:", result["selected_agent"])
    print("PHASE:", result["phase"])
    print("APPROVED:", result["approved"])
    print("ATTEMPTS:", result["attempts"])
    print("SCORE:", result["review_score"] if result["attempts"] else "N/A (direct)")
    print("PATH:", result["execution_path"])
    print("ANSWER:\n", result["messages"][-1].content)
