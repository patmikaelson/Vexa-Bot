import discord
from datetime import datetime, timezone

BLURPLE = 0x5865F2
SUCCESS = 0x00C853
ERROR = 0xFF1744
WARNING = 0xFFAB00
GREY = 0x607D8B

THUMB = "https://i.imgur.com/6wX9F6p.png"


def _base(title: str, desc: str = None, color: int = BLURPLE) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=color,
                      timestamp=datetime.now(timezone.utc))
    e.set_footer(text="Built by Vexa – Secure Bot Shop", icon_url=THUMB)
    e.set_thumbnail(url=THUMB)
    return e


def success(title: str, desc: str) -> discord.Embed:
    return _base(f"✅ {title}", desc, SUCCESS)


def error(title: str, desc: str) -> discord.Embed:
    return _base(f"❌ {title}", desc, ERROR)


def warn(title: str, desc: str) -> discord.Embed:
    return _base(f"⚠️ {title}", desc, WARNING)


def verify_panel() -> discord.Embed:
    e = _base("✦ Vexa Verification",
              "Click **✅ Verify Me** below to gain full access.")
    e.add_field(name="📋 Steps", value="1. Click Verify\n2. Read rules\n3. Enjoy!", inline=False)
    return e


def welcome_dm(name: str) -> discord.Embed:
    e = success("🎉 Welcome!", f"Hey **{name}**, you've been verified!")
    e.add_field(name="🌟 What's Next?",
                value="• `/shop` — browse bots\n• `#🎫・create-ticket` — get help\n• `/referral` — earn rewards",
                inline=False)
    return e


def ticket_panel() -> discord.Embed:
    e = _base("🎫 Create a Ticket",
              "Select an option from the dropdown below to get started.")
    e.add_field(name="🛒 Buy a Bot", value="Purchase inquiries", inline=True)
    e.add_field(name="❓ Support", value="Technical help", inline=True)
    e.add_field(name="🤝 Referral", value="Referral or wallet issues", inline=True)
    return e


def ticket_created(tid: str, ttype: str, uid: int) -> discord.Embed:
    labels = {"buy": "🛒 Buy a Bot", "support": "❓ Support", "referral": "🤝 Referral Question"}
    e = success(f"Ticket #{tid}", f"Welcome <@{uid}>!")
    e.add_field(name="🆔 ID", value=f"`{tid}`", inline=True)
    e.add_field(name="📋 Type", value=labels.get(ttype, ttype), inline=True)
    e.add_field(name="👤 By", value=f"<@{uid}>", inline=True)
    e.add_field(name="📅 Created", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
    e.add_field(name="📌 Status", value="🟢 Open", inline=True)
    return e


def ticket_archived(tid: str) -> discord.Embed:
    return _base(f"📁 Ticket #{tid} Archived", "This ticket has been closed and archived.", GREY)


def product_embed(p: dict) -> discord.Embed:
    e = _base(f"🤖 {p['name']}", p.get("description", ""))
    e.add_field(name="💰 Price", value=f"`${p['price']:.2f}`", inline=True)
    e.add_field(name="🆔 ID", value=f"`{p['product_id']}`", inline=True)
    if p.get("image_url"):
        e.set_image(url=p["image_url"])
    if p.get("gif_url"):
        e.set_thumbnail(url=p["gif_url"])
    return e


def pricing_embed(products: list) -> discord.Embed:
    e = _base("💰 Bot Pricing", "Browse our bots. Use `/buy <id>` to purchase.")
    for p in products:
        e.add_field(
            name=f"🤖 {p['name']}",
            value=f"**${p['price']:.2f}** — `{p['product_id']}`\n{p.get('description', '')[:80]}",
            inline=False
        )
    e.add_field(name="💳 Payment", value="• Wallet Credit\n• ZarinPal (IRR)\n• NowPayments (Crypto)", inline=False)
    return e


def stats_embed(online: int, open_tix: int, stale: int, voice: int,
                sales_today: int, sales_week: float) -> discord.Embed:
    e = _base("📊 Live Server Stats", "Real-time metrics")
    e.add_field(name="🟢 Online", value=f"`{online}`", inline=True)
    e.add_field(name="🎫 Open Tickets", value=f"`{open_tix}`", inline=True)
    e.add_field(name="⏳ Stale (>5m)", value=f"`{stale}`", inline=True)
    e.add_field(name="🎧 Voice Support", value=f"`{voice}` users", inline=True)
    e.add_field(name="💰 Sales Today", value=f"`{sales_today}` txns", inline=True)
    e.add_field(name="📈 Weekly Revenue", value=f"`${sales_week:.2f}`", inline=True)
    return e


def leaderboard_embed(top: list, guild) -> discord.Embed:
    e = _base("🏆 Referral Leaderboard", "Top 10 referrers")
    if not top:
        e.description = "No referrals yet. Be the first!"
    else:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for pos, entry in enumerate(top, 1):
            m = guild.get_member(entry["_id"])
            name = m.display_name if m else f"User {entry['_id']}"
            p = medals.get(pos, f"**{pos}.**")
            e.add_field(name=f"{p} {name}",
                        value=f"👥 {entry['count']} · 💰 ${entry['total_earned']:.2f}",
                        inline=False)
    return e


def flash_sale_embed(p: dict) -> discord.Embed:
    e = _base("🔥 Flash Sale!",
              f"**Limited time!**\n**{p['name']}** at a great price!")
    e.add_field(name="🤖 Bot", value=p['name'], inline=True)
    e.add_field(name="💰 Price", value=f"~~${p['price']*1.3:.2f}~~ **${p['price']:.2f}**", inline=True)
    e.add_field(name="⏳ Offer Ends", value="Soon!", inline=False)
    if p.get("image_url"):
        e.set_image(url=p["image_url"])
    return e


def rules_embed() -> discord.Embed:
    e = _base("📜 Server Rules", "Follow the rules to keep Vexa safe.")
    e.add_field(name="1️⃣ Be Respectful", value="No harassment or toxicity.", inline=False)
    e.add_field(name="2️⃣ No Spam", value="No spam messages or invites.", inline=False)
    e.add_field(name="3️⃣ No Scams", value="No unauthorized selling.", inline=False)
    e.add_field(name="4️⃣ Discord ToS", value="You must be 13+.", inline=False)
    e.add_field(name="5️⃣ Tickets", value="Use `#🎫・create-ticket` for support.", inline=False)
    e.add_field(name="6️⃣ Verify", value="Verify in `#✅・verify` to access channels.", inline=False)
    return e


def announcement_embed(title: str, message: str, author: str) -> discord.Embed:
    e = _base(f"📢 {title}", message)
    e.set_footer(text=f"Posted by {author} • Built by Vexa – Secure Bot Shop", icon_url=THUMB)
    return e


def bot_log(event: str, details: str) -> discord.Embed:
    return _base(f"⚙️ {event}", details, GREY)


def wallet_embed(balance: float, code: str, refs: int, earned: float,
                 transactions: list) -> discord.Embed:
    e = _base("💰 Your Wallet", f"**Balance:** `${balance:.2f}`")
    e.add_field(name="🔗 Referral Code", value=f"`{code}`", inline=True)
    e.add_field(name="👥 Referred", value=f"`{refs}`", inline=True)
    e.add_field(name="🏆 Bonus Earned", value=f"`${earned:.2f}`", inline=True)
    if transactions:
        lines = []
        for tx in transactions[:5]:
            amt = tx.get("amount", 0)
            m = tx.get("method", tx.get("gateway", "?"))
            s = "✅" if tx.get("status") == "completed" else "⏳"
            lines.append(f"{s} `${amt:.2f}` via {m}")
        e.add_field(name="📜 Recent Activity", value="\n".join(lines) or "None", inline=False)
    else:
        e.add_field(name="📜 Recent Activity", value="No transactions yet.", inline=False)
    return e


def deposit_success(amount: float, method: str, balance: float) -> discord.Embed:
    return success("Deposit Successful",
                   f"**+${amount:.2f}** via **{method}**\nNew balance: **${balance:.2f}**")


def live_demo_embed(product: dict, remaining: int) -> discord.Embed:
    name = product.get("name", "Unknown Bot")
    desc = product.get("description", "")
    price = product.get("price_tomans", 0)
    category = product.get("category", "General")
    img = product.get("image_url") or THUMB

    e = discord.Embed(
        title=f"🎵 Now Showing: {name}",
        description=desc,
        color=BLURPLE,
        timestamp=datetime.now(timezone.utc)
    )
    e.set_thumbnail(url=img)
    e.add_field(name="💰 Price", value=f"{price:,} Tomans", inline=True)
    e.add_field(name="📂 Category", value=category, inline=True)
    e.set_footer(text=f"Built by Vexa – Secure Bot Shop | #{remaining} bots left in rotation",
                 icon_url=THUMB)
    return e
