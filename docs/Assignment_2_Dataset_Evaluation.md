# Assignment-2: Dataset Evaluation

**Course:** CSAI810
**Student Names:** Esraa Abdelrazek & Nancy Abdo
**Date:** 16th February 2026

---

## 1. Introduction

In this study, we evaluate three datasets that are fundamental to how code-generating AI models work. Since our project relies on a model (DeepSeek) to understand and fix code, it is important for us to know what kind of data it was trained on. We looked at a training dataset, a fine-tuning dataset, and an evaluation benchmark.

---

## 2. Selected Datasets

### Dataset 1: The Stack v2 (Training)

* **Content**: A massive collection of source code in 600+ languages from GitHub.
* **Intended Task**: Pre-training LLMs to understand code syntax and structure.
* **Size**: ~67 TB of data (3 billion+ files).
* **Creator**: BigCode Project.
* **Link**: [Hugging Face Dataset](https://huggingface.co/datasets/bigcode/the-stack-v2)
* **Reason for Selection**: Our project's main goal is to analyze full GitHub repositories. Since this dataset is literally a collection of GitHub repositories, it represents the exact type of data our model will face in the real world.
* **Concrete Example**: (Representative of a standard Python source file found in the dataset)
    ```python
    # Path: src/utils/validators.py
    def validate_email(email):
        """Checks if email format is valid using regex."""
        import re
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None
    ```

### Dataset 2: CommitPackFT (Fine-tuning)

* **Content**: "Before and After" code changes (Diffs) paired with commit messages.
* **Intended Task**: Teaching models how to edit code and describe changes (Instruction Tuning).
* **Size**: ~2TB of filtered commit history.
* **Creator**: BigCode Project.
* **Link**: [Hugging Face Dataset](https://huggingface.co/datasets/bigcode/commitpackft)
* **Reason for Selection**: We selected this because our tool will feature "Code Diff Analysis" and "Issue Generation" capabilities. This dataset trains models on how code changes over time (diffs) and how to describe those changes (commit messages), which matches the functionality we intend to build.
* **Concrete Example**: (Shows the Git Diff format used to teach models code changes)
    ```diff
    Commit: 8f9d12a - "Optimize database query for user lookup"
    --- a/server/db.py
    +++ b/server/db.py
    - users = db.execute("SELECT * FROM users")
    - return [u for u in users if u.id == user_id]
    + return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    ```

### Dataset 3: HumanEval (Evaluation)

* **Content**: 164 hand-written Python coding problems.
* **Intended Task**: Testing if a model can write correct code from a description.
* **Size**: Small (164 items).
* **Creator**: OpenAI.
* **Link**: [GitHub Repository](https://github.com/openai/human-eval)
* **Reason for Selection**: We included this as our evaluation benchmark because we need to verify that the model can actually write correct Python code. If the model can't solve these basic problems, we won't be able to trust it to suggest bug fixes in our app.
* **Concrete Example**: (Actual JSON format from the HumanEval benchmark file)
    ```python
    {"task_id": "HumanEval/0",
     "prompt": "def has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\" Check if in given list of numbers, are any two numbers closer to each other than\n    given threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    \"\"\"\n",
     "entry_point": "has_close_elements"}
    ```

---

## 3. Evaluation Criteria Definition

We used these criteria to see if the datasets are good for building our RAG tool.

1. **Task Relevance**

   * **What it measures**: Does the data look like the real work our tool will do?
   * **How it is assessed**: Qualitative (Comparing dataset samples to our RAG inputs).
2. **Data Quality (PII Filtering)**

   * **What it measures**: Is personal info (emails, passwords) removed?
   * **How it is assessed**: Qualitative (Reviewing the cleaning steps used by creators).
   * **Why it matters**: We don't want our model leaking private data.
3. **Opt-Out Mechanisms**

   * **What it measures**: Can developers remove their code from the set?
   * **How it is assessed**: Qualitative (Checking for "Am I in the stack" tools).
   * **Why it matters**: It is about ethical AI usage.
4. **Scale & Diversity**

   * **What it measures**: How many languages and scenarios are covered?
   * **How it is assessed**: Quantitative (Number of languages/files).
5. **Freshness (Temporal Relevance)**

   * **What it measures**: How new is the code?
   * **How it is assessed**: Quantitative (Cutoff date).
   * **Why it matters**: Old data means the model won't know new Python features.
6. **Complexity**

   * **What it measures**: Are the samples simple scripts or full projects?
   * **How it is assessed**: Qualitative (Average file size/structure).

---

## 4. Comparative Table

| Evaluation Criterion        | The Stack v2                                                                           | CommitPackFT                                                                                                                         | HumanEval                                                                                |
| :-------------------------- | :------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------- |
| **1. Task Relevance** | **High**. It contains full files, which is exactly what our RAG system analyzes. | **High (for Diffs)**. This data teaches the model how to suggest fixes and generate issues, which is a key feature of our app. | **Moderate**. It only checks function-level logic, not full project understanding. |
| **2. Data Quality**   | **Excellent**. Uses advanced filtering to remove PII and duplicate code.         | **High**. Filters for "high quality" commit messages to avoid "fix typo" spam.                                                 | **High**. Manually created by humans, so it is 100% clean.                         |
| **3. Opt-Out**        | **Yes**. Has a specific tool for developers to remove their code.                | **Yes**. Follows the same ethical standards as The Stack.                                                                      | **N/A**. It is a benchmark, not user data.                                         |
| **4. Scale**          | **Massive**. Covers almost every language on GitHub.                             | **Large**. Billions of tokens, but limited to code *changes*.                                                                | **Tiny**. Only 164 problems. Too small to learn from, only for testing.            |
| **5. Freshness**      | **Variable**. Depends on when the snapshot was taken.                            | **Variable**. Needs regular updates to catch new coding patterns.                                                              | **Static**. Created in 2021. It does not know about Python 3.12 updates.           |
| **6. Complexity**     | **High**. Includes complex, multi-file projects.                                 | **Medium**. Focuses on the logic of a single change/edit.                                                                      | **Low**. Isolated functions only.                                                  |

---

## 5. Discussion

For our project, we learned that:

* **The Stack v2** is the most important dataset because it will give our model the broad knowledge to read any Python file we upload.
* **CommitPackFT** is likely why DeepSeek is so good at tasks like "Code Diff" and "Generate Issues"—it was trained on how developers actually fix bugs, which is why we want to use this model.
* **HumanEval** is good for a quick score, but we realize we cannot rely on it alone to judge if the model will handle our complex RAG tasks.

---

## 6. References

1. **The Stack v2**: Lozhkov, A., et al. (2024). *StarCoder 2 and The Stack v2*. Hugging Face. Blog: [https://huggingface.co/blog/starcoder2](https://huggingface.co/blog/starcoder2), Dataset: [https://huggingface.co/datasets/bigcode/the-stack-v2](https://huggingface.co/datasets/bigcode/the-stack-v2)
2. **CommitPackFT**: Muennighoff, N., et al. (2023). *OctoPack: Instruction Tuning Code LLMs*. Paper: [https://arxiv.org/abs/2308.07124](https://arxiv.org/abs/2308.07124), Dataset: [https://huggingface.co/datasets/bigcode/commitpackft](https://huggingface.co/datasets/bigcode/commitpackft)
3. **HumanEval**: OpenAI. (2021). *Evaluating Large Language Models Trained on Code*. Repository: [https://github.com/openai/human-eval](https://github.com/openai/human-eval)
4. **BigCode Project**: (The organization behind both The Stack v2 and CommitPackFT). *BigCode: Open Scientific Collaboration on Code AI*. [https://www.bigcode-project.org/](https://www.bigcode-project.org/)
