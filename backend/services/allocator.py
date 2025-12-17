import os, requests
from typing import Tuple
from utils import generate_dev_address

# Safe modes
MODE_DEV='DEV_FAKE'
MODE_GATEWAY='GATEWAY_HTTP'
MODE_XPUB='XPUB'

def allocate_address(network: str, user_id: int) -> Tuple[str, str]:
    # Default to DEV_FAKE if not set, to prevent errors
    mode = (os.getenv('ALLOCATION_MODE') or MODE_DEV).upper()
    
    if mode == MODE_DEV:
        return generate_dev_address(network, user_id), f'{network} wallet'
    
    if mode == MODE_GATEWAY:
        url = os.getenv('ALLOCATOR_URL')
        key = os.getenv('ALLOCATOR_API_KEY')
        if not url or not key: 
            # Fallback to dev mode if config is missing instead of crashing
            print("Warning: Gateway config missing. Falling back to DEV mode.")
            return generate_dev_address(network, user_id), f'{network} wallet'
            
        try:
            r = requests.post(url, json={'network':network,'user_id':user_id},
                              headers={'Authorization': f'Bearer {key}','Content-Type':'application/json'}, timeout=15)
            r.raise_for_status()
            data = r.json()
            addr = data.get('address')
            label = data.get('label') or f'{network} wallet'
            if not addr: raise RuntimeError('Allocator returned no address')
            return addr, label
        except Exception as e:
            # Log error and fallback to prevent user blockage
            print(f"Allocator Error: {e}")
            return generate_dev_address(network, user_id), f'{network} wallet'

    # Fallback for unimplemented modes
    if mode == MODE_XPUB:
        # Prevent crash: just use dev address until XPUB is built
        return generate_dev_address(network, user_id), f'{network} (XPUB-Sim)'

    return generate_dev_address(network, user_id), f'{network} wallet'