import motor.motor_asyncio
from datetime import datetime, timezone, timedelta

from bot.config import MONGODB_URI, DB_NAME

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

users_col = db["users"]
tickets_col = db["tickets"]
products_col = db["products"]
transactions_col = db["transactions"]
referrals_col = db["referrals"]
invite_refs_col = db["invite_refs"]
embeds_col = db["embeds"]
guild_settings_col = db["guild_settings"]
wallet_deposits_col = db["wallet_deposits"]


FIFTY_PRODUCTS = [
    {"name": "Auralux", "description": "High-quality music playback from YouTube, Spotify, SoundCloud with live equalizer and sound effects.", "price_tomans": 1500000, "category": "Music"},
    {"name": "Nightwave", "description": "24/7 radio with virtual DJ, song requests, and community voting for next track.", "price_tomans": 2000000, "category": "Music"},
    {"name": "BassDrop", "description": "Music player with bass boost, nightcore, 8D, and slow-motion audio filters.", "price_tomans": 1800000, "category": "Music"},
    {"name": "Playlist Pro", "description": "Save and manage playlists, auto-suggest songs based on server's favourite genres.", "price_tomans": 1200000, "category": "Music"},
    {"name": "Karaoke King", "description": "Sing-along with real-time lyrics sync, karaoke scoring, and leaderboard.", "price_tomans": 2200000, "category": "Music"},
    {"name": "TicketFusion", "description": "Dynamic ticket forms, file uploads, auto-prioritisation, escalation to technical team.", "price_tomans": 2500000, "category": "Ticket"},
    {"name": "SupportFlow", "description": "Ticket system with SLA (guaranteed response time), reminders, weekly reports.", "price_tomans": 2000000, "category": "Ticket"},
    {"name": "VoiceTicket", "description": "Voice-based tickets: users explain issues via voice message, bot transcribes and sends to admins.", "price_tomans": 3000000, "category": "Ticket"},
    {"name": "AutoClose", "description": "Auto-detect unanswered tickets, close after 24h, and archive automatically.", "price_tomans": 1500000, "category": "Ticket"},
    {"name": "MultiDept", "description": "Separate departments (Sales, Support, Tech, Billing) with smart routing.", "price_tomans": 2800000, "category": "Ticket"},
    {"name": "LuxWelcome", "description": "Animated welcome embeds, custom GIFs, clickable rules, auto-role assignment.", "price_tomans": 1000000, "category": "Giveaway"},
    {"name": "GiveawayX", "description": "Advanced giveaways: multiple winners, role/join requirements, delayed draw.", "price_tomans": 1200000, "category": "Giveaway"},
    {"name": "LevelUpGreet", "description": "Level-based welcoming: temporary role for new members, permanent after 10 messages.", "price_tomans": 1500000, "category": "Giveaway"},
    {"name": "RaffleMaster", "description": "Live raffles with animation, ticket purchase using in-app coins.", "price_tomans": 2000000, "category": "Giveaway"},
    {"name": "BirthdayWisher", "description": "Auto birthday wishes (users set date), custom GIFs and role.", "price_tomans": 800000, "category": "Giveaway"},
    {"name": "AntiNuke Pro", "description": "Instant lockdown on suspicious activity (mass role/channel deletion), raid protection.", "price_tomans": 3000000, "category": "Security"},
    {"name": "ShieldX", "description": "Smart link filtering (spam, phishing, NSFW) with trainable AI.", "price_tomans": 2500000, "category": "Security"},
    {"name": "PhishBlocker", "description": "Real-time malicious link database, auto-delete and report.", "price_tomans": 2000000, "category": "Security"},
    {"name": "TimeoutBot", "description": "Progressive timeout system: 5m, 1h, 1d based on repeat offences.", "price_tomans": 1200000, "category": "Security"},
    {"name": "LogSpecter", "description": "Complete event logging (message edits/deletions, role changes, join/leave) with search.", "price_tomans": 1800000, "category": "Security"},
    {"name": "TriviaMania", "description": "Daily trivia contests, leaderboard, coin rewards.", "price_tomans": 1000000, "category": "Game"},
    {"name": "DiceRoller", "description": "Dice and simple casino games (bet with virtual coins).", "price_tomans": 800000, "category": "Game"},
    {"name": "EconomyFarm", "description": "Full farming economy: plant, harvest, steal, sell, billionaire ranking.", "price_tomans": 2200000, "category": "Game"},
    {"name": "CountTo100", "description": "Collaborative counting game, mistake = 10s mute.", "price_tomans": 500000, "category": "Game"},
    {"name": "MemeWar", "description": "Meme competition: users upload memes, community votes with emojis.", "price_tomans": 1500000, "category": "Game"},
    {"name": "PokéDex", "description": "Catch virtual Pokémon in random channels, complete the Pokédex.", "price_tomans": 2500000, "category": "Game"},
    {"name": "RockPaperScissor", "description": "Rock-paper-scissors against bot, ELO ranking.", "price_tomans": 600000, "category": "Game"},
    {"name": "Werewolf", "description": "Complete werewolf game: roles, night phases, voting, voice channel support.", "price_tomans": 3500000, "category": "Game"},
    {"name": "Arena Duel", "description": "Text-based duels with weapons, skills, XP and leveling.", "price_tomans": 2000000, "category": "Game"},
    {"name": "Snake Game", "description": "Classic snake game inside chat with arrow buttons.", "price_tomans": 1200000, "category": "Game"},
    {"name": "ReminderX", "description": "Advanced reminders with recurrence (daily, weekly, monthly) and timezone support.", "price_tomans": 800000, "category": "Utility"},
    {"name": "PollMaster", "description": "Multi-option polls, anonymous voting, expiry dates, bar chart output.", "price_tomans": 700000, "category": "Utility"},
    {"name": "LinkKeeper", "description": "Save important links in a hidden channel with categories and search.", "price_tomans": 600000, "category": "Utility"},
    {"name": "TempVoice", "description": "Temporary voice channels: users create a voice channel, auto-deleted when empty.", "price_tomans": 1000000, "category": "Utility"},
    {"name": "AutoTranslate", "description": "Automatic message translation to server's preferred language (Google Translate API).", "price_tomans": 2000000, "category": "Utility"},
    {"name": "ServerStats", "description": "Display server statistics as text-based bar charts.", "price_tomans": 900000, "category": "Utility"},
    {"name": "QOTD", "description": "Question of the Day, users submit answers, best answer of the week.", "price_tomans": 700000, "category": "Utility"},
    {"name": "TodoList", "description": "Personal to-do lists with priorities and due dates.", "price_tomans": 1000000, "category": "Utility"},
    {"name": "Calculator", "description": "Scientific calculator (trigonometry, logarithms) inside Discord.", "price_tomans": 500000, "category": "Utility"},
    {"name": "WebhookSender", "description": "Auto-send messages to external webhooks (announcements across servers).", "price_tomans": 1200000, "category": "Utility"},
    {"name": "ChatGPT Bridge", "description": "Chat with GPT-4, conversation memory per user.", "price_tomans": 4000000, "category": "AI"},
    {"name": "ImageGenius", "description": "Generate images using DALL-E / Midjourney style prompts.", "price_tomans": 3500000, "category": "AI"},
    {"name": "AI Mod", "description": "AI-based profanity and inappropriate content detection (not just keywords).", "price_tomans": 5000000, "category": "AI"},
    {"name": "Summarizer", "description": "Auto-summarise a channel (last 100 messages) using AI.", "price_tomans": 2800000, "category": "AI"},
    {"name": "Sentiment", "description": "Analyse message sentiment (happy, sad, angry) and report to admins.", "price_tomans": 2000000, "category": "AI"},
    {"name": "FiveM Status", "description": "Show FiveM server status (players, ping, map).", "price_tomans": 1500000, "category": "FiveM"},
    {"name": "Whitelist Manager", "description": "FiveM whitelist application form, admin approval system.", "price_tomans": 2000000, "category": "FiveM"},
    {"name": "RP Helper", "description": "Roleplay tools: damage calculator, dice rolls, digital ID.", "price_tomans": 2500000, "category": "FiveM"},
    {"name": "Live Squad", "description": "Real-time Squad team composition shown in voice channel.", "price_tomans": 1000000, "category": "FiveM"},
    {"name": "Game Server Logs", "description": "Receive and display game server logs (Minecraft, Rust, etc.) in a Discord channel.", "price_tomans": 1800000, "category": "FiveM"},
]


class EmbedTracker:
    @staticmethod
    async def get(channel_key: str) -> int | None:
        doc = await embeds_col.find_one({"_id": channel_key})
        return doc["message_id"] if doc else None

    @staticmethod
    async def set(channel_key: str, message_id: int):
        await embeds_col.update_one(
            {"_id": channel_key},
            {"$set": {"message_id": message_id}},
            upsert=True
        )

    @staticmethod
    async def delete(channel_key: str):
        await embeds_col.delete_one({"_id": channel_key})


class GuildSettings:
    @staticmethod
    async def get(key: str):
        doc = await guild_settings_col.find_one({"_id": "guild"})
        return doc.get(key) if doc else None

    @staticmethod
    async def set(key: str, value):
        await guild_settings_col.update_one(
            {"_id": "guild"},
            {"$set": {key: value}},
            upsert=True
        )

    @staticmethod
    async def get_all():
        return await guild_settings_col.find_one({"_id": "guild"}) or {}

    @staticmethod
    async def delete(key: str):
        await guild_settings_col.update_one(
            {"_id": "guild"},
            {"$unset": {key: ""}}
        )


class UserModel:
    @staticmethod
    async def get(user_id: int):
        return await users_col.find_one({"user_id": user_id})

    @staticmethod
    async def upsert(user_id: int, name: str):
        await users_col.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {
                "user_id": user_id, "name": name, "verified": False,
                "wallet_balance": 0.0, "referral_code": None,
                "referred_by": None, "customer": False,
                "created_at": datetime.now(timezone.utc),
            }},
            upsert=True
        )

    @staticmethod
    async def set_verified(user_id: int):
        await users_col.update_one({"user_id": user_id}, {"$set": {"verified": True}})

    @staticmethod
    async def update(user_id: int, **kwargs):
        await users_col.update_one({"user_id": user_id}, {"$set": kwargs})

    @staticmethod
    async def add_wallet(user_id: int, amount: float):
        await users_col.update_one({"user_id": user_id}, {"$inc": {"wallet_balance": amount}})

    @staticmethod
    async def deduct_wallet(user_id: int, amount: float) -> bool:
        r = await users_col.update_one(
            {"user_id": user_id, "wallet_balance": {"$gte": amount}},
            {"$inc": {"wallet_balance": -amount}}
        )
        return r.modified_count > 0

    @staticmethod
    async def get_transactions(user_id: int, limit: int = 5):
        return await transactions_col.find({"user_id": user_id})\
            .sort("created_at", -1).to_list(length=limit)


class TicketModel:
    @staticmethod
    async def create(ticket_id: str, user_id: int, ticket_type: str,
                     channel_id: int, priority: str = "medium"):
        doc = {
            "ticket_id": ticket_id, "user_id": user_id, "type": ticket_type,
            "channel_id": channel_id, "voice_channel_id": None,
            "priority": priority, "status": "open", "messages": [],
            "created_at": datetime.now(timezone.utc),
            "last_response_at": datetime.now(timezone.utc), "closed_at": None,
            "archived": False,
        }
        await tickets_col.insert_one(doc)
        return doc

    @staticmethod
    async def get(ticket_id: str):
        return await tickets_col.find_one({"ticket_id": ticket_id})

    @staticmethod
    async def get_by_channel(channel_id: int):
        return await tickets_col.find_one({"channel_id": channel_id})

    @staticmethod
    async def get_by_user(user_id: int):
        return await tickets_col.find_one({"user_id": user_id, "status": "open"})

    @staticmethod
    async def update(ticket_id: str, **kwargs):
        await tickets_col.update_one({"ticket_id": ticket_id}, {"$set": kwargs})

    @staticmethod
    async def close(ticket_id: str):
        await tickets_col.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status": "closed", "closed_at": datetime.now(timezone.utc)}}
        )

    @staticmethod
    async def reopen(ticket_id: str):
        await tickets_col.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status": "open", "closed_at": None}}
        )

    @staticmethod
    async def set_voice_channel(ticket_id: str, vc_id: int):
        await tickets_col.update_one(
            {"ticket_id": ticket_id}, {"$set": {"voice_channel_id": vc_id}}
        )

    @staticmethod
    async def count_open():
        return await tickets_col.count_documents({"status": "open"})

    @staticmethod
    async def count_stale(minutes: int = 5):
        threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return await tickets_col.count_documents({
            "status": "open", "last_response_at": {"$lt": threshold}
        })

    @staticmethod
    async def archive_messages(ticket_id: str, channel, limit=500):
        msgs = []
        async for m in channel.history(limit=limit, oldest_first=True):
            msgs.append({
                "author": str(m.author), "author_id": m.author.id,
                "content": m.content, "timestamp": m.created_at.isoformat(),
            })
        await tickets_col.update_one(
            {"ticket_id": ticket_id}, {"$set": {"archived_messages": msgs}}
        )


class ProductModel:
    @staticmethod
    async def get_all():
        return await products_col.find({"is_active": True}).to_list(length=100)

    @staticmethod
    async def get(product_id: str):
        return await products_col.find_one({"product_id": product_id})

    @staticmethod
    async def get_by_name(name: str):
        return await products_col.find_one({"name": name})

    @staticmethod
    async def random():
        docs = await products_col.aggregate([{"$match": {"is_active": True}}, {"$sample": {"size": 1}}]).to_list(length=1)
        return docs[0] if docs else None

    @staticmethod
    async def count_active():
        return await products_col.count_documents({"is_active": True})

    @staticmethod
    async def create(name: str, description: str, price_tomans: int, category: str, image_url: str = ""):
        doc = {
            "name": name,
            "description": description,
            "price_tomans": price_tomans,
            "category": category,
            "image_url": image_url,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        await products_col.insert_one(doc)
        return doc

    @staticmethod
    async def seed_50():
        existing_count = await products_col.count_documents({})
        if existing_count >= 50:
            return existing_count
        count = 0
        for p in FIFTY_PRODUCTS:
            exists = await products_col.find_one({"name": p["name"]})
            if not exists:
                doc = {
                    "name": p["name"],
                    "description": p["description"],
                    "price_tomans": p["price_tomans"],
                    "category": p["category"],
                    "image_url": "",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc),
                }
                await products_col.insert_one(doc)
                count += 1
        return count


class TransactionModel:
    @staticmethod
    async def create(tx_id: str, user_id: int, product_id: str, amount: float,
                     currency: str, gateway: str, tx_type: str = "purchase"):
        doc = {
            "tx_id": tx_id, "user_id": user_id, "product_id": product_id,
            "amount": amount, "currency": currency, "gateway": gateway,
            "status": "pending", "type": tx_type,
            "referrer_id": None, "referral_bonus": 0.0,
            "created_at": datetime.now(timezone.utc), "completed_at": None,
        }
        await transactions_col.insert_one(doc)

    @staticmethod
    async def complete(tx_id: str):
        await transactions_col.update_one(
            {"tx_id": tx_id},
            {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc)}}
        )

    @staticmethod
    async def get(tx_id: str):
        return await transactions_col.find_one({"tx_id": tx_id})

    @staticmethod
    async def by_user(user_id: int, limit: int = 5):
        return await transactions_col.find({"user_id": user_id})\
            .sort("created_at", -1).to_list(length=limit)

    @staticmethod
    async def count_today():
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return await transactions_col.count_documents({
            "status": "completed", "completed_at": {"$gte": start}
        })

    @staticmethod
    async def sum_week():
        start = datetime.now(timezone.utc) - timedelta(days=7)
        pipeline = [
            {"$match": {"status": "completed", "completed_at": {"$gte": start}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        r = await transactions_col.aggregate(pipeline).to_list(length=1)
        return r[0]["total"] if r else 0.0


class ReferralModel:
    @staticmethod
    async def create(referrer_id: int, referred_id: int, code: str):
        await referrals_col.insert_one({
            "referrer_id": referrer_id, "referred_id": referred_id, "code": code,
            "purchases": 0, "bonus_earned": 0.0,
            "created_at": datetime.now(timezone.utc),
        })

    @staticmethod
    async def get_by_referrer(referrer_id: int):
        return await referrals_col.find({"referrer_id": referrer_id}).to_list(length=100)

    @staticmethod
    async def get_by_referred(referred_id: int):
        return await referrals_col.find_one({"referred_id": referred_id})

    @staticmethod
    async def add_purchase(referrer_id: int, referred_id: int, amount: float) -> float:
        bonus = round(amount * 0.1, 2)
        await referrals_col.update_one(
            {"referrer_id": referrer_id, "referred_id": referred_id},
            {"$inc": {"purchases": 1, "bonus_earned": bonus}}
        )
        return bonus

    @staticmethod
    async def leaderboard(limit: int = 10):
        pipeline = [
            {"$group": {
                "_id": "$referrer_id",
                "total_earned": {"$sum": "$bonus_earned"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"total_earned": -1}},
            {"$limit": limit},
        ]
        return await referrals_col.aggregate(pipeline).to_list(length=limit)


class WalletDeposit:
    @staticmethod
    async def create(user_id: int, amount: float, method: str, tx_id: str):
        await wallet_deposits_col.insert_one({
            "user_id": user_id, "amount": amount, "method": method,
            "tx_id": tx_id, "status": "completed",
            "created_at": datetime.now(timezone.utc),
        })
