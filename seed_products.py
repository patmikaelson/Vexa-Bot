import asyncio
import motor.motor_asyncio

MONGODB_URI = "mongodb://admin:vexasecure2024@localhost:27017/vexa?authSource=admin"

PRODUCTS = [
    {"product_id": "mod-bot-pro", "name": "🤖 ModBot Pro", "description": "Advanced moderation with auto-mod, logging, anti-raid.", "price": 29.99, "image_url": "https://i.imgur.com/6wX9F6p.png", "gif_url": "https://i.imgur.com/6wX9F6p.png"},
    {"product_id": "music-bot-premium", "name": "🎵 MusicBot Premium", "description": "High-quality music with Spotify, YouTube, SoundCloud.", "price": 19.99, "image_url": "https://i.imgur.com/6wX9F6p.png", "gif_url": "https://i.imgur.com/6wX9F6p.png"},
    {"product_id": "ticket-bot-enterprise", "name": "🎫 TicketBot Enterprise", "description": "Multi-category ticket system with priority and voice support.", "price": 24.99, "image_url": "https://i.imgur.com/6wX9F6p.png", "gif_url": "https://i.imgur.com/6wX9F6p.png"},
    {"product_id": "economy-bot-gold", "name": "💰 EconomyBot Gold", "description": "Full economy: currency, shops, gambling, leaderboards.", "price": 34.99, "image_url": "https://i.imgur.com/6wX9F6p.png", "gif_url": "https://i.imgur.com/6wX9F6p.png"},
    {"product_id": "giveaway-bot-ultimate", "name": "🎁 GiveawayBot Ultimate", "description": "Automated giveaways with winners, requirements, scheduling.", "price": 14.99, "image_url": "https://i.imgur.com/6wX9F6p.png", "gif_url": "https://i.imgur.com/6wX9F6p.png"},
    {"product_id": "leveling-bot-max", "name": "📈 LevelingBot Max", "description": "XP tracking, role rewards, leaderboards, custom messages.", "price": 22.99, "image_url": "https://i.imgur.com/6wX9F6p.png", "gif_url": "https://i.imgur.com/6wX9F6p.png"},
    {"product_id": "welcomer-bot-pro", "name": "👋 WelcomerBot Pro", "description": "Custom welcome messages, auto-roles, image generation.", "price": 17.99, "image_url": "https://i.imgur.com/6wX9F6p.png", "gif_url": "https://i.imgur.com/6wX9F6p.png"},
    {"product_id": "utility-bot-complete", "name": "🔧 UtilityBot Complete", "description": "Polls, reminders, timers, embeds, server management.", "price": 27.99, "image_url": "https://i.imgur.com/6wX9F6p.png", "gif_url": "https://i.imgur.com/6wX9F6p.png"},
]


async def seed():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    db = client["vexa"]
    existing = await db["products"].count_documents({})
    if existing > 0:
        print(f"Products collection already has {existing} docs. Skipping.")
        return
    for p in PRODUCTS:
        await db["products"].update_one({"product_id": p["product_id"]}, {"$setOnInsert": p}, upsert=True)
    print(f"✅ Seeded {len(PRODUCTS)} products.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
