import datetime
import json
import os
        
class DebugStore:
    """
    A store to hold full prompts and replies for debugging purposes.
    This in-memory store keeps a list of records where each record contains:
      - timestamp: When the record was created.
      - full_prompt: The full prompt sent to the LLM.
      - bot_reply: The reply from the LLM.
      - verifier_reply: The verifier's reply (if available).
    """
    def __init__(self):
        self.records = []

    def add_record(self, full_prompt: str, bot_reply: str, verifier_reply: str = None):
        record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "full_prompt": full_prompt,
            "bot_reply": bot_reply,
            "verifier_reply": verifier_reply,
        }
        self.records.append(record)

    def update_last_record_with_verifier(self, verifier_reply: str):
        if self.records:
            self.records[-1]["verifier_reply"] = verifier_reply

    def get_all_records(self):
        return self.records

    def clear(self):
        self.records = []

    def save_records_to_file(self, file_path: str = None) -> str:
        """
        Saves all debug records to a JSON file.
        
        If file_path is not provided, the file is saved in the current directory with a generated filename.
        If file_path is provided and it is a directory, a filename based on the current timestamp is generated
        and attached to that directory.
        If a full file path is provided (including filename), it will be used as-is.
        
        Ensures the target directory exists before writing.
        
        Returns:
            The full file path used for saving the debug records.
        """
        
        # Generate a timestamp-based filename.
        # timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        generated_filename = "debug_logs.json"

        if file_path is None:
            # No path provided, so use the generated filename in the current directory.
            file_path = generated_filename
        else:
            # If file_path is a directory, attach the generated filename.
            if os.path.isdir(file_path):
                file_path = os.path.join(file_path, generated_filename)
            # Otherwise, file_path is assumed to be a full file path (including filename).

        # Ensure that the directory for the file exists.
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.records, f, indent=4)
        except Exception as e:
            raise IOError(f"Failed to save debug logs to {file_path}: {e}")
        return file_path
