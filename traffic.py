"""Pretend to be customers so the shop has traffic during the demo.

Run:  python traffic.py            (about 2 orders per second)
      python traffic.py --rps 5
"""
import argparse
import random
import time

import requests

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://localhost:5000")
parser.add_argument("--rps", type=float, default=2)
args = parser.parse_args()

ITEMS = ["tea", "ghee", "rice", "dal", "mango", "pickle"]
COUPONS = [None, None, None, "SAVE10", "FEST20"]  # most people use no coupon

print(f"Sending about {args.rps} orders/second to {args.url}. Ctrl+C to stop.")
ok = failed = 0
while True:
    body = {
        "items": [{"id": random.choice(ITEMS), "qty": random.randint(1, 3)}],
        "coupon": random.choice(COUPONS),
    }
    try:
        r = requests.post(f"{args.url}/api/checkout", json=body, timeout=5)
        if r.ok:
            ok += 1
        else:
            failed += 1
    except requests.RequestException:
        failed += 1
    print(f"\rok={ok}  failed={failed}", end="", flush=True)
    time.sleep(1 / args.rps)
