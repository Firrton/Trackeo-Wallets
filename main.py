import discord
from bot import handle_on_ready, handle_on_message

# Reemplaza esto con tu token directamente
TOKEN = "Token del bot"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    await handle_on_ready(client)

@client.event
async def on_message(message):
    await handle_on_message(message)

# Asegúrate de que el token no sea None
if TOKEN is None or TOKEN == "":
    raise ValueError("El token de Discord no está configurado. Asegúrate de que la variable TOKEN esté establecida correctamente.")

client.run(TOKEN)