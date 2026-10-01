# ShopKart: the fake shop for the Fixer demo

A tiny online shop that you can break on purpose.

## 1. Run it (5 minutes)

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000. Add an item, click **Pay now**. It works.

## 2. Put it on GitHub (Fixer needs a repo to revert)

```bash
git init
git add .
git commit -m "ShopKart v2.4.1"
git branch -M main
git remote add origin https://github.com/YOUR-NAME/shopkart.git
git push -u origin main
```

## 3. Create fake customers

In a second terminal:

```bash
python traffic.py
```

Keep it running. It sends about 2 orders per second, so there is always traffic.

## 4. Connect the alert to n8n

1. In n8n, add a **Webhook** node (POST). Copy its **Production URL**.
2. Start the shop with that URL:

   Mac/Linux: `N8N_WEBHOOK_URL="https://your-n8n/webhook/fixer" python app.py`

   Windows PowerShell: `$env:N8N_WEBHOOK_URL="https://your-n8n/webhook/fixer"; python app.py`

When more than 30% of recent checkouts fail, the shop sends n8n a message like:

```json
{"service": "shopkart-checkout", "error_rate_percent": 61.0,
 "sample_error": "AttributeError(...)", "endpoint": "/api/checkout"}
```

That is the trigger for your Fixer workflow. If you prefer Sentry, set `SENTRY_DSN` instead.

## 5. Break it (the demo moment)

```bash
python break_it.py
```

This removes the null check in `apply_discount()`, commits it as "refactor discount calc", and pushes. Restart `app.py` so the broken code runs. Customers who use no coupon now get errors, and the page badge turns red.

## 6. What Fixer should do

1. Get the alert from the webhook.
2. Read the recent commits from GitHub and see "refactor discount calc" removed a check.
3. Decide with the AI node, then revert the commit.
4. Restart the app and poll `GET /api/status` until `"healthy": true`.
5. Write the post-mortem and save it to memory.

## Useful endpoints

| URL | What it gives you |
|---|---|
| `GET /api/status` | error rate and health, for n8n to verify the fix |
| `POST /api/checkout` | the order endpoint (this is what breaks) |
| `POST /api/reset-stats` | clears the error counter between demo runs |
| `shopkart.log` | log file with the stack trace, for the "logs" clue |

## Demo tips

- Run `curl -X POST localhost:5000/api/reset-stats` before each rehearsal.
- Record a backup video of one clean run.
- Keep the shop page on screen so judges see the red badge turn green.
