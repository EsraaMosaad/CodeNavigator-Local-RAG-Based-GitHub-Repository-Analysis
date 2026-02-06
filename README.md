# RAG-Based GitHub Code Analyzer 🚀

A fully local, privacy-first system to analyze public GitHub Python repositories using Retrieval-Augmented Generation (RAG). This project was built for a university demonstration to showcase local LLM capabilities in software engineering.

## 🎯 Project Goal
This project aims to build a **local RAG-based system** that analyzes GitHub repositories to:
1.  **Generate meaningful GitHub issues** (bugs, refactoring, security).
2.  **Perform code diff analysis** against external logic.
3.  **Summarize source code** with visual diagrams (Mermaid.js).

The system retrieves and reasons over code using vector databases and large language models to highlight changes, detect potential issues, and improve code understanding, providing practical experience in RAG pipelines and AI-assisted software analysis.

## 🌟 Features
- **Local Ingestion**: Clone any public GitHub repository directly.
- **Semantic Code Splitting**: Uses AST-aware parsing to maintain function and class context.
- **Local Embeddings**: Powered by `sentence-transformers/all-MiniLM-L6-v2` (runs on CPU).
- **Vector Storage**: Uses `ChromaDB` for fast, local similarity search.
- **Local LLM**: Integrated with `Ollama` using the `deepseek-coder-v2:lite` model.
- **Specialized Tools**:
    - **📝 Summarize Code**: High-level architecture + Class Diagrams.
    - **🐛 Generate Issues**: Auto-drafts GitHub issues for bugs/improvements.
    - **📊 Visual Diagrams**: Flowcharts and Sequence Diagrams.
    - **🔍 Code Diff**: Compare external snippets with repo logic.

## 🏗️ Architecture
The system follows a standard RAG pipeline:
1. **Load**: Clone repo and load `.py` files.
2. **Split**: Break code into semantic chunks.
3. **Embed**: Convert chunks into vectors.
4. **Store**: Save vectors in ChromaDB.
5. **Retrieve**: Find relevant code snippets based on user query.
6. **Generate**: Use Ollama to generate a technical answer based on retrieved context.

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.9+
- [Ollama](https://ollama.com/) (Must be installed and running)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Pull the Local LLM
Open your terminal and run:
```bash
ollama pull deepseek-coder-v2:lite
```

### 4. Run the Application
```bash
streamlit run app.py
```

## 📖 Usage
1. Enter a public GitHub URL (e.g., `https://github.com/psf/requests`).
2. Click **Process Repository** and wait for the indexing to complete.
3. Ask questions like:
   - "How does the authentication logic work?"
   - "Summarize the main entry point of the application."
   - "Are there any potential security issues in the file handling?"

## 🎓 Academic Justification
- **Privacy**: No data leaves the local machine.
- **Reproducibility**: Uses open-source tools and models.
- **Cost**: Completely free to run.
- **Technical Depth**: Demonstrates integration of AST parsing, vector databases, and LLM orchestration.

---
Built with ❤️ for University Project.
