# LangGraph Supervisor & ReAct AI

**A Multi-Agent AI Platform with Intelligent Routing, Answer Review, Tool Execution, and Live Workflow Visualization.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Framework-LangGraph-green.svg)](https://www.langchain.com/langgraph)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq-orange.svg)](https://groq.com/)
[![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-blue.svg)](https://ai.google.dev/)

## Overview

LangGraph Supervisor & ReAct AI is a multi-agent AI application built using LangGraph, LangChain, FastAPI, Groq, and Google Gemini.

The platform combines two different AI architectures:

- **Supervisor Architecture:** A centralized supervisor intelligently routes user requests to specialized agents, reviews their responses, and requests improvements when necessary.
- **ReAct Architecture:** An independent Gemini-powered agent that reasons about user requests and dynamically selects tools to complete tasks.

The application includes a web-based interface that allows users to interact with both workflows and observe their execution.

The goal is to demonstrate how multiple AI agents, tools, and LLMs can work together to solve different types of tasks through structured workflows.

## Key Features

### 1. Supervisor Multi-Agent Workflow

A centralized Supervisor manages the complete execution process.

- Intelligent query classification and routing.
- Specialized agents for research, data analysis, and document processing.
- Supervisor reviews the generated response.
- Feedback-based revision when an answer needs improvement.
- Maximum of three worker attempts.
- Execution path and workflow status tracking.
- Review score and approval status.

**Workflow:**

```text
              USER QUERY
                   |
                   v
             SUPERVISOR
                   |
          Classify the request
                   |
        +----------+----------+
        |          |          |
        v          v          v
     RESEARCH   DATA       DOCUMENT
      AGENT    ANALYST      AGENT
        |          |          |
        +----------+----------+
                   |
                   v
             DRAFT ANSWER
                   |
                   v
             SUPERVISOR
                REVIEW
                   |
             +-----+-----+
             |           |
          Approved    Rejected
             |           |
             v           v
            END      REVISION
                         |
                         v
                    SAME WORKER
                   (Max 3 Attempts)
```

### 2. Specialized Agents

| Agent | Responsibility |
|---|---|
| Supervisor | General conversation, routing, and answer review |
| Research Agent | Web research and current information |
| Data Analyst | CSV/XLSX analysis and data visualization |
| Document Agent | PDF document analysis |

### 3. Gemini ReAct Agent

A separate tool-using AI agent powered by Google's Gemini model.

The agent follows the Reasoning and Acting (ReAct) approach to decide when a tool is needed.

**Available Tools:**

| Tool | Function |
|---|---|
| Web Search | Search for information online |
| PDF Generator | Generate downloadable PDF reports |
| Date & Time | Retrieve current date and time information |
| Email | Prepare email content and handle sending requests |

Additional email safeguards distinguish between drafting an email and explicitly requesting that it be sent.

### 4. Live Workflow Monitoring

The application provides real-time workflow updates using Server-Sent Events (SSE).

Users can observe:

- Query received.
- Supervisor routing.
- Selected agent.
- Worker execution.
- Tool activity.
- Answer generation.
- Supervisor review.
- Revision requests.
- Final completion status.

### 5. File Upload Support

Upload documents and datasets directly through the application.

Supported formats:

- PDF
- CSV
- XLSX

Uploaded PDFs are processed by the Document Agent, while CSV and XLSX files are handled by the Data Analyst.

Maximum upload size: 10 MB.

### 6. Web Interface

The application provides separate interfaces for the two AI workflows:

- Supervisor interface for multi-agent execution.
- ReAct interface for tool-based conversations.
- Live execution pipeline.
- File upload support.
- Tool activity visualization.
- PDF report access.

## Technology Stack

| Category | Technologies |
|---|---|
| Language | Python 3.12+ |
| Agent Framework | LangGraph |
| LLM Integration | LangChain |
| Supervisor LLM | Groq |
| ReAct LLM | Google Gemini |
| Backend | FastAPI |
| Streaming | Server-Sent Events (SSE) |
| Frontend | HTML, CSS, JavaScript |
| Data Processing | Pandas, OpenPyXL |
| PDF Processing | PDFPlumber, PyPDF |
| PDF Generation | ReportLab |
| Web Search | Tavily |
| Observability | LangSmith |
| Package Manager | uv |

## Project Architecture

```text
langgraph-supervisor-react/
│
├── agents/
│   ├── supervisor.py
│   ├── research.py
│   ├── data_analyst.py
│   └── react_agent.py
│
├── api/
│   ├── routes.py
│   ├── stream_routes.py
│   ├── upload_routes.py
│   ├── react_routes.py
│   └── react_email_routes.py
│
├── core/
│   └── config.py
│
├── graph/
│   ├── state.py
│   └── workflow.py
│
├── tools/
│   ├── react_web_search.py
│   ├── react_pdf_tool.py
│   ├── react_datetime_tool.py
│   ├── react_email_tool.py
│   ├── data_tools.py
│   └── document_tools.py
│
├── frontend/
│   ├── index.html
│   ├── react.html
│   ├── css/
│   └── js/
│
├── data/
│   └── react_reports/
│
├── scripts/
├── test/
├── main.py
├── test_graph.py
├── pyproject.toml
├── uv.lock
└── README.md
```

*Note: This is a high-level view of the project. Some folders contain additional modules and files.*

## Getting Started

### Prerequisites

Before running the project, make sure you have:

- Python 3.12 or higher
- uv package manager
- Groq API key
- Google Gemini API key

Optional:
- Tavily API key for web research.
- LangSmith API key for tracing and monitoring.

### 1. Clone the Repository

```bash
git clone https://github.com/digvijayforreal/langgraph-supervisor-react.git

cd langgraph-supervisor-react
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment Variables

Create a `.env` file in the project root.

```env
# Groq API
GROQ_API_KEY=your_groq_api_key

# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Optional: Tavily Search
TAVILY_API_KEY=your_tavily_api_key

# Optional: LangSmith
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=langgraph-supervisor
```

The Supervisor models can also be configured through environment variables:

```env
SUPERVISOR_MODEL=openai/gpt-oss-120b
CODING_MODEL=qwen/qwen3.8-27b
MATH_MODEL=openai/gpt-oss-20b
TRANSLATOR_MODEL=openai/gpt-oss-120b
```

Use model identifiers available to your Groq account.

**Important:** Never commit your `.env` file or expose API keys publicly.

### 4. Run the Application

Start the FastAPI server:

```bash
uv run uvicorn main:app --reload
```

### 5. Open the Application

| Interface | URL |
|---|---|
| Supervisor | http://127.0.0.1:8000/ |
| ReAct Agent | http://127.0.0.1:8000/react |
| API Documentation | http://127.0.0.1:8000/docs |

## API Endpoints

### Supervisor Workflow

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat` | Execute Supervisor workflow |
| POST | `/chat/stream` | Execute workflow with live SSE updates |
| POST | `/upload` | Upload PDF, CSV, or XLSX files |

### ReAct Workflow

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/react/chat` | Execute Gemini ReAct agent |
| POST | `/api/react/chat/stream` | Stream tool activity and final response |
| GET | `/api/react/reports/{filename}` | Access generated PDF reports |

### Example: Supervisor Request

```json
{
  "message": "Explain how a binary search algorithm works."
}
```

### Example: ReAct Request

```json
{
  "message": "Search for the latest developments in artificial intelligence and generate a PDF report."
}
```

## How the Supervisor Works

The Supervisor workflow follows a structured process:

1. **Receive:** Accept the user's query.
2. **Classify:** Determine whether the request needs a direct answer, research, data analysis, or document processing.
3. **Route:** Select the appropriate specialist agent.
4. **Execute:** The selected agent performs its task using relevant tools.
5. **Review:** The Supervisor evaluates the generated answer against the original query and execution evidence.
6. **Revise:** If the answer is rejected, the same worker receives feedback and gets another attempt.
7. **Complete:** Return the approved answer or report that the answer did not pass review within the attempt limit.

## ReAct vs Supervisor

| Feature | Supervisor | ReAct |
|---|---|---|
| Architecture | Multi-agent workflow | Single tool-using agent |
| LLM Provider | Groq | Google Gemini |
| Agent Routing | Central Supervisor | Model-driven tool selection |
| Answer Review | Supervisor review loop | ReAct execution |
| Web Search | Research Agent | Web Search Tool |
| PDF Generation | Document/data workflows | Dedicated PDF Tool |
| Email | Not its primary workflow | Email Tool |
| Streaming | Yes | Yes |

## Testing

Run the graph test:

```bash
uv run python test_graph.py
```

Check Python module compilation:

```bash
uv run python -m compileall -q agents graph api main.py test_graph.py
```

## Future Improvements

- Persistent conversation memory.
- Additional specialized agents and tools.
- Improved workflow observability.
- More advanced agent collaboration.
- Enhanced error handling and retry strategies.
- Expanded file processing capabilities.

## Contributing

Contributions, suggestions, and improvements are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Implement your changes.
4. Test your changes.
5. Submit a pull request.

## Author

**Digvijay Mali**

GitHub: [@digvijayforreal](https://github.com/digvijayforreal)

Project: [LangGraph Supervisor & ReAct AI](https://github.com/digvijayforreal/langgraph-supervisor-react)

---

**Built with LangGraph, FastAPI, Groq, and Google Gemini.**