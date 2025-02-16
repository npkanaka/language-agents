import streamlit as st
from datetime import datetime

from .conversation import ConversationManager
from .llm_client import LLMClient
from .config import Config
from .documentdb import DocumentDB  

class ChatBot:
    """Handles the chatbot's UI and user interactions."""

    def __init__(self):
        """Initializes the chatbot application."""
        self.port = Config.get("llm.port")  # Get LLM port from config
        self.rag_enabled = Config.get("rag.enabled")  # Get RAG setting
        self.db_path = Config.get("paths.db_path")  # Get absolute path to ChromaDB

        self.llm_client = LLMClient(self.port)
        self.conversation_manager = ConversationManager()

        if self.rag_enabled:
            self.document_db = DocumentDB()  # Initialize RAG
            print("📚 RAG is enabled.")

        self.setup_ui()
        
    def setup_ui(self):
        """Configures the Streamlit UI."""
        st.set_page_config(page_title="MoreOn", layout="centered")
        st.title("💬 MoreOn")
        # st.write(f"Connected to API on port **{self.port}**")

        # Clear Chat Button
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    def handle_chat(self):
        """Handles the chat input and response generation."""
        prompt = st.chat_input("Type your message here...")

        if prompt:
            self.conversation_manager.add_message("user", prompt)

            # If RAG is enabled, retrieve relevant documents
            if self.rag_enabled:
                retrieved_docs = self.document_db.query_documents(prompt)
                context = "\n".join(retrieved_docs[:2])  # Use top 2 documents
                prompt_with_context = f"{context}\n\nUser: {prompt}\n Today's date is {datetime.now().strftime('%Y-%m-%d')}\n\nAssistant: "
            else:
                prompt_with_context = prompt

            # Generate response
            bot_reply = self.llm_client.generate_response(prompt_with_context)

            # Add assistant's response
            self.conversation_manager.add_message("assistant", bot_reply)

        # Display chat messages
        self.display_chat()
    
    def display_chat(self):
        """Renders the conversation history in Streamlit."""
        for msg in self.conversation_manager.get_conversation():
            avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.write(msg["content"])
