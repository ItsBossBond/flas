import os, requests
from typing import Dict

class EthGateway:
    def __init__(self):
        self.url = os.getenv('ETH_GATEWAY_URL')
        self.key = os.getenv('ETH_API_KEY')
    def tx_status(self, tx_id: str) -> Dict:
        if not self.url: raise RuntimeError('ETH_GATEWAY_URL not set')
        r = requests.post(self.url, json={'method':'tx_status','tx_id':tx_id,'api_key':self.key}, timeout=15)
        r.raise_for_status(); return r.json()

class TronGateway:
    def __init__(self):
        self.url = os.getenv('TRON_GATEWAY_URL')
        self.key = os.getenv('TRON_API_KEY')
    def tx_status(self, tx_id: str) -> Dict:
        if not self.url: raise RuntimeError('TRON_GATEWAY_URL not set')
        r = requests.post(self.url, json={'method':'tx_status','tx_id':tx_id,'api_key':self.key}, timeout=15)
        r.raise_for_status(); return r.json()
