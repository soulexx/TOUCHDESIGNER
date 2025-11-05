import re

# Das Regex aus dem Handler
RE_COUNT = re.compile(r'^/eos/out/get/(?P<typ>ip|fp|cp|bp)/count$')

# Test mit den tatsächlichen OSC-Adressen
test_addresses = [
    '/eos/out/get/ip/count',
    '/eos/out/get/fp/count',
    '/eos/out/get/cp/count',
    '/eos/out/get/bp/count',
]

print('Regex-Test:')
for addr in test_addresses:
    match = RE_COUNT.match(addr)
    if match:
        print(f'  ✅ {addr} -> {match.group("typ")}')
    else:
        print(f'  ❌ {addr} -> NO MATCH')
