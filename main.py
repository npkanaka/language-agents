import logging
from src.chatbot import ChatBot

# Configure logging with default level INFO
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

if __name__ == "__main__":
    app = ChatBot()
    app.handle_chat()
