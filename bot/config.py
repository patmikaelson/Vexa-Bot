import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
GUILD_ID = int(os.getenv("GUILD_ID") or "0")
OWNER_ID = int(os.getenv("OWNER_ID") or "0")

CLIENT_ID = 1513531519787077632
APPLICATION_ID = 1513531519787077632
GUILD_ID_INT = 1513530008008654889

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:vexasecure2024@localhost:27017/vexa?authSource=admin")
DB_NAME = "vexa"
REDIS_URL = os.getenv("REDIS_URL", "redis://:vexaredis2024@localhost:6379/0")
PAYMENT_API_URL = os.getenv("PAYMENT_API_URL", "http://payment-api:3001")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

VERIFIED_ROLE_ID = 1513662326450950215

CATEGORIES = {
    "🔰 ──── 𝗪𝗘𝗟𝗖𝗢𝗠𝗘": [
        ("👋・welcome", "text", {}),
        ("📢・announcements", "text", {}),
        ("📌・rules", "text", {}),
    ],
    "🛡️ ──── 𝗦𝗘𝗖𝗨𝗥𝗜𝗧𝗬": [
        ("✅・verify", "text", {}),
        ("📊・admin-logs", "text", {"admin_only": True}),
    ],
    "🛒 ──── 𝗦𝗛𝗢𝗣": [
        ("🎬・live-demo", "text", {}),
        ("💰・pricing", "text", {"readonly": True}),
        ("🎫・create-ticket", "text", {}),
    ],
    "👥 ──── 𝗦𝗨𝗣𝗣𝗢𝗥𝗧": [
        ("💬・support-chat", "text", {}),
        ("🎧・voice-support", "voice", {}),
        ("🏆・referral-leaderboard", "text", {}),
    ],
    "📈 ──── 𝗦𝗧𝗔𝗧𝗦": [
        ("📊・live-stats", "text", {}),
        ("🔥・flash-sales", "text", {}),
    ],
    "🤖 ──── 𝗕𝗢𝗧 𝗖𝗢𝗡𝗧𝗥𝗢𝗟": [
        ("⚙️・bot-logs", "text", {"hidden": True}),
        ("🛠️・config", "text", {"hidden": True}),
    ],
}

CATEGORY_ORDER = list(CATEGORIES.keys())

ROLES = {
    "👑 Owner": {"color": 0x8B0000, "permissions": 8, "hoist": True, "mentionable": True},
    "🛡️ Admin": {"color": 0xFF8C00, "permissions": 0x38, "hoist": True, "mentionable": True},
    "🟢 Support": {"color": 0x00C853, "permissions": 0x140000, "hoist": True, "mentionable": True},
    "✦ VXM": {"color": 0x2196F3, "permissions": 0x400, "hoist": True, "mentionable": False},
    "⭐ Customer": {"color": 0xFFD700, "permissions": 0, "hoist": True, "mentionable": False},
    "🚫 Muted": {"color": 0x607D8B, "permissions": 0, "hoist": False, "mentionable": False},
}

TICKET_TYPES = {
    "buy": {"emoji": "🛒", "label": "Buy a Bot"},
    "support": {"emoji": "❓", "label": "Support"},
    "referral": {"emoji": "🤝", "label": "Referral Question"},
}

ASSETS_URL = "https://raw.githubusercontent.com/patmikaelson/Vexa-Bot/main/assets/"

CATEGORY_IMAGE_MAP = {
    "Music": ASSETS_URL + "category_music.png",
    "Ticket": ASSETS_URL + "category_ticket.png",
    "Game": ASSETS_URL + "category_game.png",
    "Utility": ASSETS_URL + "category_utility.png",
    "AI": ASSETS_URL + "category_utility.png",
    "FiveM": ASSETS_URL + "category_fivem.png",
    "Security": ASSETS_URL + "category_utility.png",
    "Giveaway": ASSETS_URL + "category_game.png",
}

PROFANITY_LIST = [
    r'\b(fuck|shit|ass|damn|bitch|cunt|dick|bastard|piss)\b',
    r'\b(فحش|کثافت|گوه|کون|کس|سگ|خر)\b',
]
