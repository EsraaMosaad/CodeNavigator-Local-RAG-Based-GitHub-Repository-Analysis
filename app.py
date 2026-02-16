import pysqlite3
import sys
sys.modules['sqlite3'] = pysqlite3

import streamlit as st
import os
import requests
from src.ingestion.loader import GitLoader
from src.ingestion.parser import PythonParser
from src.embeddings.hf_embeddings import HFEmbeddings
from src.vectorstore.chroma_manager import ChromaManager
from src.models.ollama_client import OllamaModel
from src.rag.pipeline import RAGPipeline

# Page Config
st.set_page_config(page_title="Modular RAG Code Analyzer", page_icon="💻", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; color: white; border: 1px solid #464b5d; }
    .stButton>button:hover { border-color: #ff4b4b; color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

def check_ollama():
    try:
        return requests.get("http://localhost:11434/api/tags").status_code == 200
    except:
        return False

st.title("🚀 Modular RAG Code Analyzer")

# Initialize Components
loader = GitLoader()
parser = PythonParser()
embeddings_manager = HFEmbeddings()
vector_manager = ChromaManager()
llm_manager = OllamaModel(model_name="mistral")

with st.sidebar:
    st.header("Settings")
    if check_ollama():
        st.success("✅ Ollama is running")
    else:
        st.error("❌ Ollama is not running")
        if st.button("Retry Connection"): st.rerun()

    repo_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/username/repo")
    process_button = st.button("Process Repository")

    if process_button and repo_url:
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        
        with st.status(f"Processing {repo_name}...", expanded=True) as status:
            # 1. Load (with deduplication check)
            st.write("Checking repository...")
            repo_path = loader.load(repo_url, "temp_repos")
            st.session_state.repo_path = repo_path
            
            # 2. Check if already processed in vector store
            st.write("Checking vector store...")
            embedding_fn = embeddings_manager.get_embedding_function()
            vector_store = vector_manager.create_or_load(None, repo_name, embedding_fn)
            
            if vector_store:
                st.write("Using existing vector store.")
            else:
                st.write("Parsing and indexing...")
                texts = parser.parse_and_split(repo_path)
                if not texts:
                    st.error("No Python files found.")
                else:
                    vector_store = vector_manager.create_or_load(texts, repo_name, embedding_fn)
            
            if vector_store:
                st.session_state.vector_store = vector_store
                st.session_state.processed = True
                st.session_state.repo_name = repo_name
                status.update(label="Ready!", state="complete", expanded=False)

# Main Chat
if "messages" not in st.session_state: st.session_state.messages = []

if st.session_state.get("processed"):
    # Ensure branches are loaded for context
    if "branches" not in st.session_state:
        st.session_state.branches = loader.get_branches(st.session_state.repo_path)
    
    repo_context = {
        "Repository Name": st.session_state.repo_name,
        "Available Branches": ", ".join(st.session_state.branches) if st.session_state.branches else "Unknown"
    }

    pipeline = RAGPipeline(llm_manager.get_llm(), st.session_state.vector_store.as_retriever(), repo_context)
    
    st.subheader(f"Analyzing: {st.session_state.repo_name}")
    
    # Specialized Analysis Tools
    st.markdown("### 🛠️ Developer Tools")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Summarize Code"):
            with st.spinner("Generating Summary..."):
                ans, src = pipeline.query_specialized("summarize")
                st.session_state.messages.append({"role": "assistant", "content": ans, "sources": src})
                st.rerun()
                
    with col2:
        if st.button("🐛 Generate Issues"):
            with st.spinner("Drafting GitHub Issues..."):
                ans, src = pipeline.query_specialized("issues")
                st.session_state.messages.append({"role": "assistant", "content": ans, "sources": src})
                st.rerun()

    with col3:
        if st.button("📊 Visual Diagrams"):
            with st.spinner("Drawing Diagrams..."):
                ans, src = pipeline.query_specialized("diagrams")
                st.session_state.messages.append({"role": "assistant", "content": ans, "sources": src})
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
                            with st.spinner(f"Computing diff between {branch_a} and {branch_b}..."):
                                # 1. Get the raw git diff text
                                raw_diff = loader.get_diff(st.session_state.repo_path, branch_a, branch_b)
                                
                                # 2. Limit diff size to avoid context overflow (e.g., 2000 chars)
                                if len(raw_diff) > 5000:
                                    display_diff = raw_diff[:5000] + "\n...(truncated due to length)..."
                                else:
                                    display_diff = raw_diff

                                # 3. Send to LLM
                                ans, src = pipeline.query_specialized("diff", display_diff)
                                st.session_state.messages.append({"role": "assistant", "content": ans, "sources": []})  # No sources for diff usually
                                st.rerun()
    
    st.divider()
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources"):
                    for doc in msg["sources"]: st.code(doc.page_content, language="python")

    if prompt := st.chat_input("Ask about the code..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ans, src = pipeline.query(prompt)
                st.markdown(ans)
                if src:
                    with st.expander("Sources"):
                        for doc in src: st.code(doc.page_content, language="python")
                st.session_state.messages.append({"role": "assistant", "content": ans, "sources": src})
else:
    st.info("Enter a GitHub URL to begin.")
