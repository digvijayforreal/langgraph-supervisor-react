
from langchain_core.messages import HumanMessage
from agents.supervisor import supervisor_node


test_queries = [
    "Write Python code for bubble sort",
    "Solve the equation 5x + 10 = 35",
    "Explain artificial intelligence"
]


for query in test_queries:

    print("\n-----------------------------")
    print("Query:", query)

    state = {
        "messages": [
            HumanMessage(content=query)
        ],
        "selected_agent": None,
        "routing_reason": "",
        "execution_path": []
    }

    result = supervisor_node(state)

    print("Result:", result)

