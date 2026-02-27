# CodeNavigator: Technical Repository Analysis

A professional-grade, local repository analysis system leveraging Retrieval-Augmented Generation (RAG) for deep-dive codebase exploration. This platform enables secure, offline analysis of Python projects using local large language models.

## Project Objectives
This system provides an automated framework for repository intelligence, focusing on:
1.  **Issue Identification**: Detection of potential logic flaws, refactoring opportunities, and security considerations.
2.  **Logic Synchronization**: Comparative analysis between different code versions and branches.
3.  **Architectural Mapping**: Generation of high-level system overviews and component diagrams.

The infrastructure ensures data sovereignty by processing all information locally, utilizing advanced vector search and optimized inference engines.

## Key Capabilities
- **On-Demand Indexing**: Direct integration with Git for repository cloning and processing.
- **Structural Code Analysis**: Abstract Syntax Tree (AST) optimized parsing for high-context retrieval.
- **Optimized Vector Search**: Enterprise-ready storage using ChromaDB for sub-second retrieval performance.
- **Secure Local Inference**: Integration with Ollama for privacy-focused language processing.
- **Advanced Visualization**: Dynamic generation of Mermaid.js architecture and class diagrams.

## System Architecture
The platform implements a multi-stage RAG pipeline:
1. **Ingestion**: Automated cloning and file traversal.
2. **Standardization**: Semantic splitting of source code into discrete units.
3. **Representation**: High-dimensional vector embedding for semantic search.
4. **Knowledge Storage**: Persistent indexing in a centralized vector store.
5. **Retrieval & Synthesis**: Context-aware retrieval followed by technical response generation.

## Implementation Guide

### 1. Requirements
- Python 3.9 or higher
- Ollama Service (Running locally)

### 2. Dependency Management
Install the required software components using the project manifest:
```bash
pip install -r requirements.txt
```

### 3. Engine Configuration
Ensure the required model is available in your local environment:
```bash
ollama pull deepseek-coder-v2:lite
```

### 4. System Launch
Initialize the analytics interface:
```bash
streamlit run app.py
```

## Functional Overview
1. Provide a public GitHub repository URI.
2. Execute **Initialize Analysis** to begin background indexing.
3. Utilize the analytical tools to query the system for architectural summaries, issue tracking, or logic verification.

## Disclaimer
This system is designed for secure, local-only processing. No data is transmitted to external telemetry or third-party APIs during the standard analysis workflows.
