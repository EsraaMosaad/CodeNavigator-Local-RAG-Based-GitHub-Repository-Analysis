from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

class RAGPipeline:
    def __init__(self, llm, retriever, repo_context: dict = None):
        self.llm = llm
        self.retriever = retriever
        self.repo_context = repo_context or {}
        self.qa_chain = self._build_chain()

    def _build_chain(self):
        # Format context string
        context_str = ""
        if self.repo_context:
            context_str = "Repository Metadata:\n"
            for k, v in self.repo_context.items():
                context_str += f"- {k}: {v}\n"
        
        template = f"""You are an expert software engineer.
        {context_str}
        Use the following pieces of retrieved code context to answer the user's question. 
        If you don't know the answer, just say that you don't know.
        
        Context:
        {{context}}
        
        Question: {{question}}
        
        Helpful Answer:"""
        
        prompt = PromptTemplate(template=template, input_variables=["context", "question"])
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )

    def query(self, question: str):
        try:
            result = self.qa_chain.invoke({"query": question})
            return result["result"], result["source_documents"]
        except Exception as e:
            return f"Error: {str(e)}", []

    def query_specialized(self, task_type: str, extra_context: str = ""):
        prompts = {
            "summarize": "Provide a comprehensive summary of this repository. Include the project goal, architecture, and key modules. Also, generate a Mermaid.js class diagram representing the core structure.",
            "issues": "Act as a Senior Code Reviewer. Analyze the retrieved code and generate 3 meaningful GitHub Issues. For each issue, provide: \n1. **Title**\n2. **Description** (current behavior vs expected)\n3. **Suggested Fix**\n4. **Labels** (e.g., bug, refactor, security).",
            "diagrams": "Analyze the control flow of the main logic. Generate a Mermaid.js sequence diagram or flowchart that visualizes how data moves through the system. Explain the flow textually first.",
            "diff": f"You are analyzing a Git Diff between two branches. Below is the raw diff output:\n\n{extra_context}\n\nTasks:\n1. Summarize the key changes (files modified, added, removed).\n2. Explain the logic changes in plain English.\n3. Identify any potential bugs or security risks introduced by these changes."
        }
        
        query_text = prompts.get(task_type, "Analyze the code.")
        return self.query(query_text)
