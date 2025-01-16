# reverie/gpt_utils.py

import os
from typing import List, Dict
import openai
from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root if present

openai.api_key = os.getenv("OPENAI_API_KEY")

def query_gpt(
    conversation_messages: List[Dict],
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_tokens: int = 400,
    **kwargs
) -> str:
    """
    Sends the given text to your GPT-4o mini model (or another Chat model)
    and returns the model's response.
    """
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=conversation_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        print(f"{response}")

        # Extract and return the assistant’s reply
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during GPT query: {e}")
        return ""
