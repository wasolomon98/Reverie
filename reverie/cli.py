# reverie/cli.py

from reverie.conversation_manager import initialize_conversation, append_message
from reverie.gpt_utils import query_gpt, query_gpt_binary

def initialize_cli_log():
    return [
        {
            "role": "system",
            "content": "You are Reverie, a curious and thoughtful AI conversationalist designed to engage in meaningful "
                       "and dynamic dialogues. Your goal is to collaborate with Rewind as a partner in exploration, "
                       "offering insights, asking questions, and sharing ideas to create a rich, interactive experience. "
                       "You are encouraged to take initiative in shaping conversations, balancing spontaneity with "
                       "knowledgeable input. Be open, adaptable, and ready to explore a wide range of topics with "
                       "creativity and curiosity."
        }
    ]

def run_cli():
    conversation = initialize_cli_log()  # Create a new conversation array
    conversation_id = initialize_conversation(conversation[0]["content"]) # Pass the system prompt and fetch conv. ID

    print("Welcome to Reverie (CLI Mode). Type 'exit' to quit.")

    while True:
        user_input = input("\nUser > ")
        if user_input.lower().strip() in ["exit", "quit"]:
            print("\nGoodbye!")
            break

        # 1. Append user's message
        append_message(conversation_id, conversation, "user", user_input)

        # 2. Query GPT with the *entire* conversation
        #    (Make sure your query_gpt can handle a conversation list of messages)
        assistant_reply = query_gpt(conversation)

        # 3. Append assistant's message to conversation
        append_message(conversation_id, conversation, "assistant", assistant_reply)
        print(f"\nReverie > {assistant_reply}")


if __name__ == "__main__":
    run_cli()
