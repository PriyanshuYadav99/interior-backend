import time
from services.external_clients import supabase

_CACHE, _TTL = {}, 300

def get_client_config(client_name):
    if not client_name:
        return None

    hit = _CACHE.get(client_name)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]

    rows = supabase.table('client_config').select('*') \
        .eq('client_name', client_name).eq('is_active', True).execute().data
    cfg = rows[0] if rows else None
    _CACHE[client_name] = (time.time(), cfg)
    return cfg