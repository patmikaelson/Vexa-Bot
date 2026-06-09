import random
import string
import re
from datetime import datetime, timezone

import redis.asyncio as redis

from bot.config import REDIS_URL

_redis = None


async def get_redis():
    global _redis
    if _redis is None:
        _redis = await redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


def ch_name(name: str) -> str:
    return name.lower().replace(" ", "-")


def ticket_id() -> str:
    ts = int(datetime.now(timezone.utc).timestamp())
    suf = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"VX-{ts}-{suf}"


def referral_code(user_id: int) -> str:
    suf = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"VEXA_{suf}"


def tx_id() -> str:
    ts = int(datetime.now(timezone.utc).timestamp())
    suf = ''.join(random.choices(string.hexdigits.upper(), k=8))
    return f"TXVX-{ts}-{suf}"


async def set_active_ticket(user_id: int, tid: str, ttl: int = 600):
    r = await get_redis()
    await r.setex(f"ticket:active:{user_id}", ttl, tid)


async def get_active_ticket(user_id: int):
    r = await get_redis()
    return await r.get(f"ticket:active:{user_id}")


async def del_active_ticket(user_id: int):
    r = await get_redis()
    await r.delete(f"ticket:active:{user_id}")


INVITE_RE = re.compile(
    r'(?:https?://)?(?:www\.)?'
    r'(?:discord\.(?:gg|io|me|li)|discord(?:app)?\.com/invite)/[\w-]+',
    re.IGNORECASE
)


def has_invite(text: str) -> bool:
    return bool(INVITE_RE.search(text))
