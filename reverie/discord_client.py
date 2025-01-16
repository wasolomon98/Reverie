import os
from dotenv import load_dotenv

import discord

from reverie.conversation_utils import initialize_conversation_log, initialize_conversation, append_message
from reverie.db_utils import get_recent_messages
from reverie.gpt_utils import query_gpt

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

conversation_id = ""
conversation_log = []

@client.event
async def on_ready():

    print(f"Logged in as {client.user} and ready to respond!")

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    append_message(conversation_id, conversation_log, "user", message.content)

    response = query_gpt(conversation_log)
    print(f"{response}")

    append_message(conversation_id, conversation_log, "assistant", response)

    await message.channel.send(f"{response}")

if __name__ == "__main__":
    conversation_log = initialize_conversation_log()
    conversation_id = initialize_conversation(conversation_log)
    conversation_log.extend(get_recent_messages())

    client.run(DISCORD_TOKEN)