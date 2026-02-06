from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

class RAGPipeline:
    def __init__(self, llm, retriever):
        self.llm = llm
        self.retriever = retriever
        self.qa_chain = self._build_chain()

    def _build_chain(self):
        template = """You are an expert software engineer. Use the following pieces of retrieved code context to answer the user's question. 
        If you don't know the answer, just say that you don't know.
        
        Context:
        {context}
        
        Question: {question}
        
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
            "diff": f"Compare the following external code/logic with the existing repository context: \n\n{extra_context}\n\nHighlight key differences, potential conflicts, and suggest how to merge or improve them."
        }
        
        query_text = prompts.get(task_type, "Analyze the code.")
        return self.query(query_text)
