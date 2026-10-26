import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing in .env")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# These are the models already used in your working project.
# Change the environment variables if your Groq account's model access changes.
SUPERVISOR_MODEL = os.getenv("SUPERVISOR_MODEL", "openai/gpt-oss-120b")
CODING_MODEL = os.getenv("CODING_MODEL", "qwen/qwen3.8-27b")
MATH_MODEL = os.getenv("MATH_MODEL", "openai/gpt-oss-20b")
TRANSLATOR_MODEL = os.getenv("TRANSLATOR_MODEL", "openai/gpt-oss-120b")


def make_llm(model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        temperature=0,
        max_retries=2,
        use_responses_api=False,
    )


supervisor_llm = make_llm(SUPERVISOR_MODEL)
coding_llm = make_llm(CODING_MODEL)
math_llm = make_llm(MATH_MODEL)
translator_llm = make_llm(TRANSLATOR_MODEL)

MODEL_NAMES = {
    "supervisor": SUPERVISOR_MODEL,
    "research": SUPERVISOR_MODEL,
    "data_analyst": SUPERVISOR_MODEL,
    "document": SUPERVISOR_MODEL,
}
