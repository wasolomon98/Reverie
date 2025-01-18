# reverie/context_utils.py

import re
from collections import Counter, deque

class ContextManager:
    """
    Manages a circular buffer and cached keyword frequencies.
    """
    def __init__(self, buffer_size=50):
        self.buffer = CircularBuffer(buffer_size)
        self.keyword_counter = Counter()

    def update_context(self, new_message: str):
        # Add the new message to the buffer
        self.buffer.add_message(new_message)
        # Re-extract the keywords from the updated buffer
        self.keyword_counter = extract_keywords(self.buffer.get_messages())

    def get_relevance_score(self, message: str) -> int:
        return relevance_score(message, self.keyword_counter)

class CircularBuffer:
    def __init__(self, size):
        self.buffer = deque(maxlen=size)

    def add_message(self, message):
        """Add a new message, automatically discarding oldest if full."""
        self.buffer.append(message)

    def get_messages(self):
        """Retrieve all messages currently in the buffer."""
        return list(self.buffer)

stop_words = {"the", "is", "and", "to", "a", "of"}  # Expand as needed

def extract_keywords(messages):
    """
    A simple regex-based tokenizer that removes non-alphanumeric chars,
    lowercases, and filters out stop words.
    """
    text = " ".join(messages)
    tokens = re.findall(r"\b\w+\b", text.lower())
    filtered_tokens = [t for t in tokens if t not in stop_words]
    keyword_frequency = Counter(filtered_tokens)
    return keyword_frequency

def relevance_score(message, keyword_frequency):
    tokens = re.findall(r"\b\w+\b", message.lower())
    score = 0
    for token in tokens:
        if token in keyword_frequency:
            # Weight can simply be the frequency or a custom weighting
            score += keyword_frequency[token]
    return score

