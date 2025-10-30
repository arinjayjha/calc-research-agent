# 🧠 Calc + Research Agent

This project is a hands-on **Agentic AI demo** that combines:
- A **safe math evaluator** for calculation queries.
- A **web search + summarizer** pipeline (via Tavily API + Azure OpenAI).
- A **Streamlit UI** for interactive use.
- Features like **structured JSON outputs**, **copy-to-clipboard**, **history tracking**, **downloadable results**, and **Dockerization** for portability.

The goal is to **practice and demonstrate agentic AI concepts** in a practical, small-scale but feature-rich project.  
It shows:
- Tool routing (math vs search).
- Using an LLM (Azure OpenAI) for summarization.
- Integration of external tools (Tavily).
- Returning structured, validated outputs (Pydantic).
- Building a UI (Streamlit).
- Packaging with Docker and pushing to GitHub.

---

## ✨ Features
- **Math path:** Evaluates arithmetic expressions safely using `numexpr`.
- **Search path:** Queries Tavily API, fetches top results, and uses Azure OpenAI to summarize into 3 concise bullet points with sources.
- **Router:** Heuristically decides whether the query is math or search.
- **Structured output:** Always returns JSON with `{mode, answer, sources}` validated by Pydantic.
- **Streamlit UI:**
  - Input box for queries.
  - Shows mode, formatted answer, and clickable sources.
  - Copy-to-clipboard buttons for answers and sources.
  - Expandable history (last 10 queries).
  - Download any result as JSON.
  - Clear history button.
- **Dockerized:** Runs anywhere with one command.
- **GitHub-ready:** Includes `.gitignore`, `.env.example`, and CI workflow to build Docker image.

---

## 🚀 Quickstart

### 1. Clone & setup
```bash
git clone https://github.com/<your-username>/calc-research-agent.git
cd calc-research-agent
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
Copy `.env.example` → `.env` and fill in:
```
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
TAVILY_API_KEY=tvly_xxxxxxxxxxxxxxx
```

### 3. Run locally
```bash
streamlit run app.py
```
Visit [http://localhost:8501](http://localhost:8501).

---

## 🐳 Docker

Build:
```bash
docker build -t calc-research-agent:latest .
```

Run:
```bash
docker run --rm -p 8501:8501 --env-file .env calc-research-agent:latest
```

---

## 📝 Example Queries
- **Math:**  
  - `What is (23*47)+199?`  
  - `Compute 19^3 + 47`  
  - `CAGR approx: (210/120)^(1/3) - 1`

- **Search:**  
  - `Who won the 2024 Nobel Prize in Physics?`  
  - `Latest update on large language models in healthcare`

---

## 📂 Project Structure
```
calc-research-agent/
├── app.py              # Streamlit app
├── requirements.txt    # Python deps
├── Dockerfile          # Container build
├── .gitignore
├── .env.example        # Template for secrets
└── README.md           # Project documentation
```

---

## 📈 Roadmap / Next Steps
- Add LLM-based router instead of regex (small classifier prompt).
- Extend search tools (SerpAPI, Bing, etc.).
- Add RAG over PDFs (for internal docs).
- Deploy on Streamlit Cloud or Azure Web App.
- Write simple unit tests (pytest) for math + search paths.

---

## 🤝 Why this project?
This is a **learning + showcase project** to:
- Practice LangChain-style agent concepts without heavy frameworks.
- Get hands-on with **Azure OpenAI** (company-provided keys).
- Explore **tool-using agents** (math & search).
- Build something you can **demo in a standup** and share in a portfolio.
- Create a stepping stone toward more complex **multi-agent workflows**.

It balances **simplicity** (easy to run, free tiers only) with **real agent patterns** (routing, tool use, structured outputs).

---

## 📜 License
MIT — free to use, share, and adapt.
