from solana.rpc.api import Client
from solana.publickey import PublicKey
import base58

# Conexión con la red de Solana
solana_client = Client("https://api.mainnet-beta.solana.com")  # Nodo RPC de Solana

# Lista para almacenar wallets a rastrear
tracked_wallets = {}
# Diccionario para almacenar balances anteriores de wallets
wallet_balances = {}

def es_direccion_valida(wallet_address):
    """
    Valida si una dirección de wallet es válida en la red Solana.
    """
    try:
        decoded = base58.b58decode(wallet_address)
        return len(decoded) == 32
    except ValueError:
        return False

async def rastrear_wallet(wallet_address, channel):
    """
    Valida y agrega una wallet al monitoreo.
    """
    try:
        # Validar que la dirección sea válida
        public_key = PublicKey(wallet_address)
        account_info = solana_client.get_account_info(public_key)

        if not account_info['result']['value']:
            await channel.send(f"⚠️ La dirección `{wallet_address}` no existe en la red Solana.")
            return

        # Verificar si es una cuenta de sistema (wallet)
        owner = account_info['result']['value']['owner']
        if owner != "11111111111111111111111111111111":
            await channel.send(f"⚠️ La dirección `{wallet_address}` no es una wallet válida, parece ser un token o programa.")
            return

        # Agregar al monitoreo si pasa la validación
        if wallet_address not in tracked_wallets:
            tracked_wallets[wallet_address] = True
            wallet_balances[wallet_address] = solana_client.get_balance(public_key)['result']['value']
            await channel.send(f"✅ La wallet `{wallet_address}` ha sido añadida al monitoreo.")
        else:
            await channel.send(f"⚠️ La wallet `{wallet_address}` ya está siendo monitoreada.")
    except Exception as e:
        await channel.send(f"❌ Error al intentar rastrear `{wallet_address}`: {e}")

async def obtener_balance_wallet(wallet_address, channel):
    """
    Obtiene el balance de una wallet y lo envía al canal.
    """
    try:
        # Verifica si la dirección es válida
        if not es_direccion_valida(wallet_address):
            await channel.send(f"La dirección `{wallet_address}` no es válida. Por favor, ingresa una wallet de Solana válida.")
            return

        # Convierte la dirección a un objeto PublicKey
        public_key = PublicKey(wallet_address)

        # Obtén el balance de la wallet
        response = solana_client.get_balance(public_key)

        if "result" in response and "value" in response["result"]:
            balance = response["result"]["value"] / 1e9  # Convierte lamports a SOL
            await channel.send(f"El balance de la wallet `{wallet_address}` es `{balance:.6f}` SOL.")
        else:
            error_msg = response.get("error", {}).get("message", "Error desconocido")
            await channel.send(f"No se pudo obtener el balance de la wallet: `{wallet_address}`. {error_msg}")
    except ValueError:
        await channel.send("Formato incorrecto. Usa `!balance_wallet <dirección_wallet>`")
    except Exception as e:
        await channel.send(f"Ocurrió un error al obtener el balance: {e}")

async def eliminar_wallet(wallet_address, channel):
    """
    Elimina una wallet del monitoreo.
    """
    try:
        if wallet_address in tracked_wallets:
            del tracked_wallets[wallet_address]
            del wallet_balances[wallet_address]
            await channel.send(f"Se eliminó la wallet {wallet_address} del rastreo.")
        else:
            await channel.send(f"La wallet {wallet_address} no está siendo rastreada.")
    except ValueError:
        await channel.send("Formato incorrecto. Usa `!eliminar_wallet <dirección_wallet>`")

async def snapshot_wallet(wallet_address, channel):
    """
    Toma un snapshot del balance de una wallet.
    """
    try:
        # Verifica si la dirección es válida
        if not es_direccion_valida(wallet_address):
            await channel.send(f"La dirección `{wallet_address}` no es válida. Por favor, ingresa una wallet de Solana válida.")
            return

        # Convierte la dirección a un objeto PublicKey
        public_key = PublicKey(wallet_address)

        # Obtén el balance de la wallet
        response = solana_client.get_balance(public_key)

        if "result" in response and "value" in response["result"]:
            balance = response["result"]["value"] / 1e9  # Convierte lamports a SOL
            wallet_balances[wallet_address] = response["result"]["value"]
            await channel.send(f"Snapshot tomado. El balance de la wallet `{wallet_address}` es `{balance:.6f}` SOL.")
        else:
            error_msg = response.get("error", {}).get("message", "Error desconocido")
            await channel.send(f"No se pudo obtener el balance de la wallet: `{wallet_address}`. {error_msg}")
    except ValueError:
        await channel.send("Formato incorrecto. Usa `!snapshot_wallet <dirección_wallet>`")
    except Exception as e:
        await channel.send(f"Ocurrió un error al tomar el snapshot: {e}")

async def obtener_transacciones_wallet(wallet_address, channel):
    """
    Obtiene las transacciones más recientes de una wallet y las envía al canal.
    """
    try:
        # Verifica si la dirección es válida
        if not es_direccion_valida(wallet_address):
            await channel.send(f"La dirección `{wallet_address}` no es válida. Por favor, ingresa una wallet de Solana válida.")
            return

        # Convierte la dirección a un objeto PublicKey
        public_key = PublicKey(wallet_address)

        # Obtén las transacciones más recientes
        response = solana_client.get_signatures_for_address(public_key, limit=10)

        if "result" in response:
            transactions = response["result"]
            if transactions:
                message_content = f"Transacciones recientes para la wallet `{wallet_address}`:\n"
                for tx in transactions:
                    tx_signature = tx["signature"]
                    slot = tx["slot"]
                    message_content += f"- Transacción: `{tx_signature}` en el slot `{slot}`\n"
                await channel.send(message_content)
            else:
                await channel.send(f"No se encontraron transacciones recientes para la wallet `{wallet_address}`.")
        else:
            error_msg = response.get("error", {}).get("message", "Error desconocido")
            await channel.send(f"No se pudieron obtener las transacciones de la wallet: `{wallet_address}`. {error_msg}")
    except ValueError:
        await channel.send("Formato incorrecto. Usa `!transacciones <dirección_wallet>`")
    except Exception as e:
        await channel.send(f"Ocurrió un error al obtener las transacciones: {e}")