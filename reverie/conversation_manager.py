import os
import json
from typing import List, Dict
import tiktoken

DEFAULT_LOGFILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "conversation.json"
)

# Define file paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONVERSATION_LOG = os.path.join(DATA_DIR, "conversation.json")
SUMMARY_LOG = os.path.join(DATA_DIR, "conversation_summaries.json")

# Tokenizer setup
ENCODING = tiktoken.get_encoding("cl100k_base")  # Adjust based on model

# Summarization threshold
SUMMARY_THRESHOLD = 3000  # Example token threshold

def load_conversation(logfile: str = DEFAULT_LOGFILE) -> List[Dict]:
    if not os.path.exists(logfile):
        return [{"role": "system", "content": "You are a helpful AI assistant."}]

    try:
        with open(logfile, "r", encoding="utf-8") as f:
            conversation = json.load(f)
            if isinstance(conversation, list) and all(
                    isinstance(msg, dict) and "role" in msg and "content" in msg for msg in conversation
            ):
                return conversation
            else:
                print("Invalid conversation format. Starting fresh.")
                return [{"role": "system", "content": "You are a helpful AI assistant."}]
    except Exception as e:
        print(f"Error loading conversation log: {e}")
        return [{"role": "system", "content": "You are a helpful AI assistant."}]


def save_conversation(conversation: List[Dict], logfile: str = DEFAULT_LOGFILE):
    os.makedirs(os.path.dirname(logfile), exist_ok=True)
    try:
        with open(logfile, "w", encoding="utf-8") as f:
            json.dump(conversation, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving conversation log: {e}")


def append_message(conversation: List[Dict], role: str, content: str):
    """
    Appends a new message to the conversation list in-memory.
    Then you can call save_conversation() to persist.
    """
    conversation.append({"role": role, "content": content})

#
# Optional: Summarize, truncate, or handle large logs here.
# For example:
#
# def truncate_conversation_if_needed(conversation: List[Dict], max_length=40):
#     if len(conversation) > max_length:
#         # remove oldest user/assistant pairs or summarize them
#         ...
