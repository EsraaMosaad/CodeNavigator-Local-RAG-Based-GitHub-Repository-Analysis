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

def render_mermaid(answer: str):
    """Extracts mermaid blocks from LLM answer and renders them visually,
    then shows remaining text as markdown."""
    mermaid_pattern = re.compile(r"```mermaid\s*([\s\S]*?)```", re.IGNORECASE)
    matches = mermaid_pattern.findall(answer)
    text_without_mermaid = mermaid_pattern.sub("", answer).strip()
    if text_without_mermaid:
        st.markdown(text_without_mermaid)
    if matches:
        for diagram_code in matches:
            escaped = diagram_code.strip().replace('`', '\\`')
            html = f"""
            <style>
              body {{ background-color: #0F1629 !important; color: #F8FAFC !important; margin: 0; font-family: 'Inter', sans-serif; }}
              .mermaid {{ text-align: center; background: transparent !important; }}
            </style>
            <div id="mermaid-container" style="background:#162035;border-radius:10px;padding:20px;margin:10px 0">
              <div class="mermaid">{diagram_code.strip()}</div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
            <script>
              mermaid.initialize({{ startOnLoad: true, theme: 'dark', themeVariables: {{ 'primaryTextColor': '#F8FAFC' }} }});
            </script>
            """
            components.html(html, height=500, scrolling=True)
    elif not matches:
        st.info("No Mermaid diagram was generated. Try clicking Visual Diagrams again.")

# Page Config
st.set_page_config(page_title="CodeNavigator AI", page_icon="🤖", layout="wide")

# Custom Creative CSS
# Load Custom CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
# Styled Header (Compact)
st.markdown("""
<div style="margin-top: -20px; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px;">
    <h1 style="color: #FFFFFF; margin: 0; font-family: 'Inter', sans-serif; font-weight: 700; font-size: 26px; display: flex; align-items: center; gap: 10px;">
        <span style="color: #3B82F6;">⚡</span> CodeNavigator AI
    </h1>
    <p style="color: #94A3B8; margin-top: 2px; font-size: 14px; font-weight: 400;">Intelligent repository mapping and deep code analysis</p>
</div>
""", unsafe_allow_html=True)

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
    st.markdown("<h3 style='color: white; font-weight: 600; font-size: 16px; margin-bottom: 20px;'>⚙️ Settings</h3>", unsafe_allow_html=True)
    if check_ollama():
        st.markdown("""
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.2); padding: 4px 10px; border-radius: 16px; margin-bottom: 15px;">
                <div style="width: 6px; height: 6px; background-color: #22C55E; border-radius: 50%;"></div>
                <span style="color: #22C55E; font-size: 12px; font-weight: 600;">Ollama Connected</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); padding: 4px 10px; border-radius: 16px; margin-bottom: 15px;">
                <div style="width: 6px; height: 6px; background-color: #EF4444; border-radius: 50%;"></div>
                <span style="color: #EF4444; font-size: 12px; font-weight: 600;">Ollama Offline</span>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Reconnect"): st.rerun()

    st.divider()
    
    repo_url = st.text_input("Git URL", placeholder="https://github.com/...")
    process_button = st.button("✨ Initialize Analysis")

    st.markdown("---")
    if st.button("🗑️ Clear Cache"):
        import shutil
        # Reset ChromaDB in-memory singleton BEFORE deleting files to avoid InternalError
        try:
            chromadb.api.client.SharedSystemClient.clear_system_cache()
        except Exception:
            pass
        if os.path.exists("temp_repos"): shutil.rmtree("temp_repos", ignore_errors=True)
        if os.path.exists("vector_stores"): shutil.rmtree("vector_stores", ignore_errors=True)
        st.session_state.clear()
        st.success("Cache cleared!")
        st.rerun()

    if process_button and repo_url:
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        
        with st.status(f"Scanning {repo_name}...", expanded=True) as status:
            st.write("📥 Cloning repository...")
            repo_path = loader.load(repo_url, "temp_repos")
            st.session_state.repo_path = repo_path
            
            st.write("🔍 Creating Knowledge Graph...")
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
                status.update(label="Ready for deep-dive!", state="complete", expanded=False)

    # Sidebar Footer / Stats Card & Toolbox
    with st.sidebar:
        if st.session_state.get("processed"):
            st.markdown(f"""
            <div style="background: rgba(59,130,246,0.05); padding: 14px 16px; border-radius: 8px; border: 1px solid rgba(59,130,246,0.2); margin-top: 20px;">
                <p style="margin: 0 0 4px 0; color: #6B7FA3; font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">🔎 Exploring</p>
                <p style="margin: 0 0 10px 0; font-size: 13px; font-weight: 600; color: #3B82F6; font-family: 'JetBrains Mono', monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{st.session_state.repo_name}</p>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <div style="width: 6px; height: 6px; border-radius: 50%; background: #22C55E;"></div>
                    <span style="font-size: 12px; color: #94A3B8;">Ready for analysis</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<p style='color: #6B7FA3; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 25px; margin-bottom: 10px;'>ANALYSIS TOOLBOX</p>", unsafe_allow_html=True)
            
            t_col1, t_col2 = st.columns(2)
            
            with t_col1:
                if st.button("📝 Summary", use_container_width=True):
                    st.session_state.pending_action = "summarize"
                    st.rerun()
                if st.button("🗺️ Roadmap", use_container_width=True):
                    st.session_state.pending_action = "roadmap"
                    st.rerun()
                    
            with t_col2:
                if st.button("🚩 Issues", use_container_width=True):
                    st.session_state.pending_action = "issues"
                    st.rerun()
                
                with st.popover("🔀 Diff", use_container_width=True):
                    if "repo_path" not in st.session_state:
                        st.error("Repository path not found. Please reload.")
                    else:
                        if "branches" not in st.session_state:
                            with st.spinner("Fetching branches..."):
                                st.session_state.branches = loader.get_branches(st.session_state.repo_path)
                        
                        branches = st.session_state.branches
                        
                        if not branches or "Error" in branches[0]:
                            st.error(f"Could not fetch branches: {branches}")
                            if st.button("Retry Fetch"):
                                del st.session_state.branches
                                st.rerun()
                        else:
                            branch_a = st.selectbox("Base Branch", branches, index=0)
                            default_index = 1 if len(branches) > 1 else 0
                            branch_b = st.selectbox("Target Branch", branches, index=default_index)
                            
                            if st.button("Analyze Branch Diff"):
                                if branch_a == branch_b:
                                    st.warning("Please select different branches.")
                                else:
                                    st.session_state.pending_action = "diff"
                                    st.session_state.pending_branches = (branch_a, branch_b)
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
            elif msg.get("has_diagram"):
                render_mermaid(msg["content"])
            else:
                st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources"):
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
            st.session_state.messages.append({"role": "assistant", "content": ans, "sources": src})
else:
    st.info("Enter a GitHub URL to begin.")
