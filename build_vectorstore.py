import json
import ollama
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List

# --- Create a Custom Embeddings Class for Ollama ---
class OllamaLocalEmbeddings(Embeddings):
    """
    Custom LangChain embeddings class that uses the official 'ollama' library.
    """
    def __init__(self, model: str):
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # The response object has an 'embeddings' attribute, which is the list of vectors.
        return ollama.embed(model=self.model, input=texts).embeddings

    def embed_query(self, text: str) -> List[float]:
        # For a single text, the response object also has an 'embeddings' attribute.
        # We just need the first (and only) vector from the list.
        return ollama.embed(model=self.model, input=text).embeddings[0]

def build_vector_store():
    """
    Builds a FAISS vector store using the direct Ollama library.
    """
    print("🚀 Starting vector store build process...")

    # 1. Load the data
    try:
        with open("cyber_laws.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print("✅ Successfully loaded cyber_laws.json")
    except Exception as e:
        print(f"❌ ERROR: Failed to load JSON file. {e}")
        return

    # 2. Initialize our custom Ollama Embedding Model
    try:
        print("📥 Initializing direct Ollama embedding model (nomic-embed-text)...")
        embeddings = OllamaLocalEmbeddings(model="nomic-embed-text")
        print("✅ Direct Ollama model initialized.")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize Ollama model. Is Ollama running? Error: {e}")
        return

    # 3. Process data into documents (same logic as before)
    documents = []
    print("📄 Processing documents from JSON data...")
    
    for section in data:
        content = section.get("description", "")
        if content:
            metadata = {
                "source": "cyber_laws.json",
                "chapter": section.get("chapter", "N/A"),
                "section": section.get("section", "N/A"),
                "section_name": section.get("section_name", "N/A")
            }
            documents.append(Document(page_content=content, metadata=metadata))
    
    if not documents:
        print("❌ ERROR: No documents were created. Check the JSON structure and the 'description' field.")
        return

    print(f"✅ Created {len(documents)} documents.")

    # 4. Split documents into chunks
    print("✂️ Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    print(f"✅ Split into {len(texts)} chunks.")

    # 5. Create the FAISS vector store
    print("🧠 Creating FAISS vector store... (This may take a few minutes)")
    try:
        vectorstore = FAISS.from_documents(texts, embeddings)
        print("✅ FAISS vector store created in memory.")
    except Exception as e:
        print(f"❌ ERROR: Failed to create FAISS vector store. Error: {e}")
        return

    # 6. Save the vector store to disk
    print("💾 Saving vector store to disk...")
    try:
        vectorstore.save_local("faiss_index")
        print("🎉 SUCCESS! Vector store saved to 'faiss_index' folder.")
    except Exception as e:
        print(f"❌ ERROR: Failed to save vector store. Error: {e}")
        return

if __name__ == "__main__":
    build_vector_store()