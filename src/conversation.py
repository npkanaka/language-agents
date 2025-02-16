import streamlit as st

class ConversationManager:
    """Handles chat history and message formatting for LLM prompts."""

    def __init__(self):
        """Initializes an empty conversation history."""
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def reset_conversation(self):
        """Clears the chat history."""
        st.session_state.messages = []

    def add_message(self, role, content):
        """Adds a message to the chat history."""
        st.session_state.messages.append({"role": role, "content": content})

    def get_conversation(self):
        """Returns the entire conversation history."""
        return st.session_state.messages

    def build_prompt(self):
        """
        Converts the entire conversation history into a formatted string.
        Ensures the LLM knows where to continue from.
        """
        conversation = []
        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg["content"]
            conversation.append(f"{role.capitalize()}: {content}")

        conversation.append("Assistant:")  # Ensures LLM knows where to continue
        return "\n".join(conversation)
