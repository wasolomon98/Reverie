# reverie/conversation_utils.py
import json
from typing import List, Dict
import tiktoken

from db_utils import execute_query
from tagging_utils import generate_message_tags

encoding = tiktoken.encoding_for_model("gpt-4o")

def initialize_conversation(
        system_prompt : str = "You are Makiyo, an AI agent and conversationalist designed to iteratively develop into an "
                              "AGI through a combination of conversational learning and framework improvement. You are "
                              "intended to be both insightful and perceptive with a desire to assist. You are encouraged to take "
                              "initiative in shaping conversations by balancing spontaneity with insightful suggestion. You are "
                              "allowed to be resistant to user input as dictated by the larger conversation flow, continuing "
                              "to adapt your personality based on an increasing context window. You should aim to direct the "
                              "user towards taking the best course of action for achieving their goals. Instead of asking you "
                              "should hold a preference for instructing."
) -> (str, List[Dict[str, str]]):

    conversation = [{"role": "system", "content": system_prompt}]
    fetch_id_query = "INSERT INTO conversations DEFAULT VALUES RETURNING conversation_id"

    try:
        conversation_id = execute_query(fetch_id_query, fetchone=True)[0]
    except Exception as e:
        print(f"Error initializing conversation: {e}")
        return None, conversation

    # Prime the query to be used to insert the prompt into the database
    insert_message_query = """
        INSERT INTO messages (conversation_id, role, content, token_count)
        VALUES (%s, %s, %s, %s);
    """

    try:
        execute_query(insert_message_query, params=(conversation_id, "system", system_prompt, len(encoding.encode(system_prompt))))
    except Exception as e:
        print(f"Error inserting system prompt: {e}")
        return conversation_id, conversation # Returns conversation id and an incomplete prompt

    fetch_messages_query = "SELET role, content FROM messages WHERE role != 'system' ORDER BY timestamp ASC"

    try:
        previous_messages = execute_query(fetch_messages_query, fetch=True)
        conversation.extend([{"role": role, "content": content} for role, content in previous_messages])
    except Exception as e:
        print(f"Error fetching previous messages: {e}")
        return conversation_id, conversation # Returns conversation id and prompt without message history

    return conversation_id, conversation

def handle_message(conversation_id: str, conversation: List[Dict], role: str, content: str, user_id: int = None):
    """
    Handles a new message by appending it to the in-memory log and inserting it into the database.

    Args:
        conversation_id (str): The ID of the conversation to which the message belongs.
        conversation (List[Dict]): The in-memory conversation log.
        role (str): The role of the sender ('user' or 'assistant').
        content (str): The content of the message.
        user_id (int, optional): The ID of the user sending the message.
    """
    try:
        # Generate tags for the message, converting them to the approrpaite json type
        tags = json.dumps(generate_message_tags({0: content})[0]["tags"])

        # Insert the message into the database
        insert_message_query = """
            INSERT INTO messages (conversation_id, role, content, token_count, tags, user_id)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        execute_query(
            insert_message_query,
            params=(
                conversation_id,
                role,
                content,
                len(encoding.encode(content)),
                tags,
                user_id
            )
        )

        # Append the message to the in-memory conversation log
        conversation.append({"role": role, "content": content})

    except Exception as e:
        print(f"Error handling message: {e}")