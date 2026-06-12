import asyncio
import motor.motor_asyncio

MONGODB_URI = "mongodb://admin:vexasecure2024@localhost:27017/vexa?authSource=admin"
ASSETS_URL = "https://raw.githubusercontent.com/patmikaelson/Vexa-Bot/main/assets/"

CATEGORY_IMAGE_MAP = {
    "Music": ASSETS_URL + "8.png",
    "Ticket": ASSETS_URL + "4.png",
    "Game": ASSETS_URL + "8.png",
    "Giveaway": ASSETS_URL + "3.png",
    "Utility": ASSETS_URL + "8.png",
    "Security": ASSETS_URL + "8.png",
    "Economy": ASSETS_URL + "11.png",
    "Leveling": ASSETS_URL + "11.png",
    "Welcomer": ASSETS_URL + "11.png",
}

PRODUCTS = [
    {"product_id": "mod-bot-pro", "name": "🤖 ModBot Pro", "description": "Advanced moderation with auto-mod, logging, anti-raid.", "price": 29.99, "category": "Security", "gif_url": ""},
    {"product_id": "music-bot-premium", "name": "🎵 MusicBot Premium", "description": "High-quality music with Spotify, YouTube, SoundCloud.", "price": 19.99, "category": "Music", "gif_url": ""},
    {"product_id": "ticket-bot-enterprise", "name": "🎫 TicketBot Enterprise", "description": "Multi-category ticket system with priority and voice support.", "price": 24.99, "category": "Ticket", "gif_url": ""},
    {"product_id": "economy-bot-gold", "name": "💰 EconomyBot Gold", "description": "Full economy: currency, shops, gambling, leaderboards.", "price": 34.99, "category": "Game", "gif_url": ""},
    {"product_id": "giveaway-bot-ultimate", "name": "🎁 GiveawayBot Ultimate", "description": "Automated giveaways with winners, requirements, scheduling.", "price": 14.99, "category": "Giveaway", "gif_url": ""},
    {"product_id": "leveling-bot-max", "name": "📈 LevelingBot Max", "description": "XP tracking, role rewards, leaderboards, custom messages.", "price": 22.99, "category": "Utility", "gif_url": ""},
    {"product_id": "welcomer-bot-pro", "name": "👋 WelcomerBot Pro", "description": "Custom welcome messages, auto-roles, image generation.", "price": 17.99, "category": "Utility", "gif_url": ""},
    {"product_id": "utility-bot-complete", "name": "🔧 UtilityBot Complete", "description": "Polls, reminders, timers, embeds, server management.", "price": 27.99, "category": "Utility", "gif_url": ""},
]


async def seed():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    db = client["vexa"]
    existing = await db["products"].count_documents({})
    if existing > 0:
        print(f"Products collection already has {existing} docs. Skipping.")
        return
    for p in PRODUCTS:
        category = p.get("category", "Utility")
        doc = {
            "product_id": p["product_id"],
            "name": p["name"],
            "description": p["description"],
            "price": p["price"],
            "category": category,
            "image_url": CATEGORY_IMAGE_MAP.get(category, ASSETS_URL + "11.png"),
            "custom_image": "",
            "gif_url": p.get("gif_url", ""),
        }
        await db["products"].update_one({"product_id": p["product_id"]}, {"$setOnInsert": doc}, upsert=True)
    print(f"✅ Seeded {len(PRODUCTS)} products.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
