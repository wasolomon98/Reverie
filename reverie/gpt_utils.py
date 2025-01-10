# reverie/gpt_utils.py

import os
from typing import List, Dict
import openai
from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root if present

openai.api_key = os.getenv("OPENAI_API_KEY")

def query_gpt(
    conversation_messages: List[Dict],
    model: str = "gpt-4o-mini",
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
        # Extract and return the assistant’s reply
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during GPT query: {e}")
        return ""

def query_gpt_binary(query: str) -> str:
    """
    Queries GPT for a binary decision (e.g., yes/no).
    """

    prompt_plus_query = [
        {"role": "system",
         "content": "You are an assistant tasked with answering questions with a binary 'Yes' or 'No' response. Do not provide any explanation."},
        {"role": "user", "content": "Is the sky blue?"},
        {"role": "assistant", "content": "Yes."},
        {"role": "user", "content": query}
    ]

    return query_gpt(
        prompt_plus_query,
        model="gpt-4o-mini",
        temperature=0.0,
        max_tokens=20
    )

