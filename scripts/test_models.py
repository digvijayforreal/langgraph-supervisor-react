
from config import supervisor_llm

response = supervisor_llm.invoke(
    "Explain LangGraph in one sentence.",
    config={
        "run_name": "Supervisor_Test",
        "tags": ["supervisor", "groq", "test"]
    }
)

print("Response:", response.content)
print("Usage:", response.usage_metadata)
