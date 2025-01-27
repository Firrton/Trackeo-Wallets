import discord
import warnings
from wallet_utils import tracked_wallets, rastrear_wallet, obtener_balance_wallet, eliminar_wallet, snapshot_wallet, obtener_transacciones_wallet
from wallet_notifications import monitor_wallet_transactions

warnings.filterwarnings("ignore", category=DeprecationWarning)

async def handle_on_ready(client):
    """
    Evento que se ejecuta cuando el bot está listo.
    """
    print(f"Bot conectado como {client.user.name}")

    funciones = """
    ¡Hola! Estoy conectado y listo para ayudarte. Estas son mis funciones disponibles:
    
    - `hola`: Respondo con un saludo.
    - `!rastrear_wallet <dirección_wallet> <nombre_wallet>`: Rastrea una wallet de Solana.
    - `!listar_wallets`: Lista las wallets rastreadas.
    - `!balance_wallet <dirección_wallet>`: Consulta el balance de una wallet.
    - `!eliminar_wallet <dirección_wallet>`: Elimina una wallet del rastreo.
    - `!snapshot_wallet <dirección_wallet>`: Toma un snapshot del balance de una wallet.
    - `!transacciones <dirección_wallet>`: Consulta las transacciones recientes de una wallet.
    - `!desconectar`: Desconecta el bot.
    """

    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == "wallets-trackeadas":
                await channel.send(f"✅ ¡Estoy conectado como `{client.user.name}`! {funciones}")
                # Inicia la tarea de monitoreo de transacciones
                client.loop.create_task(monitor_wallet_transactions(channel))
                return

    print("No se encontró un canal llamado 'wallets-trackeadas'.")

async def handle_on_message(message):
    """
    Maneja los mensajes enviados en Discord.
    """
    # Ignorar mensajes del propio bot
    if message.author.bot:
        return

    # Responde al comando hola
    if message.content.startswith("hola"):
        await message.channel.send(f"Hola {message.author.name}, comencemos la investigación")

    # Comando para desconectar el bot
    elif message.content.startswith("!desconectar"):
        # Asegúrate de que solo los administradores puedan desconectar el bot
        if message.author.guild_permissions.administrator:
            await message.channel.send(f"🔌 Desconectando el bot por solicitud de {message.author.name}.")
            await message.client.close()  # Use the client to close the bot
        else:
            await message.channel.send("❌ No tienes permiso para desconectar el bot.")

    # Comando para rastrear una wallet
    elif message.content.startswith("!rastrear_wallet"):
        try:
            _, wallet_address, wallet_name = message.content.split(" ", 2)
            wallet_address = wallet_address.strip()
            wallet_name = wallet_name.strip()
            await rastrear_wallet(wallet_address, wallet_name, message.channel)
        except ValueError:
            await message.channel.send("Formato incorrecto. Usa `!rastrear_wallet <dirección_wallet> <nombre_wallet>`")

    # Comando para listar wallets rastreadas
    elif message.content.startswith("!listar_wallets"):
        if not tracked_wallets:
            await message.channel.send("No hay wallets rastreadas actualmente.")
        else:
            wallets = "\n".join([f"{name} ({address})" for address, name in tracked_wallets.items()])
            await message.channel.send(f"Estas son las wallets rastreadas:\n`{wallets}`")

    # Comando para consultar balance de una wallet
    elif message.content.startswith("!balance_wallet"):
        try:
            _, wallet_address = message.content.split(" ", 1)
            wallet_address = wallet_address.strip()
            await obtener_balance_wallet(wallet_address, message.channel)
        except ValueError:
            await message.channel.send("Formato incorrecto. Usa `!balance_wallet <dirección_wallet>`")

    # Comando para eliminar una wallet del monitoreo
    elif message.content.startswith("!eliminar_wallet"):
        try:
            _, wallet_address = message.content.split(" ", 1)
            wallet_address = wallet_address.strip()
            await eliminar_wallet(wallet_address, message.channel)
        except ValueError:
            await message.channel.send("Formato incorrecto. Usa `!eliminar_wallet <dirección_wallet>`")

    # Comando para tomar un snapshot del balance de una wallet
    elif message.content.startswith("!snapshot_wallet"):
        try:
            _, wallet_address = message.content.split(" ", 1)
            wallet_address = wallet_address.strip()
            await snapshot_wallet(wallet_address, message.channel)
        except ValueError:
            await message.channel.send("Formato incorrecto. Usa `!snapshot_wallet <dirección_wallet>`")

    # Comando para consultar transacciones recientes de una wallet
    elif message.content.startswith("!transacciones"):
        try:
            _, wallet_address = message.content.split(" ", 1)
            wallet_address = wallet_address.strip()
            await obtener_transacciones_wallet(wallet_address, message.channel)
        except ValueError:
            await message.channel.send("Formato incorrecto. Usa `!transacciones <dirección_wallet>`")