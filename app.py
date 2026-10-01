"""ShopKart: a tiny fake shop used to demo the Fixer incident agent."""
import collections
import json
import logging
import os
import time
import urllib.request

from flask import Flask, jsonify, render_template_string, request

# Optional: send crashes to Sentry too (set SENTRY_DSN to enable)
if os.getenv("SENTRY_DSN"):
    import sentry_sdk
    sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], traces_sample_rate=0.0)

app = Flask(__name__)
logging.basicConfig(
    filename="shopkart.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

VERSION = "v2.4.1"
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")  # your n8n webhook, optional

PRODUCTS = {
    "tea": {"name": "Masala chai, 250 g", "price": 180},
    "ghee": {"name": "Cow ghee, 500 ml", "price": 420},
    "rice": {"name": "Basmati rice, 5 kg", "price": 640},
    "dal": {"name": "Toor dal, 1 kg", "price": 165},
    "mango": {"name": "Alphonso mangoes, 6 pcs", "price": 590},
    "pickle": {"name": "Mixed pickle, 400 g", "price": 120},
}
COUPONS = {"SAVE10": 10, "FEST20": 20}

recent = collections.deque(maxlen=50)  # True = ok, False = failed
last_alert = 0.0


def apply_discount(total, coupon):
    # The next two lines are the safety check. break_it.py removes them
    # to simulate a bad commit, and Fixer should put them back by reverting.
    if not coupon:  # null check
        return total  # null check
    percent = COUPONS.get(coupon.upper(), 0)
    return round(total * (100 - percent) / 100, 2)


def error_rate():
    if not recent:
        return 0.0
    return round(100 * recent.count(False) / len(recent), 1)


def maybe_alert(error_text):
    """Send an alert to n8n when more than 30% of recent checkouts fail."""
    global last_alert
    if not N8N_WEBHOOK_URL or len(recent) < 10:
        return
    if error_rate() < 30 or time.time() - last_alert < 300:
        return
    last_alert = time.time()
    payload = {
        "service": "shopkart-checkout",
        "version": VERSION,
        "error_rate_percent": error_rate(),
        "sample_error": error_text,
        "endpoint": "/api/checkout",
        "fired_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    req = urllib.request.Request(
        N8N_WEBHOOK_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as exc:  # never let alerting break the shop
        logging.warning("could not reach n8n: %s", exc)


@app.post("/api/checkout")
def checkout():
    data = request.get_json(force=True)
    try:
        total = sum(PRODUCTS[i["id"]]["price"] * i["qty"] for i in data["items"])
        final = apply_discount(total, data.get("coupon"))
        recent.append(True)
        logging.info("checkout ok total=%s coupon=%s", final, data.get("coupon"))
        return jsonify(ok=True, total=final)
    except Exception as exc:
        recent.append(False)
        logging.exception("checkout failed in apply_discount: %s", exc)
        maybe_alert(repr(exc))
        return jsonify(ok=False, error="Checkout failed. Please try again."), 500


@app.get("/api/status")
def status():
    """n8n polls this after a fix to check that the shop has recovered."""
    rate = error_rate()
    return jsonify(
        version=VERSION,
        error_rate_percent=rate,
        healthy=rate < 5,
        requests_counted=len(recent),
    )


@app.post("/api/reset-stats")
def reset_stats():
    recent.clear()
    return jsonify(ok=True)


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ShopKart</title>
<style>
  :root { --bg:#f7f5ef; --ink:#1d2b26; --muted:#66736d; --line:#d9d6c9;
          --brand:#12594a; --ok:#12594a; --bad:#b3261e; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:16px/1.5 Georgia, 'Times New Roman', serif; }
  header { display:flex; justify-content:space-between; align-items:center;
           padding:18px 24px; border-bottom:1px solid var(--line); }
  header h1 { margin:0; font-size:22px; letter-spacing:.5px; }
  #pill { font:13px system-ui, sans-serif; padding:4px 10px; border-radius:99px;
          background:var(--ok); color:#fff; }
  #pill.bad { background:var(--bad); }
  main { display:grid; grid-template-columns:1fr 320px; gap:28px;
         max-width:980px; margin:24px auto; padding:0 20px; }
  @media (max-width:760px){ main { grid-template-columns:1fr; } }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); gap:14px; }
  .item { border:1px solid var(--line); padding:14px; background:#fff; }
  .item b { display:block; margin-bottom:4px; }
  .item span { color:var(--muted); font-family:system-ui,sans-serif; }
  button { font:15px system-ui,sans-serif; cursor:pointer; border:0;
           background:var(--brand); color:#fff; padding:8px 12px; margin-top:10px; }
  button:focus-visible, input:focus-visible { outline:3px solid #e0a100; outline-offset:2px; }
  aside { border:1px solid var(--line); background:#fff; padding:16px; align-self:start; }
  aside h2 { margin:0 0 10px; font-size:18px; }
  .row { display:flex; justify-content:space-between; font-family:system-ui,sans-serif;
         font-size:14px; padding:4px 0; }
  input { width:100%; padding:8px; margin-top:12px; font:15px system-ui,sans-serif;
          border:1px solid var(--line); }
  #msg { margin-top:12px; font:14px system-ui,sans-serif; min-height:20px; }
  #msg.bad { color:var(--bad); } #msg.ok { color:var(--ok); }
</style></head><body>
<header><h1>ShopKart</h1><span id="pill">Checkout working</span></header>
<main>
  <section><div class="grid" id="grid"></div></section>
  <aside>
    <h2>Your cart</h2>
    <div id="cart"><div class="row">Cart is empty. Add an item.</div></div>
    <input id="coupon" placeholder="Coupon code (try SAVE10)" aria-label="Coupon code">
    <button id="pay" style="width:100%">Pay now</button>
    <div id="msg" role="status"></div>
  </aside>
</main>
<script>
const PRODUCTS = {{ products|tojson }};
const cart = {};
const grid = document.getElementById('grid');
for (const [id, p] of Object.entries(PRODUCTS)) {
  const d = document.createElement('div'); d.className = 'item';
  d.innerHTML = `<b>${p.name}</b><span>Rs ${p.price}</span><br>
                 <button data-id="${id}">Add to cart</button>`;
  grid.appendChild(d);
}
grid.addEventListener('click', e => {
  const id = e.target.dataset.id; if (!id) return;
  cart[id] = (cart[id] || 0) + 1; render();
});
function render() {
  const el = document.getElementById('cart');
  const ids = Object.keys(cart);
  if (!ids.length) { el.innerHTML = '<div class="row">Cart is empty. Add an item.</div>'; return; }
  el.innerHTML = ids.map(id =>
    `<div class="row"><span>${PRODUCTS[id].name} x ${cart[id]}</span>
     <span>Rs ${PRODUCTS[id].price * cart[id]}</span></div>`).join('');
}
const pill = document.getElementById('pill'), msg = document.getElementById('msg');
document.getElementById('pay').onclick = async () => {
  const items = Object.keys(cart).map(id => ({ id, qty: cart[id] }));
  if (!items.length) { msg.className = 'bad'; msg.textContent = 'Add an item first.'; return; }
  const coupon = document.getElementById('coupon').value.trim() || null;
  const r = await fetch('/api/checkout', { method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items, coupon }) });
  const j = await r.json();
  msg.className = j.ok ? 'ok' : 'bad';
  msg.textContent = j.ok ? `Order placed. You paid Rs ${j.total}.` : j.error;
};
async function poll() {
  try {
    const s = await (await fetch('/api/status')).json();
    pill.textContent = s.healthy ? 'Checkout working' : `Checkout failing (${s.error_rate_percent}% errors)`;
    pill.className = s.healthy ? '' : 'bad';
  } catch (e) {}
}
setInterval(poll, 3000); poll();
</script></body></html>"""


@app.get("/")
def home():
    return render_template_string(PAGE, products=PRODUCTS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
