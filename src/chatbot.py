import streamlit as st
from .conversation import ConversationManager
from .llm_client import LLMClient
from .config import Config
from .documentdb import DocumentDB  
from .promptbuilder import RagQueryBuilder, TraditionalQueryBuilder, DebugQueryBuilder
from .debug_store import DebugStore

class ChatBot:
    """Handles the chatbot's UI and user interactions."""
    def __init__(self):
        """Initializes the chatbot application."""
        self.port = Config.get("llm.port")             # Get LLM port from config
        self.db_path = Config.get("paths.db_path")        # Get absolute path to ChromaDB

        self.llm_client = LLMClient(self.port)
        
        # Persist the conversation manager in session_state.
        if "conversation_manager" not in st.session_state:
            st.session_state.conversation_manager = ConversationManager()
        self.conversation_manager = st.session_state.conversation_manager

        # Persist DebugStore across interactions.
        if "debug_store" not in st.session_state:
            st.session_state.debug_store = DebugStore()
        self.debug_store = st.session_state.debug_store

        self.document_db = None  # Will be created on demand if RAG is enabled

        self.setup_ui()
        
    def setup_ui(self):
        """Configures the Streamlit UI."""
        st.set_page_config(page_title="MoreOn", layout="centered")
        st.title("💬 MoreOn")
        
        # Place the RAG toggle in the main area.
        # st.markdown("**Toggle RAG Mode:**")
        st.checkbox("Retrieve?", key="rag_enabled", value=False)

        # Clear Chat Button
        if st.button("Clear Chat"):
            st.session_state.messages = []
            self.debug_store.clear()  # Also clear the debug store
            st.session_state.conversation_manager = ConversationManager()
            st.rerun()

    def handle_chat(self):
        """Handles the chat input and response generation."""
        prompt = st.chat_input("Type your message here...")

        if prompt:
            
            # Check the current value of the RAG toggle from the UI.
            rag_enabled = st.session_state.get("rag_enabled", False)
            
            # Build the query builder on demand.
            if rag_enabled:
                # If RAG is enabled and the document DB hasn't been created yet, create it.
                if self.document_db is None:
                    self.document_db = DocumentDB()
                # Instantiate RagQueryBuilder with only the document_db.
                query_builder = RagQueryBuilder(self.document_db)
                # For RAG, conversation history isn't used, so no need to pass it.
                full_prompt = query_builder.build_prompt(prompt)
            else:
                # Use TraditionalQueryBuilder which uses conversation history.
                query_builder = TraditionalQueryBuilder()
                conversation = self.conversation_manager.get_conversation()
                full_prompt = query_builder.build_prompt(prompt, conversation)
            
            # Generate the assistant's response.
            bot_reply = self.llm_client.generate_response(full_prompt)
            
            # Add the user prompt and assistant's reply to the conversation history.
            self.conversation_manager.add_message("user", prompt)
            self.conversation_manager.add_message("assistant", bot_reply)
            
            # Store the full prompt and bot reply in the debug store.
            self.debug_store.add_record(full_prompt, bot_reply)
            
            # Verifier: Build a debug prompt using the DebugQueryBuilder.
            debug_qb = DebugQueryBuilder(self.debug_store)
            verifier_prompt = debug_qb.build_prompt()
            verifier_reply = self.llm_client.generate_response(verifier_prompt)
            
            # Add the verifier's reply to the conversation history.
            self.conversation_manager.add_message("verifier", verifier_reply)
            
            # Update the last debug record with the verifier reply.
            self.debug_store.update_last_record_with_verifier(verifier_reply)

            # Save all debug records to file.
            # (Assumes Config.get("paths.debug_store") returns a directory or full file path)
            debug_store_filepath = Config.get("paths.debug_store")
            saved_path = self.debug_store.save_records_to_file(debug_store_filepath)
            print(f"Debug records saved to {saved_path}.")

        # Display the updated chat history.
        self.display_chat()
    
    def display_chat(self):
        """Renders the conversation history in Streamlit."""
        for msg in self.conversation_manager.get_conversation():
            if msg["role"] == "user":
                avatar = "🧑‍💻"
            elif msg["role"] == "assistant":
                avatar = "🤖"
            elif msg["role"] == "verifier":
                avatar = "🔍"
            else:
                avatar = "❓"
            with st.chat_message(msg["role"], avatar=avatar):
                st.write(msg["content"])
