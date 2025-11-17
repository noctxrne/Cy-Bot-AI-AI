import json
# --- REMOVED THE OLLAMA IMPORT ---
from langchain_community.vectorstores import FAISS
# --- REMOVED THE CUSTOM EMBEDDINGS IMPORT ---
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings  # <-- We will use this


# --- REMOVED THE CUSTOM OllamaLocalEmbeddings CLASS ---
# (We don't need it because we are using the HuggingFaceEmbeddings class directly)
# ---

def build_vector_store():
    """
    Builds a FAISS vector store using Hugging Face embeddings.
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

    # 2. Initialize our Hugging Face Embedding Model
    try:
        # --- THIS IS THE KEY CHANGE ---
        # We are matching the model from bot_backend.py
        print("📥 Initializing Hugging Face embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        print("✅ Hugging Face model initialized.")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize Hugging Face model. Error: {e}")
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