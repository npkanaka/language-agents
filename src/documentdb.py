import os
import requests
import chromadb
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF for PDF text extraction
import yaml

from src.config import Config  # Import the configuration settings

class DocumentDB:
    """Handles document storage and retrieval using ChromaDB."""

    def __init__(self):
        """Initialize the ChromaDB client, embedding model, and configuration."""
        self.documents_folder = Config.get("paths.documents_folder")  # Ensure absolute path
        self.links_file = Config.get("paths.links_file")  # Ensure absolute path
        self.db_path = Config.get("paths.db_path")  # Ensure absolute path
        self.rebuild_db = Config.get("rag.rebuild_db")  # Boolean value

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection("documents")

        # Load embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # If rebuild flag is set, clear the database and re-index everything
        if self.rebuild_db:
            print("🔄 Rebuilding ChromaDB...")
            if self.collection.count() > 0:  # Only delete if there are documents
                    self.collection.delete(ids=self.collection.get()["ids"])  # Delete all documents by IDs
                    print("🧹 ChromaDB cleared successfully.")
            else:
                print("⚠️ ChromaDB is already empty, skipping deletion.")
            
            self.fetch_and_store_documents()    

    def download_pdf(self, url):
        """Download a PDF file from a URL and save it locally."""
        if not os.path.exists(self.documents_folder):
            os.makedirs(self.documents_folder)

        filename = url.split("/")[-1]
        save_path = os.path.join(self.documents_folder, filename)

        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
            print(f"✅ Downloaded: {save_path}")
        else:
            print(f"⚠️ Failed to download {url}. Status Code: {response.status_code}")

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file using PyMuPDF."""
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text("text") for page in doc)
        return text

    def load_documents(self):
        """Load text from PDFs and .txt files in the documents folder."""
        documents = []
        for filename in os.listdir(self.documents_folder):
            file_path = os.path.join(self.documents_folder, filename)

            if filename.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as file:
                    text = file.read()
                    documents.append((filename, text))

            elif filename.endswith(".pdf"):
                text = self.extract_text_from_pdf(file_path)
                print(f"✅ Extracted text from {filename} ({len(text)} characters)")
                documents.append((filename, text))

        return documents

    def store_documents(self):
        """Process and store documents in ChromaDB."""
        documents = self.load_documents()
        for filename, content in documents:
            if len(content.strip()) == 0:
                print(f"⚠️ Skipping empty file: {filename}")
                continue

            embedding = self.model.encode(content).tolist()
            self.collection.add(ids=[filename], embeddings=[embedding], metadatas=[{"content": content}])

        print("✅ All documents have been processed and stored.")

    def fetch_and_store_documents(self):
        """Read links from document_links.txt and download all PDFs."""
        if not os.path.exists(self.links_file):
            print(f"⚠️ {self.links_file} not found. Please create it and add document links.")
            return

        with open(self.links_file, "r") as file:
            urls = [line.strip() for line in file.readlines() if line.strip()]

        for url in urls:
            self.download_pdf(url)

        self.store_documents()

    def query_documents(self, query_text, top_k=3):
        """Retrieve the most relevant documents based on the query."""
        print("🔍 Checking ChromaDB document count:", self.collection.count())

        query_embedding = self.model.encode(query_text).tolist()
        results = self.collection.query(query_embeddings=[query_embedding], n_results=top_k)

        retrieved_docs = [item["content"] for item in results["metadatas"][0]]
        return retrieved_docs


if __name__ == "__main__":
    db = DocumentDB()
    query = "head digital works"
    relevant_docs = db.query_documents(query)
    print("\n🔍 Retrieved Documents:", len(relevant_docs))
