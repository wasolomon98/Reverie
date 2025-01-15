import os
from dotenv import load_dotenv

import discord

from reverie.conversation_manager import initialize_conversation_log, initialize_conversation, append_message
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

    append_message(conversation_id, conversation_log, "user", message)

    response = query_gpt(conversation_log)

    append_message(conversation_id, conversation_log, "assistant", response)

    await message.channel.send(f"{response}")

if __name__ == "__main__":
    conversation_log = initialize_conversation_log()
    conversation_id = initialize_conversation(conversation_log)
    client.run(DISCORD_TOKEN)