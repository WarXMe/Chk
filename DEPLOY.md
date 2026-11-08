# XBOX CHECKER BOT — DEPLOY GUIDE
## MADE BY @NUTFRR

---

## RENDER DEPLOY (5 min)

### 1. Push to GitHub
```
git init
git add .
git commit -m "xbox checker bot"
git remote add origin https://github.com/YOUR/REPO.git
git push -u origin main
```

### 2. Create Render Web Service
- Go to https://render.com
- New → Web Service → Connect your GitHub repo
- Render will auto-detect the `render.yaml`

### 3. Set Environment Variables (in Render dashboard)
| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Your bot token from @BotFather |
| `ADMIN_ID` | Your Telegram user ID (get from @userinfobot) |
| `WEBHOOK_URL` | `https://YOUR-APP-NAME.onrender.com` |
| `WEBAPP_URL` | Same as WEBHOOK_URL — serves the Telegram Mini App |

### 4. Persistent Disk
- Render.yaml already configures a 1GB disk at `/data`
- SQLite database lives there — survives redeploys

### 5. Done
Bot goes live. Set webhook by visiting:
```
https://api.telegram.org/botYOUR_TOKEN/setWebhook?url=https://YOUR-APP.onrender.com/webhook/SECRET
```
(The bot sets this automatically on startup via run_webhook)

---

## LOCAL DEV (no WEBHOOK_URL set = polling mode)

```bash
pip install -r requirements.txt
export BOT_TOKEN=your_token
export ADMIN_ID=your_telegram_id
export DB_PATH=./dev.db
python main.py
```

---

## ADMIN COMMANDS

| Command | Description |
|---------|-------------|
| `/gencode 1 30` | Generate 1-use 30-day code |
| `/gencode 5 90` | Generate 5-use 90-day code |
| `/revoke CODE` | Revoke a code |
| `/addpremium USER_ID 30` | Add premium directly |
| `/ban USER_ID` | Ban a user |
| `/unban USER_ID` | Unban a user |
| `/broadcast message` | Message all users |

Or use the **Admin Panel** button in the bot.

---

## PLAN RECOMMENDATION (Render $50 budget)

| Plan | Cost | RAM | CPU | Good for |
|------|------|-----|-----|---------|
| Starter | $7/mo | 512MB | 0.5 | Up to ~100 users |
| Standard | $25/mo | 2GB | 1 | Up to ~1000 users, faster checking |

Starter plan works fine. Upgrade to Standard if you want 40+ threads reliably.

---

## FILE STRUCTURE

```
xboxchkr/
├── main.py               — entry point (aiohttp + TG bot, single port)
├── requirements.txt
├── Dockerfile
├── render.yaml
├── bot/
│   ├── handlers.py       — all telegram handlers + webapp button
│   ├── keyboards.py      — inline keyboards
│   └── messages.py       — message templates
├── checker/
│   └── xbox_checker.py   — Xbox OAuth2 checker core
├── db/
│   └── database.py       — SQLite database layer
└── webapp/
    ├── index.html        — Telegram Mini App (glassmorphism dashboard)
    └── api_server.py     — aiohttp API: /api/session/<id>, /api/user/<uid>
```

## TELEGRAM MINI APP FLOW

1. User sends combos (.txt or pasted) to the bot
2. Bot replies: **"✅ N combos loaded!"** + preview + **"🖥️ Open Live Dashboard"** button
3. User taps button → full-screen glassmorphism webapp opens inside Telegram
4. Webapp polls `/api/session/<id>` every 1.2s — live counters + scrolling log
5. Each hit also arrives as a Telegram message card for instant notification
6. When done: results screen with hit cards + Download button (bot sends the file)

---

**Credits: @NUTFRR**
