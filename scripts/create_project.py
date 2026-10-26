
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

client = Client()

project = client.create_project(
    project_name="langgraph-supervisor",
    description="Multi-Agent LangGraph Chat API"
)

print("Project created successfully!")
print("Project name:", project.name)
