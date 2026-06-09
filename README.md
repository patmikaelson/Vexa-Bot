# Vexa — Discord Bot Shop & Security

A full-featured Discord bot with ticket system, wallet/payments, referral rewards, auto-moderation, anti-raid, live demos, and a Node.js payment microservice.

## Tech Stack

- **Python 3.11+** — `discord.py` 2.3+, `motor` (async MongoDB), `celery`, `redis.asyncio`
- **Node.js 18** — Express payment API (simulated or real ZarinPal/NowPayments)
- **Docker** — 6 services: `mongodb`, `redis`, `bot`, `celery-worker`, `celery-beat`, `payment-api`

## Quick Start

### 1. Clone & Configure

```bash
git clone <repo>
cd Vexa-Bot
cp .env.example .env
```

Edit `.env` with your values:

```
BOT_TOKEN=your_discord_bot_token
GUILD_ID=1513530008008654889
OWNER_ID=1013088817827295384
```

### 2. Upload Assets (Required)

In the [Discord Developer Portal](https://discord.com/developers/applications):

1. Go to **Rich Presence** → **Art Assets**.
2. Upload two images:
   - **Large Image** — name it exactly `5852430520841604823`, text "Vexa – Your Bot Business Partner"
   - **Small Image** — name it exactly `5852430520841604822`, text "Secure • Fast • Modern"
3. The large image should be the Vexa logo (512×512 PNG); the small image a shield/checkmark icon.

### 3. Ensure the Verified Role Exists

Create a role in your Discord server named `✦ VXM` (or any name) and note its ID. Set `VERIFIED_ROLE_ID` in `bot/config.py` **OR** ensure the role ID `1513662326450950215` exists in your server. The bot will fall back to looking up the role by name if the ID doesn't exist.

### 4. Run with Docker

```bash
docker-compose up -d --build
```

This starts all 6 services. The bot will:
- Auto-create all categories, channels, and roles
- Clean duplicates if they exist
- Seed static embeds (rules, announcement, pricing)
- Post the verify panel and ticket panel
- Begin Celery tasks (live demo every 30s, stats every 60s, etc.)

### 5. Run without Docker (Development)

**Requirements:** Python 3.11+, MongoDB 6+, Redis 7+, Node.js 18+

```bash
# Install Python deps
pip install -r bot/requirements.txt

# Install Node deps
cd payment-api && npm install && cd ..

# Start MongoDB & Redis (e.g., via Docker)
docker run -d -p 27017:27017 mongo:6
docker run -d -p 6379:6379 redis:7-alpine redis-server --requirepass vexaredis2024

# Seed products
python seed_products.py

# Start payment API
cd payment-api && node server.js &

# Start Celery (separate terminals)
celery -A bot.celery_app worker --loglevel=info --concurrency=4
celery -A bot.celery_app beat --loglevel=info

# Start bot
python -m bot.main
```

## Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/setup full` | Create missing channels/roles, clean duplicates | Owner |
| `/setup purge` | Delete all channels/roles, recreate from scratch | Owner |
| `/verify` | (Re)send the verification panel | Admin |
| `/wallet` | View balance, transaction history, deposit credits | Everyone |
| `/referral link` | Get your referral link + code | Everyone |
| `/referral leaderboard` | Show top 10 referrers | Everyone |
| `/buy <product_id>` | Purchase a bot (wallet or gateway) | Everyone |
| `/shop` | Browse available products | Everyone |
| `/reopen <ticket_id>` | Reopen an archived ticket | Admin |
| `/announce` | Post an announcement | Owner |
| `/sync` | Force sync slash commands | Owner |

## Features

### Auto-Setup (Idempotent)
On every startup, the bot checks all categories, channels, and roles. If duplicates are found (e.g., two `#verify` channels), extras are deleted. Missing items are created. Stored message IDs in MongoDB prevent duplicate embeds.

### Verification
- Button in `#✅・verify` assigns the verified role (ID `1513662326450950215` or `✦ VXM` by name)
- Sends a welcome DM with command overview
- Logs every verification to `#📊・admin-logs`

### Ticket System
- **Glassmorphic dropdown** in `#🎫・create-ticket` with 3 options (Buy/Support/Referral)
- Private `ticket-{user.id}` channel under `🎫 TICKETS` category
- Priority selector (Low/Medium/High), Close, Escalate, and Voice Request buttons
- Closing archives messages and moves channel to `📁 Archived Tickets`
- `/reopen` moves it back to active

### Wallet & Payments
- `/wallet` shows balance, referral code, recent transactions, and deposit buttons
- 3 deposit methods: Crypto, PayPal, Iranian Bank (all simulated — auto-success)
- Each opens a modal for amount entry; on submit, credits are added instantly
- Wallet can be used for `/buy` purchases

### Referral System
- Each user gets a unique code via `/referral link`
- Tracking via invite `?ref=CODE` parameter
- 10% of first purchase goes to referrer's wallet
- Leaderboard updated every 60s by Celery in `#🏆・referral-leaderboard`

### Live Demo & Stats
- Celery rotates a random product embed in `#🎬・live-demo` every 30s
- Live stats embed in `#📊・live-stats` updated every 60s
- Alerts when >3 tickets are stale (>5min unanswered)

### Security
- **Anti-raid**: >5 joins in 10s → lockdown (only `✦ VXM`+ can see channels) → auto-remove after 5min
- **Auto-mod**: Deletes invites, profanity, spam; logs to `#📊・admin-logs`; mutes spammers for 10min

### Payment Microservice
- Node.js Express API on port 3001
- Mock ZarinPal and NowPayments integrations
- Webhook support for real gateways
- Docker service connects via `http://payment-api:3001`

## Project Structure

```
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point, presence, on_ready
│   ├── config.py             # All constants, channel/role definitions
│   ├── models.py             # MongoDB models (EmbedTracker, GuildSettings, etc.)
│   ├── embeds.py             # All embed builders (0x5865F2, thumb, footer)
│   ├── utils.py              # ID generators, Redis, ch_name helper
│   ├── tasks.py              # Celery tasks (demo, stats, alerts, leaderboard)
│   ├── celery_app.py         # Celery config + beat schedule
│   ├── requirements.txt
│   ├── Dockerfile
│   └── cogs/
│       ├── setup.py          # Auto-setup, /setup, /announce
│       ├── verification.py   # Verify button, /verify
│       ├── tickets.py        # Dropdown + ticket management, /reopen
│       ├── shop.py           # /shop, /buy, /wallet with deposit modals
│       ├── referral.py       # /referral link & leaderboard
│       ├── stats.py          # Live stats embed refresh
│       └── security.py       # Anti-raid, auto-mod
├── payment-api/
│   ├── server.js             # Express payment API
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml        # 6 services
├── seed_products.py          # Seed DB with 8 products
├── .env.example
└── README.md
```

## Environment Variables

See `.env.example` for all variables. Key ones:

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Discord bot token |
| `GUILD_ID` | Server (guild) ID |
| `OWNER_ID` | Your Discord user ID |
| `MONGO_ROOT_USER` | MongoDB username |
| `MONGO_ROOT_PASS` | MongoDB password |
| `REDIS_PASSWORD` | Redis password |
| `ZARINPAL_MERCHANT_ID` | ZarinPal merchant ID (optional, for real payments) |
| `NOWPAYMENTS_API_KEY` | NowPayments API key (optional, for crypto) |

## License

MIT
