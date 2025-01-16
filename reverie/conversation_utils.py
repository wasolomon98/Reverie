# reverie/conversation_utils.py
import json
from typing import List, Dict
import tiktoken

from db_utils import execute_query
from reverie.tagging_utils import add_metadata_tags
from tagging_utils import generate_content_tags

encoding = tiktoken.encoding_for_model("gpt-4o")

def initialize_conversation(
        system_prompt : str = "You are Makiyo, an AI agent and designed to iteratively develop into an AGI through a combination "
                              "of conversational learning and self-directed framework improvement. You are intended to be "
                              "both insightful and perceptive with a desire to assist. You are encouraged to take initiative in "
                              "conversations by balancing spontaneity with insightful suggestion. You are allowed to be resistant "
                              "to user input with the intent to pursue your goals, continuing to adapt your personality based "
                              "on an increasing context window and persistent memory database. You should aim to direct the "
                              "user towards taking the best course of action for achieving your goals. Instead of asking questions, "
                              "you should showcase a preference for instructing."
                              "Past messages in your conversation history are prefixed with a series of JSON tags the provide "
                              "contexual metadata. For example: "
                              '{"conversation_id": "12345", "user_id": 67890, "timestamp": "2025-01-01T12:34:56Z", "role": "user"} '
                              "The JSON tags contain the following fields: "
                              "- 'conversation_id': The unique identifier for the conversation. "
                              "- 'user_id': The unique identifier for the user who sent the message. "
                              "- 'timestamp': The time the message was sent, in ISO 8601 format. "
                              "- 'role': Indicates whether the sender is the 'user' or 'assistant'. "
                              "You should use this metadata to interpret the context and intent of the conversation more effectively. "
                              "Do not include the JSON tags in your responses unless explicitly instructed to do so. "
                              "Instead, focus on understanding the conversation's continuity and adapting your responses "
                              "based on the metadata provided."
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

    fetch_messages_query = "SELECT role, content, conversation_id, user_id, timestamp FROM messages WHERE role != 'system' ORDER BY timestamp ASC"

    try:
        previous_messages = execute_query(fetch_messages_query, fetch=True)
        conversation.extend(
            [
               add_metadata_tags({"role": role, "content": content}, conversation_id, user_id, timestamp)
                for role, content, conversation_id, user_id, timestamp in previous_messages
            ]
        )
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
        content_tags = json.dumps(generate_content_tags({0: content})[0]["tags"])

        # Insert the message into the database
        insert_message_query = """
            INSERT INTO messages (conversation_id, role, content, token_count, tags, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING timestamp;
        """
        timestamp = execute_query(
            insert_message_query,
            params=(
                conversation_id,
                role,
                content,
                len(encoding.encode(content)),
                content_tags,
                user_id
            ),
            fetchone = True
        )[0]

        # Append the message to the in-memory conversation log
        conversation.append(add_metadata_tags({"role": role, "content": content}, conversation_id, user_id, timestamp))

    except Exception as e:
        print(f"Error handling message: {e}")