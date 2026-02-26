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
            <div id="mermaid-container" style="background:#1e1e2e;border-radius:10px;padding:20px;margin:10px 0">
              <div class="mermaid" style="text-align:center">{diagram_code.strip()}</div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
            <script>
              mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
            </script>
            """
            components.html(html, height=500, scrolling=True)
    elif not matches:
        st.info("No Mermaid diagram was generated. Try clicking Visual Diagrams again.")

# Page Config
st.set_page_config(page_title="CodeNavigator AI", page_icon="�️", layout="wide")

# Custom Creative CSS
st.markdown("""
    <style>
    /* Full page styling */
    .main { 
        background-color: #0d1117; 
        color: #c9d1d9; 
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 1px solid #30363d;
    }

    /* Premium Button Styling */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3.5em; 
        background: #21262d; 
        color: #c9d1d9; 
        border: 1px solid #30363d;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover { 
        border-color: #58a6ff; 
        color: #58a6ff; 
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(88,166,255,0.15);
    }

    /* Input styling */
    .stTextInput>div>div>input {
        background-color: #161b22;
        border-color: #30363d;
        color: white;
        border-radius: 10px;
    }

    /* Chat message area enhancement */
    .stChatMessage {
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 12px;
        border: 1px solid #30363d;
        background: #161b22;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Make text in chat bubbles much clearer and brighter */
    .stChatMessage [data-testid="stMarkdownContainer"] p {
        color: #e6edf3 !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Improve contrast for code blocks in chat */
    .stChatMessage code {
        color: #ffa657 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Styled Header
st.markdown("""
<div style="background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px; border-radius: 20px; margin-bottom: 35px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);">
    <h1 style="color: white; margin: 0; font-family: 'Outfit', sans-serif; font-weight: 900; letter-spacing: -1px;">🚀 CodeNavigator AI</h1>
    <p style="color: rgba(255,255,255,0.8); margin-top: 5px; font-size: 17px; font-weight: 500;">Intelligent repository mapping and deep code analysis.</p>
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
    st.markdown("### ⚙️ Settings")
    if check_ollama():
        st.success("✅ Ollama: Connected")
    else:
        st.error("❌ Ollama: Offline")
        if st.button("🔄 Reconnect"): st.rerun()

    st.divider()
    
    repo_url = st.text_input("Git URL", placeholder="https://github.com/...")
    process_button = st.button("✨ Initialize Analysis")

    st.markdown("---")
    if st.button("🗑️ Clear Cache"):
        import shutil
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

    # Sidebar Footer / Stats Card
    if st.session_state.get("processed"):
        st.sidebar.markdown(f"""
        <div style="background: rgba(88,166,255,0.05); padding: 18px; border-radius: 12px; border: 1px solid #30363d; margin-top: 25px;">
            <p style="margin: 0; color: #58a6ff; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Active Project</p>
            <p style="margin: 5px 0 10px 0; font-size: 16px; font-weight: 700; color: #f0f6fc;">{st.session_state.repo_name}</p>
            <div style="display: flex; gap: 10px; align-items: center;">
                <div style="width: 8px; height: 8px; border-radius: 50%; background: #238636;"></div>
                <span style="font-size: 13px; color: #8b949e;">Status: Ready</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
    
    st.markdown(f"#### 🔎 Exploring: `{st.session_state.repo_name}`")
    
    # Analysis Toolbox
    st.markdown("### 🧪 Analysis Toolbox")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Summarize"):
            st.session_state.pending_action = "summarize"
            st.rerun()
                
    with col2:
        if st.button("🚩 Find Issues"):
            st.session_state.pending_action = "issues"
            st.rerun()

    with col3:
        if st.button("🗺️ Interactive Roadmap"):
            st.session_state.pending_action = "roadmap"
            st.rerun()

    with col4:
        with st.popover("🔀 Branch Diff"):
            if "repo_path" not in st.session_state:
                st.error("Repository path not found. Please reload.")
            else:
                # Get branches (cached)
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
                    col_a, col_b = st.columns(2)
                    with col_a:
                        branch_a = st.selectbox("Base Branch", branches, index=0)
                    with col_b:
                        # Try to find a different branch for the second default
                        default_index = 1 if len(branches) > 1 else 0
                        branch_b = st.selectbox("Target Branch", branches, index=default_index)
                    
                    if st.button("Analyze Branch Diff"):
                        if branch_a == branch_b:
                            st.warning("Please select different branches.")
                        else:
                            st.session_state.pending_action = "diff"
                            st.session_state.pending_branches = (branch_a, branch_b)
                            st.rerun()
    
    st.divider()
    
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
