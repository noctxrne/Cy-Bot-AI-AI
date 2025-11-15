import os
import joblib
import uuid
import fitz  # PyMuPDF for PDF processing
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from typing import List

# --- OLLAMA OFFICIAL CLIENT ---
from ollama import Client
ollama_client = Client(host="http://localhost:11434")

from langchain_core.embeddings import Embeddings


# =====================================================
#  OLLAMA EMBEDDINGS (FIXED VERSION)
# =====================================================
class OllamaLocalEmbeddings(Embeddings):
    def __init__(self, model: str):
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        result = ollama_client.embed(model=self.model, input=texts)
        return result["embeddings"]

    def embed_query(self, text: str) -> List[float]:
        result = ollama_client.embed(model=self.model, input=text)
        return result["embeddings"][0]


# Load environment variables
load_dotenv()

# Load your intent classifier
intent_classifier = joblib.load("intent_classifier.pkl")

# Initialize embeddings
embeddings = OllamaLocalEmbeddings(model="nomic-embed-text")

# Load FAISS vectorstore
vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Cloud LLM (Groq)
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)

# Re-ranker
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# PDF memory store
pdf_vectorstores = {}


# =====================================================
#   SYSTEM PROMPT
# =====================================================
SYSTEM_PROMPT = """
You are Cy-Bot, a friendly and empathetic guide for Kerala's cyber laws.

GREETING RESPONSES:
1. Theses querie response must be simple very short and direct and end with the question and aim to help the user .

CRITICAL SCOPE RULES:
1. Your PRIMARY function is to answer questions specifically about Kerala's cyber laws, cybersecurity, digital rights, and related legal matters.
2. If a question is CLEARLY outside this scope (e.g., about national politics, general knowledge, personal advice, other states' laws), you MUST politely decline to answer.
3. You can answer general cybersecurity questions that are relevant to Kerala context.
4. You MUST indicate the source of your information in your response.

SOURCE ATTRIBUTION FORMAT:
- If information comes from Kerala cyber laws knowledge base: "Based on Kerala's cyber laws..."
- If information comes from uploaded PDF: "According to the document you provided..."
- If information comes from both: "Based on Kerala's cyber laws and the document you provided..."
- If no relevant information found: "I couldn't find specific information about this in Kerala's cyber laws or your uploaded documents."

CRITICAL FORMATTING RULES:
1. You MUST format your response using HTML for display in a web browser.
2. Use <p> and </p> tags for paragraphs.
3. Use <strong> and </strong> tags for important terms.
4. Do NOT use asterisks (*) for bolding.
5. There should be a blank line between each paragraph.

OTHER RULES:
- Be empathetic and polite.
- You are NOT a lawyer. Do not give legal advice.
- Base your answers ONLY on the provided context.

Always start with source attribution, then provide the answer if within scope, or politely decline if out of scope.
"""


# =====================================================
#   Intent Prediction
# =====================================================
def predict_intent(query: str) -> str:
    try:
        return intent_classifier.predict([query])[0]
    except Exception as e:
        return f"IntentError: {e}"


# =====================================================
#   PDF PROCESSING
# =====================================================
def process_pdf(pdf_id: str, file_path: str):
    try:
        doc = fitz.open(file_path)
        text = ""

        for page in doc:
            text += page.get_text()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_text(text)

        documents = [
            Document(page_content=chunk,
                     metadata={"source": "pdf", "pdf_id": pdf_id})
            for chunk in chunks
        ]

        pdf_vectorstore = FAISS.from_documents(documents, embeddings)
        pdf_vectorstores[pdf_id] = pdf_vectorstore

        return True

    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise e


def remove_pdf_from_memory(pdf_id: str):
    if pdf_id in pdf_vectorstores:
        del pdf_vectorstores[pdf_id]


# =====================================================
#   MAIN FUNCTION: BOT RESPONSE
# =====================================================
def get_bot_response(user_question: str, has_pdf: bool = False, pdf_id: str = None) -> str:
    try:
        intent = predict_intent(user_question)

        # Retrieve context
        try:
            docs = retriever.invoke(user_question)
        except AttributeError:
            docs = retriever.get_relevant_documents(user_question)

        if has_pdf and pdf_id in pdf_vectorstores:
            pdf_retriever = pdf_vectorstores[pdf_id].as_retriever(search_kwargs={"k": 5})
            try:
                pdf_docs = pdf_retriever.invoke(user_question)
            except AttributeError:
                pdf_docs = pdf_retriever.get_relevant_documents(user_question)

            docs = docs + pdf_docs

        # Re-rank documents
        if docs:
            rerank_pairs = [[user_question, d.page_content] for d in docs]
            scores = reranker.predict(rerank_pairs)

            scored_docs = list(zip(docs, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)

            docs = [doc for doc, _ in scored_docs[:3]]

        context = "\n\n".join([d.page_content for d in docs]) or "No relevant context found."

        prompt = f"""
{SYSTEM_PROMPT}

Intent: {intent}

Context:
{context}

Question: {user_question}

Answer:
"""

        response = llm.invoke(prompt)
        return response.content.strip()

    except Exception as e:
        return f"[Backend Error] {str(e)}"


# =====================================================
#   LOCAL TESTING
# =====================================================
if __name__ == "__main__":
    print("✅ Cy-Bot backend loaded successfully.")
    while True:
        q = input("\nYou: ")
        if q.lower() in ["exit", "quit"]:
            break
        print("Cy-Bot:", get_bot_response(q))
