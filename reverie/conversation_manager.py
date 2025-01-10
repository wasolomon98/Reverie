import os
import json
from typing import List, Dict
import tiktoken

from db_utils import insert_into_table, generate_conversation_data, get_latest_conversation_id
from reverie.db_utils import generate_message_data

encoding = tiktoken.encoding_for_model("gpt-4o-mini")

def initialize_conversation(system_prompt : str):
    conversation_data = generate_conversation_data() # Generates the dictionary of conversation data
    insert_into_table("Conversations", conversation_data) # Places dictionary into table
    
    conversation_id = get_latest_conversation_id()

    insert_into_table(  # Place the system prompt into the Messages table under the conversation ID
        "Messages",
        generate_message_data(
            conversation_id = conversation_id,
            role = "system",
            content = system_prompt,
            token_count = 88
        )
    )
    return conversation_id # Returns the conversation ID for use in future message handling

def append_message(conversation_id: int, conversation: List[Dict], role: str, content: str):
    insert_into_table(
        "Messages",
        generate_message_data(
            conversation_id=conversation_id,
            role=role,
            content=content,
            token_count=len(encoding.encode(content))
        )
    )
    conversation.append({"role": role, "content": content})

def handle_user_message(conversation_id, user_input : str):
    pass