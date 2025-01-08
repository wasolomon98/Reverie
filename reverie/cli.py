# reverie/cli.py

from reverie.conversation_manager import load_conversation, save_conversation, append_message
from reverie.gpt_utils import query_gpt

def run_cli():
    conversation = load_conversation()  # Load existing conversation (if any)
    print("Welcome to Reverie (CLI Mode). Type 'exit' to quit.")

    while True:
        user_input = input("\nUser > ")
        if user_input.lower().strip() in ["exit", "quit"]:
            print("Goodbye!")
            break

        # 1. Append user's message
        append_message(conversation, "user", user_input)

        # 2. Query GPT with the *entire* conversation
        #    (Make sure your query_gpt can handle a conversation list of messages)
        assistant_reply = query_gpt(conversation)

        # 3. Append assistant's message to conversation
        append_message(conversation, "assistant", assistant_reply)
        print(f"Reverie > {assistant_reply}")

        # 4. Save updated log
        save_conversation(conversation)

if __name__ == "__main__":
    run_cli()
