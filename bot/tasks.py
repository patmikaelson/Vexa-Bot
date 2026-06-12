import os
import asyncio
import random

from dotenv import load_dotenv
load_dotenv()
import discord

os.environ.setdefault("BOT_TOKEN", "")
os.environ.setdefault("GUILD_ID", "0")

from bot.celery_app import app
from bot.models import ProductModel, TicketModel, TransactionModel, ReferralModel, EmbedTracker
from bot.embeds import stats_embed, flash_sale_embed, warn, leaderboard_embed, live_demo_embed, bot_log
from bot.utils import ch_name, get_redis


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))


async def _edit_or_send(channel, key: str, embed, view=None):
    mid = await EmbedTracker.get(key)
    if mid:
        try:
            msg = await channel.fetch_message(mid)
            kwargs = {"embed": embed}
            if view is not None:
                kwargs["view"] = view
            await msg.edit(**kwargs)
            return
        except:
            pass
    kwargs = {"embed": embed}
    if view is not None:
        kwargs["view"] = view
    msg = await channel.send(**kwargs)
    await EmbedTracker.set(key, msg.id)


async def _run(action: str, **kw):
    if not BOT_TOKEN or not GUILD_ID:
        return
    intents = discord.Intents.default()
    intents.members = True
    client = discord.Client(intents=intents)
    try:
        await client.login(BOT_TOKEN)
        guild = client.get_guild(GUILD_ID) or await client.fetch_guild(GUILD_ID)

        if action == "stats":
            await _stats(guild)
        elif action == "alerts":
            await _alerts(guild)
        elif action == "flash_sales":
            await _flash_sales(guild)
        elif action == "leaderboard":
            await _leaderboard(guild)
        elif action == "rotate":
            await _rotate(guild, client)
    finally:
        await client.close()


async def _stats(guild):
    ch = discord.utils.get(guild.text_channels, name=ch_name("📊・live-stats"))
    if not ch:
        return
    online = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    open_tix = await TicketModel.count_open()
    stale = await TicketModel.count_stale(5)
    vc = discord.utils.get(guild.voice_channels, name=ch_name("🎧・voice-support"))
    voice = len(vc.members) if vc else 0
    st = await TransactionModel.count_today()
    sw = await TransactionModel.sum_week()
    embed = stats_embed(online, open_tix, stale, voice, st, sw)
    await _edit_or_send(ch, "stats", embed)


async def _alerts(guild):
    open_tix = await TicketModel.count_open()
    stale = await TicketModel.count_stale(5)
    if open_tix > 3 and stale == open_tix:
        log = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
        admin_r = discord.utils.get(guild.roles, name="🛡️ Admin")
        if log:
            await log.send(
                (admin_r.mention + "\n" if admin_r else "") +
                f"🚨 {open_tix} open tickets, all stale >5 min!"
            )


async def _flash_sales(guild):
    ch = discord.utils.get(guild.text_channels, name=ch_name("🔥・flash-sales"))
    if not ch:
        return
    product = await ProductModel.random()
    if not product:
        return
    embed = flash_sale_embed(product)
    view = discord.ui.View(timeout=30)
    view.add_item(discord.ui.Button(label="🛒 Buy Now", style=discord.ButtonStyle.danger, emoji="🔥",
                                     url=f"https://discord.com/channels/{GUILD_ID}/{ch.id}"))
    await _edit_or_send(ch, "flash_sales", embed, view)


async def _leaderboard(guild):
    ch = discord.utils.get(guild.text_channels, name=ch_name("🏆・referral-leaderboard"))
    if not ch:
        return
    top = await ReferralModel.leaderboard(10)
    embed = leaderboard_embed(top, guild)
    await _edit_or_send(ch, "leaderboard", embed)


# ── Live Demo Rotation (12h) ──────────────────────────────

async def _rotate(guild, client):
    ch = discord.utils.get(guild.text_channels, name=ch_name("🎬・live-demo"))
    log_ch = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
    if not ch:
        return

    products = await ProductModel.get_all()
    if not products:
        if log_ch:
            await log_ch.send(embed=bot_log("⚠️ Rotation Failed", "No active products found in database."))
        return

    total = len(products)
    r = await get_redis()
    index_key = "live_demo_index"

    current_index = await r.get(index_key)
    if current_index is None:
        current_index = 0
    else:
        current_index = (int(current_index) + 1) % total

    remaining = total - current_index
    await r.set(index_key, current_index)

    product = products[current_index]

    view = discord.ui.View(timeout=None)
    btn = discord.ui.Button(label="🛒 Buy Now", style=discord.ButtonStyle.primary,
                            custom_id=f"buy_now_{product['_id']}")
    view.add_item(btn)

    embed = live_demo_embed(product, remaining)
    # Send as new message — never delete or edit previous ones
    await ch.send(embed=embed, view=view)

    if log_ch:
        await log_ch.send(embed=bot_log("🔄 Live Demo Rotated",
                                        f"Now showing **{product['name']}** ({current_index+1}/{total})."))


# ── Celery tasks ──────────────────────────────────

@app.task
def update_stats_embed():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_run("stats"))
    loop.close()


@app.task
def update_flash_sales():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_run("flash_sales"))
    loop.close()


@app.task
def check_alerts():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_run("alerts"))
    loop.close()


@app.task
def update_leaderboard():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_run("leaderboard"))
    loop.close()


@app.task
def rotate_live_demo():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_run("rotate"))
    loop.close()
