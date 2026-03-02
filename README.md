# CodeNavigator: Technical Repository Analysis

A professional-grade, local repository analysis system leveraging Retrieval-Augmented Generation (RAG) for deep-dive codebase exploration. This platform enables secure, offline analysis of Python projects using local large language models.

**Developed by: Esraa & Nancy**

<img width="1600" height="662" alt="image" src="https://github.com/user-attachments/assets/8a0c0cde-8f72-412e-9283-ff67b32f112f" />


## Project Objectives
This system provides an automated framework for repository intelligence, focusing on:
1.  **Issue Identification**: Detection of potential logic flaws, refactoring opportunities, and security considerations.
2.  **Logic Synchronization**: Comparative analysis between different code versions and branches.
3.  **Architectural Mapping**: Generation of high-level system overviews and component diagrams.

The infrastructure ensures data sovereignty by processing all information locally, utilizing advanced vector search and optimized inference engines.

<img width="1600" height="670" alt="image" src="https://github.com/user-attachments/assets/e0b8effe-e509-46e9-afef-2e9c7343e21b" />


## Key Capabilities
- **On-Demand Indexing**: Direct integration with Git for repository cloning and processing.
- **Structural Code Analysis**: Abstract Syntax Tree (AST) optimized parsing for high-context retrieval.
- **Optimized Vector Search**: Enterprise-ready storage using ChromaDB for sub-second retrieval performance.
- **Secure Local Inference**: Integration with Ollama for privacy-focused language processing.
- **Advanced Visualization**: Dynamic generation of Mermaid.js architecture and class diagrams.


## Docker Deployment
CodeNavigator is containerized for consistent deployment. The image is available on Docker Hub.

### Docker Hub Image
**Repository**: `esraaabdelrazek012/codenavigator`

### Deployment Instructions
1. **Pull the image**:
   ```bash
   docker pull esraaabdelrazek012/codenavigator:latest
   ```
2. **Launch with Docker Compose**:
   ```bash
   docker-compose up
   ```
   *Note: Ensure Ollama is running on your host machine at `http://localhost:11434`.*

### Manual Image Upload (For Maintainers)
To build and push a new version to Docker Hub:
```bash
docker build -t esraaabdelrazek012/codenavigator:latest .
docker login
docker push esraaabdelrazek012/codenavigator:latest
```

## Local Installation Guide

### 1. Requirements
- Python 3.9 or higher
- Ollama Service (Running locally)

### 2. Dependency Management
```bash
pip install -r requirements.txt
```

### 3. Engine Configuration
```bash
ollama pull deepseek-coder-v2:lite
```

### 4. System Launch
```bash
streamlit run app.py
```

## Disclaimer
This system is designed for secure, local-only processing. No data is transmitted to external telemetry or third-party APIs during the standard analysis workflows.
