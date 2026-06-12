from bot.models import guild_plans_col, premium_products_col, PLANS
from datetime import datetime, timezone, timedelta

FREE_FEATURES = {
    "custom_embed_color": False, "custom_footer": False, "temp_voice": False,
    "fivem_status": False, "fivem_whitelist": False, "fivem_rp_helper": False,
    "fivem_events": False, "fivem_rank_sync": False, "werewolf": False,
    "werewolf_extra_roles": False, "duel_arena": False, "giveaway": False,
    "rpg": False, "casino": False, "pokemon": False, "snake_tetris": False,
    "linkkeeper": False, "qotd": False, "auto_translate": False,
    "webhook_sender": False, "embed_templates": False, "summarizer": False,
    "auto_faq": False, "sentiment": False, "tts": False,
    "language_detection": False, "gpt4_chat": False, "dalle": False,
    "avatar_changer": False, "ip_vpn_detection": False,
    "custom_welcome_gif": False, "more_polls": False,
    "max_concurrent_tickets": 1, "file_upload_mb": 5, "log_retention_days": 3,
    "custom_commands": 0, "personality_modes": 0,
}

async def get_plan_features(plan_type: str) -> dict:
    plan_type_lower = plan_type.lower().strip()
    if plan_type_lower == "free":
        return dict(FREE_FEATURES)
    product = await premium_products_col.find_one({"plan_name": plan_type}, {"_id": 0, "features": 1})
    if product and "features" in product:
        base = dict(FREE_FEATURES)
        base.update(product["features"])
        return base
    return dict(FREE_FEATURES)

async def get_guild_plan(guild_id: int) -> dict:
    doc = await guild_plans_col.find_one({"guild_id": guild_id, "is_active": True})
    if not doc:
        return {"plan_type": "free", "features": dict(FREE_FEATURES)}
    plan_type = doc.get("plan_type", "free")
    features = await get_plan_features(plan_type)
    return {"plan_type": plan_type, "features": features, "end_date": doc.get("end_date")}

async def is_feature_enabled(guild_id: int, feature: str) -> bool:
    plan = await get_guild_plan(guild_id)
    val = plan["features"].get(feature, False)
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val > 0
    return bool(val)

async def get_feature_value(guild_id: int, feature: str, default=0):
    plan = await get_guild_plan(guild_id)
    return plan["features"].get(feature, default)

async def get_max_concurrent_tickets(guild_id: int) -> int:
    return await get_feature_value(guild_id, "max_concurrent_tickets", 1)

async def get_log_retention_days(guild_id: int) -> int:
    return await get_feature_value(guild_id, "log_retention_days", 3)

async def get_file_upload_mb(guild_id: int) -> int:
    return await get_feature_value(guild_id, "file_upload_mb", 5)

async def get_custom_command_limit(guild_id: int) -> int:
    return await get_feature_value(guild_id, "custom_commands", 0)

async def activate_plan(guild_id: int, plan_type: str, payment_id: str = ""):
    from bot.models import GuildPlanModel
    return await GuildPlanModel.create(guild_id, plan_type.lower(), payment_id)

DAILY_AI_LIMITS = {
    "free": 20,
    "silver": 50,
    "gold": 200,
    "platinum": 500,
    "ultimate": 999999,
}

async def get_daily_ai_limit(guild_id: int) -> int:
    plan = await get_guild_plan(guild_id)
    return DAILY_AI_LIMITS.get(plan["plan_type"], 20)

async def upgrade_plan(guild_id: int, new_plan_type: str, payment_id: str = ""):
    doc = await guild_plans_col.find_one({"guild_id": guild_id})
    upgraded_from = doc.get("plan_type") if doc else None
    await guild_plans_col.update_one(
        {"guild_id": guild_id},
        {"$set": {
            "plan_type": new_plan_type.lower(),
            "start_date": datetime.now(timezone.utc),
            "end_date": datetime.now(timezone.utc) + timedelta(days=30),
            "is_active": True,
            "payment_id": payment_id,
            "upgraded_from": upgraded_from,
        }},
        upsert=True
    )
