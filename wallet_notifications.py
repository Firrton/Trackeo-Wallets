from solana.rpc.api import Client
from solana.publickey import PublicKey
import base58
import asyncio

# Conexión con la red de Solana
solana_client = Client("https://api.mainnet-beta.solana.com")  # Nodo RPC de Solana

# Diccionario para almacenar wallets a rastrear y sus nombres
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

async def rastrear_wallet(wallet_address, wallet_name, channel):
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
            tracked_wallets[wallet_address] = wallet_name
            wallet_balances[wallet_address] = solana_client.get_balance(public_key)['result']['value']
            await channel.send(f"✅ La wallet `{wallet_name}` ({wallet_address}) ha sido añadida al monitoreo.")
        else:
            await channel.send(f"⚠️ La wallet `{wallet_address}` ya está siendo monitoreada.")
    except Exception as e:
        await channel.send(f"❌ Error al intentar rastrear `{wallet_address}`: {e}")

async def monitor_wallet_transactions(channel):
    """
    Monitorea las transacciones de las wallets rastreadas y envía notificaciones al canal de Discord.
    """
    print("[Wallet Monitor] Iniciando monitoreo de transacciones...")
    last_seen_transactions = {}  # Para evitar notificaciones duplicadas

    while True:
        for wallet_address, wallet_name in tracked_wallets.items():
            try:
                public_key = PublicKey(wallet_address)
                # Obtiene las transacciones más recientes
                response = solana_client.get_signatures_for_address(public_key, limit=1)

                if "result" in response and response["result"]:
                    latest_tx = response["result"][0]
                    tx_signature = latest_tx["signature"]
                    slot = latest_tx["slot"]

                    # Revisa si la transacción ya fue notificada
                    if wallet_address not in last_seen_transactions or last_seen_transactions[wallet_address] != tx_signature:
                        last_seen_transactions[wallet_address] = tx_signature

                        # Obtiene los detalles de la transacción
                        tx_details = solana_client.get_confirmed_transaction(tx_signature)

                        if "result" in tx_details:
                            instructions = tx_details["result"]["transaction"]["message"]["instructions"]
                            token_transfers = []
                            detected_swap = False

                            for instruction in instructions:
                                program_id = instruction.get("programId", "")
                                data = instruction.get("data", "")
                                
                                # Detecta transferencias SPL
                                if program_id == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA" and data.startswith("C"):
                                    source = instruction["accounts"][0]
                                    destination = instruction["accounts"][1]
                                    mint = instruction["accounts"][2]
                                    token_name = f"Token ({mint})"  # Puedes mejorar esto con un mapa de tokens
                                    token_transfers.append((source, destination, token_name))
                                
                                # Detecta intercambios (Raydium/Serum)
                                if program_id == "9xQeWvG816bUx9EPm9MktF7n8BEF9cCbAEWyYo3Rdyk":  # ID de Serum como ejemplo
                                    detected_swap = True
                            
                            # Notificación para transferencias SPL normales
                            if token_transfers and not detected_swap:
                                message = f"🚨 **Nueva transacción detectada en la wallet {wallet_name} ({wallet_address}):**\n"
                                for transfer in token_transfers:
                                    source, destination, token_name = transfer
                                    message += (
                                        f"- **Token transferido:** {token_name}\n"
                                        f"- **De:** `{source}`\n"
                                        f"- **A:** `{destination}`\n"
                                    )
                                message += f"\nConsulta más detalles en: https://solscan.io/tx/{tx_signature}"
                                await channel.send(message)
                            
                            # Notificación para intercambios detectados
                            if detected_swap:
                                message = (
                                    f"🔄 **Intercambio detectado en la wallet {wallet_name} ({wallet_address}):**\n"
                                    f"- **Transacción:** `{tx_signature}`\n"
                                    f"- Consulta más detalles en: https://solscan.io/tx/{tx_signature}"
                                )
                                await channel.send(message)
            except Exception as e:
                print(f"[Wallet Monitor] Error monitoreando la wallet {wallet_address}: {e}")

        await asyncio.sleep(30)  # Espera 30 segundos antes de verificar nuevamente