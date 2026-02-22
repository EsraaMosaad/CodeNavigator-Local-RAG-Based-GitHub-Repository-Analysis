# Assignment-2: Model Evaluation

**Course:** CSAI810  
**Student Names:** Esraa Abdelrazek & Nancy Abdo  
**Date:** 16th February 2026

---

## 1. Introduction
The objective of this study is to compare and evaluate three Generative AI models that could realistically be used in our **Local RAG-Based GitHub Code Analyzer**. Our project focuses on analyzing Python repositories to generate issues and explain code logic while running entirely on local hardware (privacy-first). We selected models based on their coding capabilities, inference speed, and license suitability for our academic project.

---

## 2. Selected Generative AI Models

### Model 1: DeepSeek-Coder-V2-Lite
*   **Purpose & Capabilities**: This is a specialized model trained specifically for code generation and understanding. It supports over 300 programming languages and is optimized for tasks like bug fixing and repository analysis.
*   **Developer**: DeepSeek AI.
*   **Access Method**: Open Weights (We access it via Ollama).

### Model 2: Llama-3.1-8B-Instruct
*   **Purpose & Capabilities**: A widely used general-purpose LLM. While not exclusively for code, it has strong reasoning abilities and is often used as a baseline for local RAG applications due to its speed and instruction-following skills.
*   **Developer**: Meta (Facebook) AI.
*   **Access Method**: Open Weights (We access it via Ollama).

### Model 3: GPT-4o ("Omni")
*   **Purpose & Capabilities**: A proprietary frontier model. It represents the "state-of-the-art" benchmark for reasoning and coding but requires a cloud connection. We included it to see what is possible with unlimited resources.
*   **Developer**: OpenAI.
*   **Access Method**: Proprietary API (Cloud-based).

---

## 3. Evaluation Criteria Definition

We defined six criteria to judge which model is best for our specific constraints (local execution, privacy, and code accuracy).

1.  **Code Generation Accuracy (HumanEval Score)**
    *   **What it measures**: The percentage of Python coding problems the model solves correctly on the first try.
    *   **How it is assessed**: Quantitative (Technical reports from DeepSeek/Meta).
    
2.  **Context Window Size**
    *   **What it measures**: How much code (in tokens) we can feed the model at once.
    *   **How it is assessed**: Quantitative (e.g., 8k vs 128k tokens). This is critical for reading large files.

3.  **Inference Speed (Local)**
    *   **What it measures**: The tokens-per-second generation speed on our laptop.
    *   **How it is assessed**: Qualitative (Fast/Slow experience during testing).

4.  **Data Privacy**
    *   **What it measures**: Whether the code we analyze leaves our machine.
    *   **How it is assessed**: Qualitative (Local execution vs Cloud API).

5.  **Instruction Following**
    *   **What it measures**: Can the model correctly format output (e.g., Mermaid.js diagrams) without errors?
    *   **How it is assessed**: Qualitative (Testing diagram generation).

6.  **Cost**
    *   **What it measures**: The price to run the model for a full repository scan.
    *   **How it is assessed**: Quantitative (Free vs Pay-per-token).

---

## 4. Comparative Table

| Evaluation Criterion | DeepSeek-Coder-V2-Lite | Llama-3.1-8B-Instruct | GPT-4o (OpenAI) |
| :--- | :--- | :--- | :--- |
| **1. Code Accuracy** | **Excellent**. Trained on massive code datasets, it rivals larger models in Python generation. | **Good**. Solid reasoning, but sometimes makes up non-existent libraries compared to DeepSeek. | **Superior**. The current industry leader, handling complex logic and edge cases perfectly. |
| **2. Context Window** | **128k Tokens**. Large enough to fit multiple Python files for cross-reference. | **128k Tokens**. Same capacity, good for RAG retrieval contexts. | **128k Tokens**. Extremely reliable retrieval over long contexts. |
| **3. Inference Speed** | **Fast**. Specialized "Lite" architecture makes it run smoothly on our local machine. | **Very Fast**. The 8B model is highly optimized for consumer hardware. | **Variable**. Depends on internet speed. Often fast, but adds network latency. |
| **4. Data Privacy** | **High (Local)**. No data leaves our laptop. Perfect for our privacy goal. | **High (Local)**. Runs locally, ensuring total data sovereignty. | **Low (Cloud)**. Sends code to OpenAI servers, violating our privacy requirement. |
| **5. Instruction Following** | **Strong**. Excells at following technical formats like JSON or Mermaid diagrams. | **Very Strong**. Very good at "chatty" responses and strict formatting. | **State-of-the-art**. Almost never fails to follow formatting rules. |
| **6. Cost** | **Free**. Uses our local RAM. | **Free**. Uses our local RAM. | **Paid**. Costs money per request, which gets expensive for large repos. |

---

## 5. Discussion & Recommendation
We plan to use **DeepSeek-Coder-V2-Lite** for our project.

*   **Why?**: It appears to be the best balance for us. It is free and private (running on Ollama), which is our main requirement.
*   **Trade-off**: While GPT-4o is smarter, we cannot use it because we want a "privacy-first" tool. Llama-3.1 is good, but DeepSeek is specifically trained for code, meaning it should give better explanations for the complex Python logic we plan to analyze.

---

## 6. References
1.  **DeepSeek-Coder-V2**: DeepSeek-AI. (2024). *DeepSeek-Coder-V2: Breaking the Barrier of Closed-Source Models in Code Intelligence*. arXiv preprint arXiv:2406.11931.
2.  **Llama 3.1**: Meta AI. (2024). *The Llama 3 Herd of Models*. Meta AI Research.
3.  **GPT-4o**: OpenAI. (2024). *Hello GPT-4o*. OpenAI Blog.
4.  **HumanEval Benchmark**: Chen, M., et al. (2021). *Evaluating Large Language Models Trained on Code*. arXiv.
