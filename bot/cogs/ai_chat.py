import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
import json
from datetime import datetime, timezone

from bot.config import GUILD_ID, ASSETS_URL
from bot.models import (
    AISessionModel, AIConversationModel, ai_sessions_col, EmbedTracker
)
from bot.embeds import success, error, BOT_AVATAR
from bot.utils import ch_name, get_redis
from bot.plan_utils import get_daily_ai_limit, get_guild_plan
from bot.utils.ai_client import AIClient

AI_CATEGORY_NAME = "🤖 AI PRIVATE CHATS"
AI_EMBED_KEY = "ai_global_embed"
RATE_LIMIT_PER_MIN = 5
CTX_TTL = 3600
CTX_MAX_MSGS = 10


def _date_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _global_ai_embed() -> discord.Embed:
    e = discord.Embed(
        title="🤖 Vexa AI – هوش مصنوعی پیشرفته",
        description=(
            "به بخش هوش مصنوعی Vexa خوش آمدید!\n\n"
            "از اینجا می‌توانی با هوش مصنوعی Vexa گفتگو کنی.\n"
            "کافیست از دستور `/ai chat` استفاده کنی تا یک کانال خصوصی برایت ساخته شود.\n\n"
            "**🔹 قابلیت‌ها:**\n"
            "• گفتگوی هوشمند با هوش مصنوعی Vexa\n"
            "• پاسخ به سوالات عمومی، فنی، آموزشی\n"
            "• حافظه مکالمه (آخرین ۱۰ پیام)\n"
            "• پشتیبانی از فارسی و انگلیسی\n\n"
            "**🔹 محدودیت روزانه (بر اساس پلن سرور):**\n"
            "• رایگان: ۲۰ پیام\n"
            "• نقره‌ای: ۵۰ پیام\n"
            "• طلایی: ۲۰۰ پیام\n"
            "• پلاتینیوم: ۵۰۰ پیام\n"
            "• نهایی: نامحدود\n\n"
            "از `/ai chat` برای شروع استفاده کن!"
        ),
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc)
    )
    e.set_thumbnail(url=BOT_AVATAR)
    e.set_footer(text="Vexa AI – پاسخ‌ها توسط هوش مصنوعی", icon_url=BOT_AVATAR)
    return e


def _instruction_embed(user_name: str, daily_limit: int) -> discord.Embed:
    e = discord.Embed(
        title=f"🤖 سلام {user_name}!",
        description=(
            "این کانال خصوصی هوش مصنوعی شماست. هر سوالی داری بپرس. "
            "من در اسرع وقت پاسخ می‌دهم.\n\n"
            "🔹 برای بستن چت، از دکمه پایین استفاده کن.\n"
            "🔹 برای درخواست کمک از ادمین، دکمه مربوطه را بزن.\n"
            f"🔹 محدودیت روزانه: **{daily_limit}** پیام (بر اساس پلن سرور)."
        ),
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc)
    )
    e.set_thumbnail(url=BOT_AVATAR)
    e.set_footer(text="Vexa AI – هوش مصنوعی پیشرفته", icon_url=BOT_AVATAR)
    return e


class CloseConfirmView(ui.View):
    def __init__(self, channel: discord.TextChannel, user: discord.User):
        super().__init__(timeout=60)
        self.channel = channel
        self.user = user

    @ui.button(label="✅ بله، ببند", style=discord.ButtonStyle.danger)
    async def confirm(self, i: discord.Interaction, b: ui.Button):
        if i.user.id != self.user.id:
            return await i.response.send_message("❌ این فقط برای توست.", ephemeral=True)
        await i.response.defer()
        for child in self.children:
            child.disabled = True
        try:
            msg = await self.channel.send("🔒 کانال در ۵ ثانیه بسته می‌شود...")
            await asyncio.sleep(5)
            await msg.edit(content="🔒 کانال بسته شد.")
        except:
            pass
        await AISessionModel.deactivate(self.channel.id)
        r = await get_redis()
        await r.delete(f"ai_ctx:{self.channel.id}")
        guild_id = self.channel.guild.id
        await ai_sessions_col.delete_one({"channel_id": self.channel.id})
        await self.channel.delete(reason="AI chat closed by user")
        try:
            await self.user.send(
                embed=discord.Embed(
                    title="🔒 کانال بسته شد",
                    description="کانال هوش مصنوعی شما بسته شد. برای باز کردن یک کانال جدید، دوباره از `/ai chat` استفاده کنید.",
                    color=0x607D8B
                )
            )
        except:
            pass

    @ui.button(label="❌ انصراف", style=discord.ButtonStyle.secondary)
    async def cancel(self, i: discord.Interaction, b: ui.Button):
        if i.user.id != self.user.id:
            return await i.response.send_message("❌ این فقط برای توست.", ephemeral=True)
        for child in self.children:
            child.disabled = True
        await i.response.edit_message(content="✅ انصراف داده شد.", view=self)


class ChatView(ui.View):
    def __init__(self, channel: discord.TextChannel, user: discord.User):
        super().__init__(timeout=None)
        self.channel = channel
        self.user = user

    @ui.button(label="🔒 بستن چت", style=discord.ButtonStyle.danger, custom_id="ai_close_chat")
    async def close_chat(self, i: discord.Interaction, b: ui.Button):
        if i.user.id != self.user.id:
            return await i.response.send_message("❌ این فقط برای توست.", ephemeral=True)
        view = CloseConfirmView(self.channel, self.user)
        await i.response.send_message(
            "آیا مطمئنی که می‌خواهی این کانال را ببندی؟ تاریخچه گفتگو پاک خواهد شد.",
            view=view, ephemeral=True
        )

    @ui.button(label="🆘 درخواست ادمین", style=discord.ButtonStyle.primary, custom_id="ai_request_admin")
    async def request_admin(self, i: discord.Interaction, b: ui.Button):
        if i.user.id != self.user.id:
            return await i.response.send_message("❌ این فقط برای توست.", ephemeral=True)
        guild = i.guild
        admin_role = discord.utils.get(guild.roles, name="🛡️ Admin")
        log_ch = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
        if log_ch:
            embed = discord.Embed(
                title="🆘 درخواست کمک در کانال AI",
                color=0xFF0000,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="کاربر", value=i.user.mention, inline=True)
            embed.add_field(name="کانال", value=self.channel.mention, inline=True)
            embed.set_footer(text="Vexa AI Support", icon_url=BOT_AVATAR)
            await log_ch.send(
                content=admin_role.mention if admin_role else "",
                embed=embed
            )
        await i.response.send_message(
            "✅ درخواست شما به ادمین ارسال شد. به زودی پاسخ داده می‌شود.",
            ephemeral=True
        )


class AIChatCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ai_client = AIClient()
        self._rate_limit_cache = {}

    async def _check_rate_limit(self, user_id: int) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        key = f"ai_rate:{user_id}"
        r = await get_redis()
        pipe = r.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.zremrangebyscore(key, 0, now - 60)
        pipe.zcard(key)
        pipe.expire(key, 60)
        results = await pipe.execute()
        return results[3] <= RATE_LIMIT_PER_MIN

    async def _get_daily_usage(self, user_id: int) -> int:
        r = await get_redis()
        val = await r.get(f"ai_msg:{user_id}:{_date_key()}")
        return int(val) if val else 0

    async def _inc_daily_usage(self, user_id: int):
        r = await get_redis()
        key = f"ai_msg:{user_id}:{_date_key()}"
        await r.incr(key)
        await r.expire(key, 86400)

    async def _get_context(self, channel_id: int) -> list:
        r = await get_redis()
        data = await r.get(f"ai_ctx:{channel_id}")
        if data:
            return json.loads(data)
        return []

    async def _save_context(self, channel_id: int, messages: list):
        r = await get_redis()
        if len(messages) > CTX_MAX_MSGS * 2:
            messages = messages[-(CTX_MAX_MSGS * 2):]
        await r.setex(f"ai_ctx:{channel_id}", CTX_TTL, json.dumps(messages))

    # ── /ai group ──────────────────────────────────────────

    ai_group = app_commands.Group(name="ai", description="Commands related to Vexa AI")

    @ai_group.command(name="chat", description="یک کانال خصوصی هوش مصنوعی باز کن")
    async def ai_chat(self, i: discord.Interaction):
        guild = i.guild
        user = i.user

        existing = await AISessionModel.get_by_user(guild.id, user.id)
        if existing:
            ch = guild.get_channel(existing["channel_id"])
            if ch:
                return await i.response.send_message(
                    embed=error(
                        "کانال باز",
                        f"❌ شما در حال حاضر یک کانال AI باز دارید: {ch.mention}. لطفاً ابتدا آن را ببندید."
                    ),
                    ephemeral=True
                )
            else:
                await AISessionModel.deactivate(existing["channel_id"])

        daily_limit = await get_daily_ai_limit(guild.id)
        usage = await self._get_daily_usage(user.id)
        if usage >= daily_limit:
            return await i.response.send_message(
                embed=error(
                    "محدودیت روزانه",
                    "❌ محدودیت روزانه شما برای استفاده از هوش مصنوعی به پایان رسیده است. "
                    "برای افزایش محدودیت، پلن خود را ارتقا دهید (`/plans`)."
                ),
                ephemeral=True
            )

        await i.response.defer(ephemeral=True)

        cat = discord.utils.get(guild.categories, name=AI_CATEGORY_NAME)
        if not cat:
            cat = await guild.create_category(AI_CATEGORY_NAME)

        admin_role = discord.utils.get(guild.roles, name="🛡️ Admin")
        support_role = discord.utils.get(guild.roles, name="🟢 Support")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, attach_files=True, embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_channels=True,
                read_message_history=True
            ),
        }
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                attach_files=True, embed_links=True, manage_channels=True
            )
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                attach_files=True, embed_links=True
            )

        ch_name_clean = user.name.lower().replace(" ", "-")[:30]
        ch = await guild.create_text_channel(
            f"ai-{ch_name_clean}",
            category=cat,
            overwrites=overwrites,
            reason=f"AI chat for {user}"
        )

        session = await AISessionModel.create(guild.id, user.id, ch.id)
        view = ChatView(ch, user)
        embed = _instruction_embed(user.display_name, daily_limit)
        await ch.send(f"{user.mention}", embed=embed, view=view)

        await i.followup.send(
            embed=success("کانال ساخته شد", f"→ {ch.mention}"),
            ephemeral=True
        )

        log_ch = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
        if log_ch:
            await log_ch.send(
                embed=discord.Embed(
                    title="🤖 AI Chat Opened",
                    description=f"{user.mention} opened an AI chat channel.\nChannel: {ch.mention}",
                    color=0x5865F2
                )
            )

    @ai_group.command(name="setup", description="ایجاد یا بازفرستادن راهنمای هوش مصنوعی")
    @app_commands.checks.has_permissions(administrator=True)
    async def ai_setup(self, i: discord.Interaction):
        guild = i.guild
        cat = discord.utils.get(guild.categories, name=AI_CATEGORY_NAME)
        if not cat:
            cat = await guild.create_category(AI_CATEGORY_NAME)

        ch = discord.utils.get(cat.text_channels, name="ai-info")
        if not ch:
            ch = await guild.create_text_channel(
                "ai-info", category=cat,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(send_messages=False),
                    guild.me: discord.PermissionOverwrite(
                        view_channel=True, send_messages=True, manage_channels=True
                    ),
                }
            )

        await EmbedTracker.delete(AI_EMBED_KEY)
        msg = await ch.send(embed=_global_ai_embed())
        await EmbedTracker.set(AI_EMBED_KEY, msg.id)
        await i.response.send_message(
            embed=success("انجام شد", "راهنمای هوش مصنوعی در کانال ai-info قرار داده شد."),
            ephemeral=True
        )

    # ── Admin commands ─────────────────────────────────────

    @ai_group.command(name="close", description="بستن کانال AI یک کاربر (ادمین)")
    @app_commands.describe(user="کاربر مورد نظر")
    @app_commands.checks.has_permissions(administrator=True)
    async def ai_close(self, i: discord.Interaction, user: discord.User):
        guild = i.guild
        session = await AISessionModel.get_by_user(guild.id, user.id)
        if not session:
            return await i.response.send_message(
                embed=error("یافت نشد", "این کاربر کانال AI باز ندارد."),
                ephemeral=True
            )
        ch = guild.get_channel(session["channel_id"])
        await AISessionModel.deactivate(session["channel_id"])
        r = await get_redis()
        await r.delete(f"ai_ctx:{session['channel_id']}")
        await ai_sessions_col.delete_one({"channel_id": session["channel_id"]})
        if ch:
            await ch.delete(reason=f"AI chat closed by admin {i.user}")
        await i.response.send_message(
            embed=success("بسته شد", f"کانال AI کاربر {user.mention} بسته شد."),
            ephemeral=True
        )

    @ai_group.command(name="history", description="مشاهده تاریخچه AI یک کاربر (ادمین)")
    @app_commands.describe(user="کاربر مورد نظر")
    @app_commands.checks.has_permissions(administrator=True)
    async def ai_history(self, i: discord.Interaction, user: discord.User):
        guild = i.guild
        session = await AISessionModel.get_by_user(guild.id, user.id)
        if not session:
            return await i.response.send_message(
                embed=error("یافت نشد", "این کاربر کانال AI باز ندارد."),
                ephemeral=True
            )
        channel_id = session["channel_id"]
        msgs = await AIConversationModel.get_history(channel_id, 20)
        if not msgs:
            ch = guild.get_channel(channel_id)
            if ch:
                msgs = []
                async for m in ch.history(limit=20, oldest_first=True):
                    if not m.author.bot:
                        msgs.append({"role": "user", "content": m.content})
                    else:
                        msgs.append({"role": "assistant", "content": m.content})

        if not msgs:
            return await i.response.send_message(
                embed=error("خالی", "تاریخچه‌ای یافت نشد."),
                ephemeral=True
            )

        lines = []
        for m in msgs[-20:]:
            role = "👤" if m.get("role") == "user" else "🤖"
            content = m.get("content", "")[:200]
            lines.append(f"{role} {content}")
        text = "\n\n".join(lines)

        if len(text) > 1900:
            import io
            fp = io.BytesIO(text.encode("utf-8"))
            await i.response.send_message(
                file=discord.File(fp, filename=f"ai_history_{user.id}.txt"),
                ephemeral=True
            )
        else:
            await i.response.send_message(
                embed=discord.Embed(
                    title=f"📋 تاریخچه AI {user.display_name}",
                    description=text[:1900],
                    color=0x5865F2
                ),
                ephemeral=True
            )

    @ai_group.command(name="reset", description="پاک کردن حافظه مکالمه AI یک کاربر (ادمین)")
    @app_commands.describe(user="کاربر مورد نظر")
    @app_commands.checks.has_permissions(administrator=True)
    async def ai_reset(self, i: discord.Interaction, user: discord.User):
        guild = i.guild
        session = await AISessionModel.get_by_user(guild.id, user.id)
        if not session:
            return await i.response.send_message(
                embed=error("یافت نشد", "این کاربر کانال AI باز ندارد."),
                ephemeral=True
            )
        r = await get_redis()
        await r.delete(f"ai_ctx:{session['channel_id']}")
        await i.response.send_message(
            embed=success("پاک شد", f"حافظه مکالمه {user.mention} پاک شد."),
            ephemeral=True
        )

    # ── Message listener for AI channels ───────────────────

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or not msg.guild:
            return
        if msg.guild.id != GUILD_ID:
            return

        channel = msg.channel
        if not isinstance(channel, discord.TextChannel):
            return
        if not channel.name.startswith("ai-"):
            return
        if channel.category and AI_CATEGORY_NAME not in channel.category.name:
            return

        guild = msg.guild
        user = msg.author
        session = await AISessionModel.get_by_channel(channel.id)
        if not session or not session.get("is_active"):
            return

        daily_limit = await get_daily_ai_limit(guild.id)
        usage = await self._get_daily_usage(user.id)
        if usage >= daily_limit:
            await channel.send(
                embed=error(
                    "محدودیت روزانه",
                    "❌ محدودیت روزانه شما برای استفاده از هوش مصنوعی به پایان رسیده است. "
                    "برای افزایش محدودیت، پلن خود را ارتقا دهید (`/plans`)."
                )
            )
            return

        if not await self._check_rate_limit(user.id):
            await channel.send(
                embed=error(
                    "محدودیت سرعت",
                    "⚠️ لطفاً کمی صبر کنید. حداکثر ۵ پیام در دقیقه مجاز است."
                )
            )
            return

        await AISessionModel.update_activity(channel.id)
        await self._inc_daily_usage(user.id)
        await AIConversationModel.save_message(channel.id, "user", msg.content)

        ctx = await self._get_context(channel.id)
        ctx.append({"role": "user", "content": msg.content})

        async with channel.typing():
            reply = await self.ai_client.chat(ctx)

        if reply is None:
            await channel.send(
                embed=error(
                    "سرویس در دسترس نیست",
                    "⚠️ در حال حاضر سرویس هوش مصنوعی در دسترس نیست. لطفاً چند دقیقه دیگر تلاش کنید."
                )
            )
            log_ch = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
            if log_ch:
                await log_ch.send(
                    embed=discord.Embed(
                        title="⚠️ AI API Error",
                        description=f"User: {user.mention} (`{user.id}`)\nChannel: {channel.mention}",
                        color=0xFFAB00
                    )
                )
            return

        ctx.append({"role": "assistant", "content": reply})
        await self._save_context(channel.id, ctx)
        await AIConversationModel.save_message(channel.id, "assistant", reply)

        if len(reply) > 2000:
            for i in range(0, len(reply), 1900):
                await channel.send(reply[i:i+1900])
        else:
            await channel.send(reply)

        session_total = session.get("total_messages", 0) + 1
        await AISessionModel.update_activity(channel.id, session_total)

    # ── Ensure global embed on startup ─────────────────────

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        if await EmbedTracker.get(AI_EMBED_KEY):
            return
        cat = discord.utils.get(guild.categories, name=AI_CATEGORY_NAME)
        if not cat:
            return
        ch = discord.utils.get(cat.text_channels, name="ai-info")
        if not ch:
            return
        msg = await ch.send(embed=_global_ai_embed())
        await EmbedTracker.set(AI_EMBED_KEY, msg.id)


async def setup(bot: commands.Bot):
    await bot.add_cog(AIChatCog(bot))
