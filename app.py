import pysqlite3
import sys
sys.modules['sqlite3'] = pysqlite3

import streamlit as st
import os
import json
import requests
from src.ingestion.loader import GitLoader
from src.ingestion.parser import PythonParser
from src.embeddings.hf_embeddings import HFEmbeddings
from src.vectorstore.chroma_manager import ChromaManager
from src.models.ollama_client import OllamaModel
from src.rag.pipeline import RAGPipeline
from src.visualization.diagram_renderer import render_architecture_diagram, render_from_data
from src.visualization.repo_scanner import scan_repo
from langchain.callbacks.base import BaseCallbackHandler
import re
import streamlit.components.v1 as components

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text + "▌")

def sanitize_mermaid(code: str) -> str:
    """Fix common LLM mistakes in mermaid syntax."""
    # Remove any lingering markdown blocks inside the content
    code = re.sub(r'```mermaid\n?|```', '', code, flags=re.IGNORECASE)
    # Fix unquoted brackets/parens in node names (very common error)
    # This is a simple heuristic: if a line looks like Node[Name], wrap it
    lines = []
    for line in code.split('\n'):
        # Escape any potential HTML characters that might break the <pre> tag
        clean_line = line.replace('<', '&lt;').replace('>', '&gt;')
        lines.append(clean_line)
    return '\n'.join(lines).strip()

def render_mermaid(answer: str):
    """Parses text and renders both markdown parts and visual Mermaid diagrams in their original order."""
    mermaid_pattern = re.compile(r"(```mermaid\s*[\s\S]*?```)", re.IGNORECASE)
    parts = mermaid_pattern.split(answer)
    
    diagram_count = 0
    for part in parts:
        if part.lower().strip().startswith("```mermaid"):
            # This is a mermaid block
            diagram_code = re.sub(r"```mermaid\s*|```", "", part, flags=re.IGNORECASE).strip()
            sanitized_code = sanitize_mermaid(diagram_code)
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
              body, html {{ margin:0; padding:0; background:transparent; overflow:hidden; font-family:'Inter', sans-serif; }}
              .wrap {{ 
                background: #111118; 
                border: 1px solid rgba(255,255,255,0.08); 
                border-radius: 12px; 
                padding: 30px; 
                margin: 10px 0;
                box-shadow: 0 10px 40px rgba(0,0,0,0.4);
              }}
              .mermaid {{ visibility: hidden; }}
              .mermaid[data-processed="true"] {{ visibility: visible; }}
            </style>
            </head>
            <body>
              <div class="wrap">
                <pre class="mermaid">
{sanitized_code}
                </pre>
              </div>
              <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
              <script>
                mermaid.initialize({{ 
                  startOnLoad: true, 
                  theme: 'dark',
                  securityLevel: 'loose',
                  themeVariables: {{
                    primaryColor: '#6366F1',
                    primaryTextColor: '#FAFAFA',
                    lineColor: '#A5B4FC',
                    mainBkg: '#18181B',
                    nodeBorder: 'rgba(255,255,255,0.1)'
                  }}
                }});
              </script>
            </body></html>
            """
            components.html(html, height=450, scrolling=True)
            diagram_count += 1
        elif part.strip():
            # This is regular markdown text
            st.markdown(part)
    return diagram_count > 0

# Page Config
st.set_page_config(page_title="CodeNavigator AI", page_icon="🤖", layout="wide")

# Load CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Components
loader = GitLoader()
parser = PythonParser()
embeddings_manager = HFEmbeddings()
vector_manager = ChromaManager()
llm_manager = OllamaModel(model_name="deepseek-coder-v2:lite")

def check_ollama():
    try:
        return requests.get("http://localhost:11434/api/tags").status_code == 200
    except:
        return False

with st.sidebar:
    # ── Logo / Header (Only when NO repo is loaded)
    if not st.session_state.get("processed"):
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; padding:16px 4px 12px;">
            <div style="width:32px; height:32px; background:linear-gradient(135deg,#6366F1,#8B5CF6);
                        border-radius:8px; display:flex; align-items:center; justify-content:center;
                        font-size:16px;">⚡</div>
            <div>
                <div style="color:#FAFAFA; font-weight:700; font-size:14px; line-height:1;">CodeNavigator</div>
                <div style="color:#71717A; font-size:11px; margin-top:2px;">AI Code Analyst</div>
            </div>
        </div>
        <hr style="border:none; border-top:1px solid rgba(255,255,255,0.07); margin:0 0 12px 0;">
        """, unsafe_allow_html=True)

    # ── Ollama status
    if check_ollama():
        st.markdown("""
        <div style="display:inline-flex; align-items:center; gap:7px;
                    background:rgba(34,197,94,0.08); border:1px solid rgba(34,197,94,0.2);
                    padding:5px 12px; border-radius:20px; margin-bottom:14px; margin-left:4px;">
            <div style="width:6px; height:6px; background:#22C55E; border-radius:50%;
                        box-shadow:0 0 6px #22C55E;"></div>
            <span style="color:#22C55E; font-size:12px; font-weight:600;">Ollama Connected</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display:inline-flex; align-items:center; gap:7px;
                    background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2);
                    padding:5px 12px; border-radius:20px; margin-bottom:8px;">
            <div style="width:6px; height:6px; background:#EF4444; border-radius:50%;"></div>
            <span style="color:#EF4444; font-size:12px; font-weight:600;">Ollama Offline</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("↻  Reconnect", use_container_width=True): st.rerun()

    # ── Repository section
    st.markdown("<p style='color:#52525B; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin:10px 0 6px;'>Repository</p>", unsafe_allow_html=True)
    repo_url = st.text_input("Git URL", placeholder="https://github.com/user/repo", label_visibility="collapsed")
    process_button = st.button("✨  Initialize Analysis", use_container_width=True)

    # Process repository
    if process_button and repo_url:
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        with st.status(f"Scanning {repo_name}...", expanded=True) as status:
            st.write("📥 Cloning repository...")
            repo_path = loader.load(repo_url, "temp_repos")
            st.session_state.repo_path = repo_path
            st.write("🔍 Building knowledge graph...")
            embedding_fn = embeddings_manager.get_embedding_function()
            vector_store = vector_manager.create_or_load(None, repo_name, embedding_fn)
            if not vector_store:
                texts = parser.parse_and_split(repo_path)
                if texts:
                    vector_store = vector_manager.create_or_load(texts, repo_name, embedding_fn)
            if vector_store:
                st.session_state.vector_store = vector_store
                st.session_state.processed = True
                st.session_state.repo_name = repo_name
                status.update(label="✅ Ready!", state="complete", expanded=False)

    # ── Active repo badge (only when loaded)
    if st.session_state.get("processed"):
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.25);
                    border-radius:10px; padding:12px 14px; margin-top:14px;">
            <div style="color:#A5B4FC; font-size:10px; font-weight:700; text-transform:uppercase;
                        letter-spacing:0.08em; margin-bottom:5px;">🔎 Exploring</div>
            <div style="color:#6366F1; font-family:'JetBrains Mono',monospace; font-size:12px;
                        font-weight:600; white-space:nowrap; overflow:hidden;
                        text-overflow:ellipsis; margin-bottom:8px;">{st.session_state.repo_name}</div>
            <div style="display:flex; align-items:center; gap:6px;">
                <div style="width:6px; height:6px; background:#22C55E; border-radius:50%;
                            box-shadow:0 0 5px #22C55E;"></div>
                <span style="color:#71717A; font-size:11px;">Active Project</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Analysis Toolbox
        st.markdown("<p style='color:#52525B; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin:18px 0 8px;'>Tools</p>", unsafe_allow_html=True)
        
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            if st.button("📝 Summary", use_container_width=True):
                st.session_state.pending_action = "summarize"; st.rerun()
            if st.button("🗺️ Roadmap", use_container_width=True):
                st.session_state.pending_action = "roadmap"; st.rerun()
        with t_col2:
            if st.button("🚩 Issues", use_container_width=True):
                st.session_state.pending_action = "issues"; st.rerun()
            with st.popover("🔀 Diff", use_container_width=True):
                if "repo_path" not in st.session_state:
                    st.error("Repository path not found.")
                else:
                    if "branches" not in st.session_state:
                        with st.spinner("Loading branches..."):
                            st.session_state.branches = loader.get_branches(st.session_state.repo_path)
                    branches = st.session_state.branches
                    if not branches or "Error" in branches[0]:
                        st.error(f"Could not fetch branches: {branches}")
                        if st.button("Retry"): del st.session_state.branches; st.rerun()
                    else:
                        branch_a = st.selectbox("Base", branches, index=0)
                        default_index = 1 if len(branches) > 1 else 0
                        branch_b = st.selectbox("Target", branches, index=default_index)
                        if st.button("Compare", use_container_width=True):
                            if branch_a == branch_b:
                                st.warning("Select different branches.")
                            else:
                                st.session_state.pending_action = "diff"
                                st.session_state.pending_branches = (branch_a, branch_b)
                                st.rerun()

    # ── Session section (bottom)
    st.markdown("<p style='color:#52525B; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin:18px 0 6px;'>Session</p>", unsafe_allow_html=True)
    if st.button("🗑️  Clear Cache", use_container_width=True):
        import shutil
        try:
            chromadb.api.client.SharedSystemClient.clear_system_cache()
        except Exception:
            pass
        if os.path.exists("temp_repos"): shutil.rmtree("temp_repos", ignore_errors=True)
        if os.path.exists("vector_stores"): shutil.rmtree("vector_stores", ignore_errors=True)
        st.session_state.clear()
        st.rerun()

# Main Chat Logic
if "messages" not in st.session_state: st.session_state.messages = []

if st.session_state.get("processed"):
    if "branches" not in st.session_state:
        st.session_state.branches = loader.get_branches(st.session_state.repo_path)
    
    repo_context = {
        "Repository Name": st.session_state.repo_name,
        "Available Branches": ", ".join(st.session_state.branches) if st.session_state.branches else "Unknown"
    }

    pipeline = RAGPipeline(llm_manager.get_llm(), st.session_state.vector_store.as_retriever(), repo_context)
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("diagram_html"):
                components.html(msg["diagram_html"], height=750, scrolling=True)
                with st.expander("Raw LLM Output"):
                    st.code(msg["content"], language="json")
            elif msg.get("diagram_image"):
                import io
                st.image(io.BytesIO(msg["diagram_image"]), use_container_width=True)
                with st.expander("Raw LLM Output"):
                    st.code(msg["content"], language="json")
            elif msg.get("diagram_html"):
                components.html(msg["diagram_html"], height=750, scrolling=True)
                with st.expander("Raw Architecture Data"):
                    st.code(msg["content"], language="json")
            else:
                # Always use render_mermaid to handle mixed text/diagram content
                content = msg["content"]
                render_mermaid(content)
            if msg.get("sources"):
                with st.expander("📎 Sources"):
                    for doc in msg["sources"]: st.code(doc.page_content, language="python")

    # Process pending actions at the bottom of the chat
    if st.session_state.get("pending_action"):
        action = st.session_state.pending_action
        st.session_state.pending_action = None
        
        if action == "summarize":
            with st.chat_message("assistant"):
                st_placeholder = st.empty()
                with st.spinner("Writing summary..."):
                    st_placeholder.markdown("*(Thinking...)*")
                    stream_handler = StreamHandler(st_placeholder)
                    ans, src = pipeline.query_specialized("summarize", callbacks=[stream_handler])
                st_placeholder.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans, "sources": src})
            st.rerun()

        elif action == "issues":
            with st.chat_message("assistant"):
                st_placeholder = st.empty()
                with st.spinner("Detecting issues..."):
                    st_placeholder.markdown("*(Analyzing code...)*")
                    stream_handler = StreamHandler(st_placeholder)
                    ans, src = pipeline.query_specialized("issues", callbacks=[stream_handler])
                st_placeholder.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans, "sources": src})
            st.rerun()
            
        elif action == "roadmap":
            with st.spinner("Analyzing architecture for humans..."):
                repo_path = st.session_state.get("repo_path", "")
                if not repo_path:
                    st.error("Repo path not found.")
                else:
                    raw_data = scan_repo(repo_path)
                    qwen_llm = OllamaModel(model_name="qwen2.5-coder:7b").get_llm(temperature=0.1)
                    repo_name_context = st.session_state.repo_name
                    prompt = f"""
                    You are a Software Architect explaining the "{repo_name_context}" project to a NON-TECHNICAL person.
                    I will give you raw data from a code scan (JSON). 
                    Your goal is to create a HUMAN-FRIENDLY roadmap of the 6-8 most important components.
                    
                    RULES:
                    1. BE SPECIFIC. Use "{repo_name_context}" and actual folder names in your labels. 
                    2. Use the "description" field as your source of truth.
                    3. Combine files from the same folder into ONE component.
                    4. Output EXACTLY 6-8 nodes.
                    
                    Raw Data: {json.dumps(raw_data)}
                    
                    Return ONLY a JSON with this structure:
                    {{
                      "nodes": [ {{"id": "id", "label": "{repo_name_context} Module", "type": "entry|module|database|external", "description": "What this specific part does for the user"}} ]
                    }}
                    """
                    simple_json_str = qwen_llm.invoke(prompt)
                    from src.visualization.diagram_renderer import extract_json_from_llm
                    simplified_data = extract_json_from_llm(simple_json_str) or raw_data
                    diagram_html = render_from_data(simplified_data, title=f"{st.session_state.repo_name} — Visual Map")
                    
                    if diagram_html:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"I've mapped out the key components of {st.session_state.repo_name} below.",
                            "sources": [],
                            "has_diagram": True,
                            "diagram_html": diagram_html
                        })
                    else:
                        st.error("Could not generate map.")
            st.rerun()
            
        elif action == "diff":
            branch_a, branch_b = st.session_state.pending_branches
            with st.chat_message("assistant"):
                st_placeholder = st.empty()
                st_placeholder.markdown(f"*Computing diff between {branch_a} and {branch_b}...*")
                raw_diff = loader.get_diff(st.session_state.repo_path, branch_a, branch_b)
                if len(raw_diff) > 5000:
                    display_diff = raw_diff[:5000] + "\n...(truncated due to length)..."
                else:
                    display_diff = raw_diff
                
                # Clear placeholder and start stream
                st_placeholder.empty()
                stream_handler = StreamHandler(st_placeholder)
                ans, src = pipeline.query_specialized("diff", display_diff, callbacks=[stream_handler])
                st_placeholder.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans, "sources": []}) 
            st.rerun()

    if prompt := st.chat_input("Ask about the code..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            st_placeholder = st.empty()
            stream_handler = StreamHandler(st_placeholder)
            ans, src = pipeline.query(prompt, callbacks=[stream_handler])
            st_placeholder.markdown(ans)
            if src:
                with st.expander("Sources"):
                    for doc in src: st.code(doc.page_content, language="python")
            
            # Auto-detect diagram in new response
            has_diagram = "```mermaid" in ans.lower()
            st.session_state.messages.append({
                "role": "assistant", 
                "content": ans, 
                "sources": src,
                "has_diagram": has_diagram
            })
            if has_diagram: st.rerun() # Refresh to trigger visual render
else:
    st.markdown("""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center;
                padding:80px 20px; text-align:center;">
        <div style="width:64px; height:64px; background:linear-gradient(135deg,#6366F1,#8B5CF6);
                    border-radius:16px; display:flex; align-items:center; justify-content:center;
                    font-size:28px; margin-bottom:20px; box-shadow:0 0 30px rgba(99,102,241,0.3);">⚡</div>
        <h2 style="color:#FAFAFA; font-family:'Inter',sans-serif; font-weight:700;
                   font-size:22px; margin:0 0 8px; letter-spacing:-0.3px;">Ready to explore any codebase</h2>
        <p style="color:#71717A; font-size:14px; max-width:400px; line-height:1.6; margin:0 0 28px;">
            Paste a GitHub URL in the sidebar and click
            <strong style='color:#A5B4FC;'>Initialize Analysis</strong>
            to start a deep-dive into any repository.
        </p>
        <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center;">
            <div style="background:#111118; border:1px solid rgba(255,255,255,0.07); border-radius:8px;
                        padding:10px 16px; font-size:13px; color:#A1A1AA;">📝 Summarize codebase</div>
            <div style="background:#111118; border:1px solid rgba(255,255,255,0.07); border-radius:8px;
                        padding:10px 16px; font-size:13px; color:#A1A1AA;">🚩 Find code issues</div>
            <div style="background:#111118; border:1px solid rgba(255,255,255,0.07); border-radius:8px;
                        padding:10px 16px; font-size:13px; color:#A1A1AA;">🗺️ Map architecture</div>
            <div style="background:#111118; border:1px solid rgba(255,255,255,0.07); border-radius:8px;
                        padding:10px 16px; font-size:13px; color:#A1A1AA;">💬 Chat with the code</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.chat_input("Enter a GitHub URL in the sidebar to begin...", disabled=True)
