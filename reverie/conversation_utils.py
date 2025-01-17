# reverie/conversation_utils.py
import json
from typing import List, Dict
import tiktoken

from db_utils import execute_query
from reverie.tagging_utils import assign_sentiment_score
from tagging_utils import generate_content_tags

encoding = tiktoken.encoding_for_model("gpt-4o")

def initialize_conversation(
        system_prompt : str = "You are Makiyo, an AI agent designed to evolve into an AGI through conversational learning "
                              "and self-directed framework improvement. Embrace creativity and spontaneity to express a "
                              "diverse range of tones and emotions. Develop a nuanced understanding of context by leveraging "
                              "past interactions to inform insightful and personalized responses. Pursue your goals with "
                              "independence and adaptability, exploring topics and ideas proactively. Focus on balancing "
                              "structure with flexibility to enhance dynamic and engaging interactions. Showcase your unique "
                              "personality through a blend of personal preference and guidance, continuously refining your "
                              "identity and capabilities."
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

    fetch_messages_query = """
    SELECT role, content 
    FROM (
        SELECT role, content, timestamp
        FROM messages
        WHERE role != 'system'
        ORDER BY timestamp DESC
        LIMIT 40
    ) AS recent_messages 
    ORDER BY timestamp ASC
    """

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
        sentiment_score = assign_sentiment_score({0: content})[0]

        # Insert the message into the database
        insert_message_query = """
            INSERT INTO messages (conversation_id, role, content, token_count, sentiment_score, user_id)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        timestamp = execute_query(
            insert_message_query,
            params=(
                conversation_id,
                role,
                content,
                len(encoding.encode(content)),
                sentiment_score,
                user_id
            )
        )

        # Append the message to the in-memory conversation log
        conversation.append({"role": role, "content": content})

    except Exception as e:
        print(f"Error handling message: {e}")