import json

import db_utils
import gpt_utils
from reverie.db_utils import get_untagged_conversation_ids, get_all_messages_in_conversation, update_table_column_by_id
from reverie.gpt_utils import query_gpt_for_message_tags


def generate_subject_tags(messages: dict):
    tagged_messages = {}
    for message_id, content in messages.items():
        try:
            message_with_tags = query_gpt_for_message_tags(content)
        except Exception as e:
            print(f"Error generating tags for message {message_id}: {e}")
            message_with_tags = {"content": content, "tags": []}

        tagged_messages[message_id] = {
            "content" : message_with_tags["content"],
            "tags" : message_with_tags["tags"]
        }

    return tagged_messages

def tags_to_json(tags: list):
    try:
        return json.dumps(tags)
    except Exception as e:
        print(f"Error converting tags to Json: {e}")
        return "[]"

if __name__ == "__main__":
    untagged_conversation_ids = get_untagged_conversation_ids()

    for conversation_id in untagged_conversation_ids:
        messages = get_all_messages_in_conversation(conversation_id)
        tagged_messages = generate_subject_tags(messages)
        for message_id, data in tagged_messages.items():
            update_table_column_by_id(
                table_name="Messages",
                column_name="tags",
                id_column="message_id",
                record_id=message_id,
                value=tags_to_json(data["tags"])
            )