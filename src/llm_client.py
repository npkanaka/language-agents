import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class LLMClient:
    """Handles communication with the LLM API."""

    def __init__(self, port):
        """Initializes with the API URL based on the provided port."""
        self.api_url = f"http://localhost:{port}/generate"
        logger.info(f"LLMClient initialized with API URL: {self.api_url}")

    def generate_response(self, prompt):
        """Sends the chat prompt to the LLM API and returns the assistant's response."""
        try:
            logger.debug(f"Sending request to LLM API: {prompt[:100]}...")
            response = requests.post(self.api_url, json={"prompt": prompt})
            if response.status_code == 200:
                response_json = response.json()
                result = response_json.get("response", "⚠️ No response").split("assistant\n\n")[-1]
                logger.info("Received response from LLM API.")
                return result
            else:
                logger.warning(f"LLM API error: {response.status_code}")
                return f"⚠️ LLM API error: {response.status_code}"
        except Exception as e:
            logger.error(f"Error connecting to LLM API: {e}")
            return f"⚠️ Error connecting to LLM API: {e}"
