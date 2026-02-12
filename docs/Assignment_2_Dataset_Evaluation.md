# Comparative Study 2: Dataset Evaluation for Generative AI

## 1. Introduction
This study evaluates three distinct datasets used in the training, fine-tuning, or evaluation of Generative AI models for code. Understanding these datasets is critical for our RAG project, as the quality of our local model's (DeepSeek-Coder) output depends entirely on the data it was trained on and the benchmarks used to verify it. We examine a massive training corpus, an instruction-tuning dataset, and an evaluation benchmark.

## 2. Selected Datasets

### Dataset A: The Stack v2 (Training)
*   **Content & Modality**: A massive dataset of source code in over 600 programming languages, collected from public GitHub repositories.
*   **Intended Task**: Pre-training Large Language Models (LLMs) for code generation and understanding.
*   **Size**: Over 3 billion files, roughly 67 TB of data.
*   **Creator**: BigCode Project (Hugging Face, ServiceNow).
*   **Example**: A full Python file `utils.py` from a public repository containing helper functions for data processing.

### Dataset B: CommitPackFT (Fine-tuning)
*   **Content & Modality**: A filtered dataset of high-quality commit messages and their associated code changes (diffs) across hundreds of programming languages.
*   **Intended Task**: Instruction fine-tuning models to understand code evolution, Git commit formatting, and describing code changes.
*   **Size**: Approximately 2TB of commit data, filtered down to high-quality subsets for instruction tuning.
*   **Creator**: BigCode Project.
*   **Example**: A git commit message "Fix null pointer exception in login logic" paired with the specific lines of code changed to fix the bug.

### Dataset C: HumanEval (Evaluation)
*   **Content & Modality**: A set of 164 hand-written Python programming problems.
*   **Intended Task**: Evaluating the functional correctness of code generation models.
*   **Size**: Small (164 problems).
*   **Creator**: OpenAI.
*   **Example**: A function signature `def unique_elements(l: list):` with a docstring describing the desired output, where the model must complete the function body.

## 3. Evaluation Criteria Definition

1.  **Task Relevance & Alignment**
    *   **What it measures**: How closely the dataset matches the downstream task (e.g., repository analysis vs. function completion).
    *   **Assessment**: Qualitative. Does the data look like the inputs/outputs our RAG app will handle?

2.  **Data Quality & Filtering (PII/Deduplication)**
    *   **What it measures**: The rigorousness of the cleaning process to remove Personal Identifiable Information (PII), malicious code, and duplicate entries.
    *   **Why it matters**: Dirty data leads to insecure models that may leak private keys or generate vulnerable code.

3.  **Opt-Out & Licensing Mechanisms**
    *   **What it measures**: The presence of mechanisms for developers to remove their code from the dataset.
    *   **Why it matters**: Ethical AI development requires respecting copyright and developer consent (e.g., "Am I training on code I shouldn't be?").

4.  **Scale & Diversity**
    *   **What it measures**: The total volume of tokens and the variety of programming languages/paradigms covered.
    *   **Why it matters**: Larger, more diverse datasets prevent overfitting and allow models to generalize to unseen coding patterns.

5.  **Temporal Relevance (Freshness)**
    *   **What it measures**: The cutoff date of the data.
    *   **Why it matters**: Code libraries change rapidly. Old datasets train models on deprecated APIs (e.g., pandas 1.0 vs 2.0), causing hallucinations in modern projects.

6.  **Sparsity & Complexity**
    *   **What it measures**: Whether the data contains complex, multi-file projects or just simple one-liners.
    *   **Why it matters**: Our project analyzes whole repositories. Models trained only on simple snippets (like HumanEval) often fail to understand broad system architecture.

## 4. Comparative Table

| Evaluation Criterion | The Stack v2 (Training) | CommitPackFT (Fine-tuning) | HumanEval (Evaluation) |
| :--- | :--- | :--- | :--- |
| **1. Task Relevance** | **High (Repository Analysis)**. Contains full file contexts and repository structures, perfectly matching our RAG system's goal of analyzing complete files. | **High (Git Analysis)**. Directly relevant to our project's "Generate Issues" and "Code Diff" features, as it teaches models how code changes over time. | **Moderate (Unit Level)**. Good for checking if the model can write Python syntax, but lacks the file-level context needed for complex RAG tasks. |
| **2. Data Quality & Filtering** | **State-of-the-art**. Uses "Near-deduplication" and rigorous PII screening (removing emails/IPs) to ensure the training data is clean and safe. | **High**. specifically filters for "high quality" commit messages (e.g., distinct, descriptive messages) to prevent training on "fixed typo" style useless commits. | **High (Manual)**. Hand-crafted by researchers to ensure correctness, ensuring no "noise" interferes with the evaluation metric. |
| **3. Licensing & Opt-out** | **Excellent**. First dataset to implement a robust "Am I in The Stack?" tool, allowing developers to opt-out. Respects permissive licenses. | **Good**. Inherits rigorous licensing filtering from The Stack, focusing on permissively licensed repositories. | **Proprietary/Open**. The benchmark itself is open (MIT), but it doesn't involve "user content," so opt-out isn't applicable in the same way. |
| **4. Scale & Diversity** | **Massive**. COvers 600+ languages. This ensures the model understands not just Python, but the Dockerfiles and JSON configs often found alongside it. | **Large but Focused**. Billions of tokens, but strictly focused on the *changes* (diffs), limiting its diversity compared to full source files. | **Tiny**. Only 164 problems. While a standard, it is too small to capture the full diversity of real-world software engineering. |
| **5. Temporal Relevance** | **Variable**. Captures a snapshot of GitHub at a specific time. Requires regular re-scraping to stay current with new library versions. | **Variable**. Depends on the snapshot date. Older commits may reference deprecated coding practices or fixed security vulnerabilities. | **Static**. Created around 2021. It does not test knowledge of newer libraries or Python 3.10+ features (like pattern matching). |
| **6. Sparsity & Complexity** | **High Complexity**. Contains entire repositories, allowing models to learn cross-file dependencies (e.g., imports). | **Medium Complexity**. Focuses on the "before" and "after" implementation of a specific feature, teaching logic flow but not full architecture. | **Low Complexity**. Problems are self-contained functions. Evaluating on this alone doesn't guarantee a model can build a full app. |

## 5. Discussion
For our project, understanding these datasets reveals the strengths and limitations of our tools:
*   **The Stack v2** is the powerhouse that gives our DeepSeek model its broad knowledge of Python and GitHub structures. Its PII filtering is crucial for our "privacy-first" claim.
*   **CommitPackFT** is likely what gives DeepSeek its ability to explain *changes* or suggest refactors, which is a key feature of our app.
*   **HumanEval**, while famous, is a limited metric. High HumanEval scores (which DeepSeek has) tell us the model knows Python syntax well, but we shouldn't rely on it to prove the model can understand a complex 100-file repository. We must rely on our own RAG testing for that.
