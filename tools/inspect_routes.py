from importlib import import_module
m = import_module('microservicios.logistica.app.main')
# stub seed_items if exists
if hasattr(m, 'seed_items'):
    m.seed_items = lambda: None
from fastapi.testclient import TestClient
c = TestClient(m.app)
print('health', c.get('/health').status_code)
print('routes:', [r.path for r in m.app.routes])
resp = c.post('/deliveries', json={'order_id':1,'delivery_address':'X'}, headers={'user-name':'a'})
print('post deliveries status', resp.status_code, 'body:', resp.text)
