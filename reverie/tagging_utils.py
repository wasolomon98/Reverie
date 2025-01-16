# reverie/tagging_utils.py

import json
from reverie.gpt_utils import query_gpt


def add_metadata_tags(message, conversation_id, user_id, timestamp):
    """
    Adds metadata tags to a message in JSON format.

    Args:
        message (dict): The message content.
        conversation_id (str): ID of the conversation.
        user_id (int): ID of the user.
        timestamp (str): Timestamp of the message.

    Returns:
        dict: A dictionary containing the message and its metadata tags.
    """
    tags = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "timestamp": timestamp
    }
    return {"user": message['role'], "content": f"{json.dumps(tags)} {message['content']}"}

def generate_content_tags(messages: dict):
    """
    Generates tags for a set of messages and formats them as JSON.

    Args:
        messages (dict): A dictionary of message IDs and their content.

    Returns:
        dict: A dictionary mapping message IDs to their content and generated tags.
    """
    tagged_messages = {}

    for message_id, content in messages.items():
        try:
            # Query GPT directly for tags
            system_prompt = "Provide relevant subject tags for the message as a JSON array."
            response = query_gpt(
                conversation_messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=50
            )
            tags = json.loads(response)  # Parse JSON output from GPT
        except json.JSONDecodeError as e:
            print(f"Error parsing tags for message {message_id}: {e}")
            tags = []  # Fallback to empty tags
        except Exception as e:
            print(f"Error generating tags for message {message_id}: {e}")
            tags = []  # Fallback to empty tags

        # Store the content and tags in the output
        tagged_messages[message_id] = {
            "content": content,
            "tags": tags
        }

    return tagged_messages
