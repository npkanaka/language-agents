import logging
from abc import ABC, abstractmethod
from datetime import datetime

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class BaseQueryBuilder(ABC):
    """
    Abstract base class for building prompts/queries for the LLM.
    No dependency on a conversation manager is required.
    
    The build_prompt() method accepts:
      - user_prompt: the current user input.
      - conversation: an optional list of previous messages.
    """
    @abstractmethod
    def build_prompt(self, user_prompt: str, conversation: list = None) -> str:
        pass

class RagQueryBuilder(BaseQueryBuilder):
    """
    Query builder for Retrieval-Augmented Generation (RAG).
    It enriches the prompt with external context retrieved from a document database.
    """
    def __init__(self, document_db):
        self.document_db = document_db

    def build_prompt(self, user_prompt: str, conversation: list = None) -> str:
        logger.debug(f"{self.__class__.__name__}.build_prompt() called with user_prompt: {user_prompt}")
        retrieved_docs = self.document_db.query_documents(user_prompt)
        context = "\n".join(retrieved_docs[:2])
        prompt = (
            f"{context}\n\n"
            f"User: {user_prompt}\n"
            f"Today's date is {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"Assistant: "
        )
        logger.debug(f"{self.__class__.__name__}.build_prompt() constructed prompt: {prompt}")
        logger.info(f"{self.__class__.__name__} built prompt using RAG.")
        return prompt

class TraditionalQueryBuilder(BaseQueryBuilder):
    """
    Traditional query builder without external document context.
    It uses the conversation history provided (if any) to build a prompt.
    """
    def build_prompt(self, user_prompt: str, conversation: list = None) -> str:
        logger.debug(f"{self.__class__.__name__}.build_prompt() called with user_prompt: {user_prompt}")
        history = ""
        if conversation:
            # Filter out messages that are not 'user' or 'assistant'
            history_lines = [
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in conversation
                if msg["role"] in ("user", "assistant")
            ]
            history = "\n".join(history_lines)
        prompt = (
            f"Today's date is {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"Conversation history:\n{history}\n"
            f"User: {user_prompt}\n"
            f"Assistant: "
        )
        logger.debug(f"{self.__class__.__name__}.build_prompt() constructed prompt: {prompt}")
        logger.info(f"{self.__class__.__name__} built prompt using traditional query building.")
        return prompt

class DebugQueryBuilder(BaseQueryBuilder):
    """
    Debug query builder that adds diagnostic information using the debug store records.
    This builder no longer references a conversation manager.
    """
    def __init__(self, debug_store):
        self.debug_store = debug_store

    def build_prompt(self, user_prompt: str = None, conversation: list = None) -> str:
        logger.debug("DebugQueryBuilder.build_prompt() called")
        # Retrieve all stored debug records
        records = self.debug_store.get_all_records()
        debug_info = ""
        for record in records:
            debug_info += (
                f"User: {record['full_prompt']}\n"
                f"Assistant: {record['bot_reply']}\n"
            )
            debug_info += "\n\n"
        prompt = (
            f"Today's date is {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"Conversation history:\n{debug_info}\n"
            f"User: Based on the conversation history above, assign a score out of 10 for relevance and accuracy to the most recent response in relation to the most recent user prompt. Output should just be a number/10 and nothing else.\n\n"
            f"Assistant: "
        )
        logger.debug(f"DebugQueryBuilder.build_prompt() constructed prompt: {prompt}")
        logger.info("DebugQueryBuilder built prompt in debug mode.")
        return prompt
