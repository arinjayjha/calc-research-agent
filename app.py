import json
import streamlit.components.v1 as components

def copy_button(label: str, text: str, key: str, height: int = 40):
    # Uses JSON to safely escape any characters
    payload = json.dumps(text or "")
    components.html(
        f"""
        <button id="btn-{key}" style="padding:8px 12px;border-radius:8px;border:1px solid #ddd;cursor:pointer">
          📋 {label}
        </button>
        <script>
          const txt{key} = {payload};
          const btn{key} = document.getElementById("btn-{key}");
          btn{key}.onclick = async () => {{
            try {{
              await navigator.clipboard.writeText(txt{key});
              btn{key}.innerText = "✅ Copied!";
              setTimeout(()=>btn{key}.innerText="📋 {label}", 1200);
            }} catch (e) {{
              btn{key}.innerText = "⚠️ Copy failed";
              setTimeout(()=>btn{key}.innerText="📋 {label}", 1500);
            }}
          }};
        </script>
        """,
        height=height,
    )

import json
from datetime import datetime

import os
import re
import time
import numexpr as ne
from typing import List, Dict
from dotenv import load_dotenv

import streamlit as st
from tavily import TavilyClient
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field, ValidationError, field_validator

# ---------- Env & Clients ----------
load_dotenv()

AZURE_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_ENDPOINT   = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_VERSION    = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
TAVILY_KEY       = os.environ.get("TAVILY_API_KEY")

llm = AzureChatOpenAI(
    azure_deployment=AZURE_DEPLOYMENT,
    azure_endpoint=AZURE_ENDPOINT,
    openai_api_version=AZURE_VERSION,
    temperature=0,
)

tavily = TavilyClient(api_key=TAVILY_KEY) if TAVILY_KEY else None

# ---------- Validation ----------
class AgentResponse(BaseModel):
    mode: str = Field(description="math|search|error")
    answer: str
    sources: List[str] = Field(default_factory=list)

    @field_validator("mode")
    @classmethod
    def valid_mode(cls, v):
        return v if v in {"math", "search", "error"} else "error"

def safe_return(payload: Dict) -> Dict:
    try:
        return AgentResponse(**payload).model_dump()
    except ValidationError as e:
        return {"mode": "error", "answer": f"Invalid payload: {e}", "sources": []}

# ---------- Math helper ----------
MATH_SEQ = re.compile(r"""
    (?:
        (?:\d+\.\d*|\.\d+|\d+)           # 12 | 3. | .75 | 12
        (?:[eE][+\-]?\d+)?               # optional exponent: e10 | E-3
      | [\+\-\*\/\%\(\)]                 # operators/parens
      | \s+                              # whitespace
    )+
""", re.VERBOSE)

def eval_math(expr: str) -> float:
    expr = expr.strip().replace("^", "**")
    if not re.fullmatch(r"[0-9\.\+\-\*\/\%\(\)\seE]+", expr):
        raise ValueError("Invalid characters in expression.")
    result = ne.evaluate(expr)
    try:
        return float(result)
    except Exception:
        return float(result.item())

def run_math(query: str) -> Dict:
    q = query.replace("^", "**")
    matches = list(MATH_SEQ.finditer(q))
    if not matches:
        raise ValueError("No math expression found.")
    expr = max((m.group(0) for m in matches), key=len).strip()
    value = eval_math(expr)
    return {"mode": "math", "answer": str(value), "sources": []}

# ---------- Search helper ----------
def with_retries(fn, *, tries=3, delay=0.6, backoff=1.8, exceptions=(Exception,), **kwargs):
    last_err = None
    for i in range(tries):
        try:
            return fn(**kwargs)
        except exceptions as e:
            last_err = e
            if i < tries - 1:
                time.sleep(delay)
                delay *= backoff
    raise last_err

def run_search(query: str, max_results: int = 5) -> Dict:
    if not tavily:
        return {"mode": "error", "answer": "Tavily API key not set.", "sources": []}

    try:
        results = with_retries(
            tavily.search,
            tries=3, delay=0.6, backoff=1.8, exceptions=(Exception,),
            query=query, max_results=max_results,
            include_answer=False, include_raw_content=True, timeout=30
        )
        items = results.get("results", []) if isinstance(results, dict) else results

        seen, sources = set(), []
        for it in items:
            url = (it.get("url") or "").strip()
            if url and url not in seen:
                seen.add(url); sources.append(url)
            if len(sources) == 3:
                break

        snippets = []
        for it in items[:3]:
            title = (it.get("title") or "")[:120]
            content = (it.get("content") or "").replace("\n", " ")[:600]
            url = it.get("url", "")
            snippets.append(f"TITLE: {title}\nSNIPPET: {content}\nURL: {url}")

        prompt = (
            "You are a concise researcher. Using ONLY the information in the snippets below, "
            "write EXACTLY three bullet points answering the user's query. "
            "No speculation. If insufficient evidence, say so.\n\n"
            f"USER QUERY:\n{query}\n\nSNIPPETS:\n" + "\n\n---\n\n".join(snippets)
        )

        summary = llm.invoke(prompt).content.strip()
        return {"mode": "search", "answer": summary, "sources": sources}

    except Exception as e:
        return {"mode": "error", "answer": f"Search failed: {e}", "sources": []}

# ---------- Router ----------
def decide_mode(query: str) -> str:
    if re.search(r"[0-9]+\s*[\+\-\*\/\^\%]\s*[0-9]+", query) or re.search(r"\b(calc|compute|what is|how many)\b", query, re.I):
        return "math"
    return "search"

def answer_query(query: str) -> Dict:
    mode = decide_mode(query)
    out = run_math(query) if mode == "math" else run_search(query)
    return safe_return(out)

# ---------- UI ----------
st.set_page_config(page_title="Calc + Research Agent", page_icon="🧠", layout="centered")
if "history" not in st.session_state:
    st.session_state["history"] = []   # each item: {"ts", "query", "response"}


st.title("🧠 Calc + Research Agent")
st.caption("Math uses a safe evaluator; search uses Tavily + Azure OpenAI summarizer.")

with st.sidebar:
    st.subheader("Status")
    st.subheader("History")
if st.session_state["history"]:
    # Most recent first
    for i, item in enumerate(reversed(st.session_state["history"][-10:]), start=1):
        ts = item["ts"]
        q  = item["query"]
        r  = item["response"]
        with st.expander(f"{i}. [{ts}] {q[:50]}{'...' if len(q)>50 else ''}"):
            st.markdown(f"**Mode:** `{r.get('mode')}`")
            st.markdown("**Answer:**")
            st.write(r.get("answer", ""))

            if r.get("sources"):
                st.markdown("**Sources:**")
                for url in r["sources"]:
                    st.markdown(f"- [{url}]({url})")

            # Download this specific item
            st.download_button(
                label="⬇️ Download JSON for this item",
                data=json.dumps(item, ensure_ascii=False, indent=2),
                file_name=f"agent_history_{ts.replace(':','-')}.json",
                mime="application/json",
                key=f"dl_{ts}"
            )
    # Clear history
    if st.button("🧹 Clear history"):
        st.session_state["history"].clear()
        st.rerun()
else:
    st.caption("No history yet. Run a query!")

    st.write(f"Azure deployment: `{AZURE_DEPLOYMENT or 'missing'}`")
    st.write(f"Tavily key: `{'set' if TAVILY_KEY else 'missing'}`")

query = st.text_input("Ask something (math or info):", placeholder="e.g., (23*47)+199  •  or  Who won the 2024 Physics Nobel?")
go = st.button("Run")

if go and query.strip():
    with st.spinner("Thinking..."):
        resp = answer_query(query.strip())

    st.markdown(f"**Mode:** `{resp.get('mode')}`")
    st.markdown("**Answer:**")
    st.write(resp.get("answer"))
    copy_button("Copy answer", resp.get("answer", ""), key="ans")
    if resp.get("sources"):
        st.markdown("**Sources:**")
        for url in resp["sources"]:
            st.markdown(f"- [{url}]({url})")
    # Save to history
    st.session_state["history"].append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "query": query.strip(),
        "response": resp
    })

    # Raw JSON + download for the latest response
    with st.expander("Raw JSON (latest response)"):
        st.code(json.dumps(resp, ensure_ascii=False, indent=2), language="json")
        st.download_button(
            label="⬇️ Download this JSON",
            data=json.dumps(resp, ensure_ascii=False, indent=2),
            file_name=f"agent_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
