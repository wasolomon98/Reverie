# reverie/tagging_utils.py

import json
from reverie.gpt_utils import query_gpt

def assign_sentiment_score(messages: dict):
    """
    Assigns a sentiment score to each message in the given dictionary.

    Args:
        messages (dict): A dictionary where keys are message IDs and values are message contents.

    Returns:
        dict: A dictionary with the same keys as the input, where the values are the assigned sentiment scores.
    """
    scored_messages = {}
    for message_id, content in messages.items():
        try:
            # Query GPT directly for sentiment score
            system_prompt = (
                "Generate a decimal sentiment score for the passed message in the range [-1.0, 1.0]. "
                "The score should represent the sentiment, where -1.0 is very negative, 0 is neutral, "
                "and 1.0 is very positive. Return only the numeric value rounded to the nearest tenths place. "
                "Provide no other output or explanation."
            )
            response = query_gpt(
                conversation_messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=50
            )

            # Extract and validate the response
            try:
                sentiment_score = float(response.strip())
                if not (-1.0 <= sentiment_score <= 1.0):
                    raise ValueError("Sentiment score out of valid range.")
            except (ValueError, TypeError):
                print(f"Invalid sentiment score for message ID {message_id}: {response}")
                sentiment_score = 0.0  # Default to neutral if parsing fails

        except Exception as e:
            print(f"Error generating sentiment score for message ID {message_id}: {e}")
            sentiment_score = 0.0  # Fallback to neutral on error

        # Assign the score to the corresponding message ID
        scored_messages[message_id] = sentiment_score

    return scored_messages


def generate_content_tags(messages: dict):
    """
    Generates predefined tags for a set of messages and formats them as JSON.

    Args:
        messages (dict): A dictionary of message IDs and their content.

    Returns:
        dict: A dictionary mapping message IDs to their content and the generated tags.
    """
    # Predefined list of tags
    predefined_tags = [
        "Informational",
        "Question",
        "Instructional",
        "Feedback",
        "Positive Sentiment",
        "Negative Sentiment",
        "Neutral Sentiment",
        "Greeting",
        "Farewell",
        "Clarification",
        "Agreement",
        "Disagreement",
    ]

    tagged_messages = {}

    # System prompt to classify messages
    system_prompt = (
        "For the given message, identify all applicable tags from the following list: "
        f"{', '.join(predefined_tags)}. "
        "Return the matching tags as a JSON array without any additional explanation."
    )

    for message_id, content in messages.items():
        try:
            # Query GPT for tags
            response = query_gpt(
                conversation_messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                temperature=0.3,
                max_tokens=100,
            )

            # Parse JSON output from GPT
            tags = json.loads(response)

            # Ensure tags are valid and within the predefined list
            valid_tags = [tag for tag in tags if tag in predefined_tags]

        except json.JSONDecodeError as e:
            print(f"Error parsing tags for message {message_id}: {e}")
            valid_tags = []  # Fallback to empty tags
        except Exception as e:
            print(f"Error generating tags for message {message_id}: {e}")
            valid_tags = []  # Fallback to empty tags

        # Store the content and valid tags in the output
        tagged_messages[message_id] = {
            "content": content,
            "tags": valid_tags,
        }

    return tagged_messages
