import discord
from discord.ext import commands
from discord import ui

from bot.config import ASSETS_URL, GUILD_ID
from bot.models import EmbedTracker, TicketModel, UserModel
from bot.embeds import success, error, BOT_AVATAR
from bot.utils import ch_name, ticket_id, set_active_ticket, get_active_ticket

INFO_CHANNEL_ID = 1513662357123895387
PREMIUM_CATEGORY_ID = 1513916161937641582

PERSIAN_INFO = (
    "**به ربات Vexa خوش آمدید**\n\n"
    "**ربات Vexa یک پلتفرم کامل برای مدیریت و فروش ربات‌های دیسکورد است.**\n\n"
    "**───  بخش‌ها  ───**\n\n"
    "**🔰 امنیت (Security)**\n"
    "• Anti-Raid: محافظت در برابر حملات عضویابی\n"
    "• فیلترینگ هوشمند: لینک‌های دعوت، الفاظ نامناسب، اسپم\n"
    "• Lockdown: قفل کردن سرور در شرایط بحرانی\n"
    "• سیستم Mute خودکار برای اسپم‌کنندگان\n\n"
    "**🎫 تیکت (Tickets)**\n"
    "• پنل تیکت با ۳ نوع: خرید، پشتیبانی، سوال رفرال\n"
    "• تیکت صوتی (Voice Ticket)\n"
    "• اولویت‌بندی: Low, Medium, High\n"
    "• ارشایو خودکار پیام‌ها\n"
    "• ارسال به ادمین‌ها در صورت عدم پاسخ\n\n"
    "**🎮 بازی و سرگرمی (Fun & Games)**\n"
    "• Werewolf (گرگینه) با نقش‌های مختلف\n"
    "• اقتصاد و فارمینگ (کشاورزی، دزدی، فروش)\n"
    "• Trivia، Dice، MemeWar، Snake، Pokémon\n"
    "• Duel Arena: مبارزات متنی با XP و Level\n\n"
    "**🎵 FiveM**\n"
    "• نمایش وضعیت سرور (Players, Ping, Map)\n"
    "• Whitelist اپلیکیشن و تایید ادمین\n"
    "• ابزارهای Roleplay: ماشین حساب damage، تاس، ID دیجیتال\n"
    "• Squad实时 و لاگ‌های سرور\n\n"
    "**🛠 ابزارها (Utility)**\n"
    "• TempVoice: ساخت و حذف خودکار چannel صوتی\n"
    "• PollMaster: نظرسنجی با گزینه‌های زیاد\n"
    "• Reminder، AutoTranslate، QOTD، ToDo\n"
    "• Webhook Sender، Embed Templates\n\n"
    "**🎨 شخصی‌سازی (Customization)**\n"
    "• Custom Embed Color و Custom Footer\n"
    "• Custom Welcome GIF\n"
    "• Personality Modes برای ربات\n"
    "• Custom Commands\n\n"
    "**🤖 هوش مصنوعی (AI)**\n"
    "• ChatGPT Bridge: مکالمه با GPT-4\n"
    "• ImageGenius: تولید تصویر با DALL-E\n"
    "• AI Mod: تشخیص محتوای نامناسب با هوش مصنوعی\n"
    "• Summarizer: خلاصه‌سازی خودکار کانال\n"
    "• Sentiment Analysis: تحلیل احساسات پیام‌ها\n\n"
    "**───  پلن‌ها  ───**\n\n"
    "**🆓 رایگان (Free)**\n"
    "• ۱ تیکت همزمان\n"
    "• آپلود فایل تا ۵ مگابایت\n"
    "• نگهداری لاگ: ۳ روز\n"
    "• ۰ کامند شخصی‌سازی\n\n"
    "**🥈 نقره‌ای (Silver) — 199,000 تومان/ماه**\n"
    "• رنگ اختصاصی امبد\n"
    "• فوتر اختصاصی\n"
    "• Temp Voice\n"
    "• FiveM Status\n"
    "• ۳ تیکت همزمان\n"
    "• آپلود ۱۰ مگابایت\n"
    "• نگهداری لاگ: ۷ روز\n"
    "• ۳ کامند شخصی\n"
    "• ۳ حالت شخصیت\n\n"
    "**🥇 طلایی (Gold) — 499,000 تومان/ماه**\n"
    "• همه چیز Silver +\n"
    "• FiveM Whitelist\n"
    "• Werewolf\n"
    "• Duel Arena\n"
    "• Giveaway\n"
    "• RPG\n"
    "• LinkKeeper\n"
    "• QOTD\n"
    "• Summarizer\n"
    "• ۸ تیکت همزمان\n"
    "• آپلود ۲۵ مگابایت\n"
    "• نگهداری لاگ: ۱۴ روز\n"
    "• ۱۰ کامند شخصی\n"
    "• ۵ حالت شخصیت\n\n"
    "**💎 پلاتینیوم (Platinum) — 999,000 تومان/ماه**\n"
    "• همه چیز Gold +\n"
    "• Werewolf Extra Roles\n"
    "• Casino\n"
    "• Pokémon\n"
    "• Auto Translate\n"
    "• Auto FAQ\n"
    "• Sentiment\n"
    "• GPT-4 Chat\n"
    "• DALL-E\n"
    "• IP/VPN Detection\n"
    "• ۱۵ تیکت همزمان\n"
    "• آپلود ۵۰ مگابایت\n"
    "• نگهداری لاگ: ۳۰ روز\n"
    "• ۲۰ کامند شخصی\n"
    "• ۱۰ حالت شخصیت\n\n"
    "**👑 نهایی (Ultimate) — 1,999,000 تومان/ماه**\n"
    "• همه چیز Platinum +\n"
    "• FiveM Rank Sync\n"
    "• Snake/Tetris\n"
    "• Webhook Sender\n"
    "• Embed Templates\n"
    "• TTS\n"
    "• Language Detection\n"
    "• Avatar Changer\n"
    "• ۹۹۹ تیکت همزمان (بدون محدودیت)\n"
    "• آپلود ۵۰۰ مگابایت\n"
    "• نگهداری لاگ: ۹۰ روز\n"
    "• ۹۹۹ کامند شخصی\n"
    "• ۹۹۹ حالت شخصیت\n"
    "• **همه چیز آنلاک است**"
)

ENGLISH_INFO = (
    "**Welcome to Vexa Bot**\n\n"
    "**Vexa is a complete platform for managing and selling Discord bots.**\n\n"
    "**───  Categories  ───**\n\n"
    "**🔰 Security**\n"
    "• Anti-Raid: protection against mass join attacks\n"
    "• Smart filtering: invite links, profanity, spam\n"
    "• Lockdown mode for emergency situations\n"
    "• Auto-mute for spammers\n\n"
    "**🎫 Tickets**\n"
    "• Ticket panel with 3 types: Buy, Support, Referral\n"
    "• Voice tickets\n"
    "• Priority levels: Low, Medium, High\n"
    "• Auto-archive messages\n"
    "• Admin alerts on inactivity\n\n"
    "**🎮 Fun & Games**\n"
    "• Werewolf with multiple roles\n"
    "• Economy & farming (plant, steal, sell)\n"
    "• Trivia, Dice, MemeWar, Snake, Pokémon\n"
    "• Duel Arena with XP and leveling\n\n"
    "**🎵 FiveM**\n"
    "• Server status (Players, Ping, Map)\n"
    "• Whitelist application & admin approval\n"
    "• RP tools: damage calculator, dice, digital ID\n"
    "• Live Squad & game server logs\n\n"
    "**🛠 Utility**\n"
    "• TempVoice: auto-create/delete voice channels\n"
    "• PollMaster with multiple options\n"
    "• Reminder, AutoTranslate, QOTD, ToDo\n"
    "• Webhook Sender, Embed Templates\n\n"
    "**🎨 Customization**\n"
    "• Custom Embed Color & Footer\n"
    "• Custom Welcome GIF\n"
    "• Personality Modes\n"
    "• Custom Commands\n\n"
    "**🤖 AI Features**\n"
    "• ChatGPT Bridge (GPT-4)\n"
    "• Image Generation (DALL-E)\n"
    "• AI Moderation\n"
    "• Channel Summarizer\n"
    "• Sentiment Analysis\n\n"
    "**───  Plans  ───**\n\n"
    "**🆓 Free**\n"
    "• 1 concurrent ticket\n"
    "• 5 MB file upload\n"
    "• 3-day log retention\n"
    "• 0 custom commands\n\n"
    "**🥈 Silver — 199,000 Tomans/month**\n"
    "• Custom embed color\n"
    "• Custom footer\n"
    "• Temp Voice\n"
    "• FiveM Status\n"
    "• 3 concurrent tickets\n"
    "• 10 MB upload\n"
    "• 7-day logs\n"
    "• 3 custom commands\n"
    "• 3 personality modes\n\n"
    "**🥇 Gold — 499,000 Tomans/month**\n"
    "• Everything in Silver +\n"
    "• FiveM Whitelist\n"
    "• Werewolf\n"
    "• Duel Arena\n"
    "• Giveaway\n"
    "• RPG\n"
    "• LinkKeeper\n"
    "• QOTD\n"
    "• Summarizer\n"
    "• 8 concurrent tickets\n"
    "• 25 MB upload\n"
    "• 14-day logs\n"
    "• 10 custom commands\n"
    "• 5 personality modes\n\n"
    "**💎 Platinum — 999,000 Tomans/month**\n"
    "• Everything in Gold +\n"
    "• Werewolf Extra Roles\n"
    "• Casino\n"
    "• Pokémon\n"
    "• Auto Translate\n"
    "• Auto FAQ\n"
    "• Sentiment\n"
    "• GPT-4 Chat\n"
    "• DALL-E\n"
    "• IP/VPN Detection\n"
    "• 15 concurrent tickets\n"
    "• 50 MB upload\n"
    "• 30-day logs\n"
    "• 20 custom commands\n"
    "• 10 personality modes\n\n"
    "**👑 Ultimate — 1,999,000 Tomans/month**\n"
    "• Everything in Platinum +\n"
    "• FiveM Rank Sync\n"
    "• Snake/Tetris\n"
    "• Webhook Sender\n"
    "• Embed Templates\n"
    "• TTS\n"
    "• Language Detection\n"
    "• Avatar Changer\n"
    "• Unlimited (999) concurrent tickets\n"
    "• 500 MB upload\n"
    "• 90-day logs\n"
    "• 999 custom commands\n"
    "• 999 personality modes\n"
    "• **Everything unlocked**"
)


class InfoView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="فارسی / English", style=discord.ButtonStyle.secondary, emoji="🌐", custom_id="info_lang_toggle")
    async def lang_toggle(self, i: discord.Interaction, b: ui.Button):
        is_farsi = i.message.embeds and i.message.embeds[0].title and "اطلاعات" in i.message.embeds[0].title
        embed = _info_embed(farsi=not is_farsi)
        await i.response.edit_message(embed=embed)

    @ui.button(label="Invite Vexa", style=discord.ButtonStyle.primary, emoji="🔗", custom_id="info_invite")
    async def invite_btn(self, i: discord.Interaction, b: ui.Button):
        invite = "https://discord.com/oauth2/authorize?client_id=1513531519787077632&permissions=8&scope=bot%20applications.commands"
        await i.response.send_message(
            embed=discord.Embed(
                title="🔗 Invite Vexa",
                description=f"[Click here to invite Vexa to your server]({invite})",
                color=0x5865F2
            ), ephemeral=True
        )

    @ui.button(label="خرید پلن / Buy Premium", style=discord.ButtonStyle.success, emoji="⭐", custom_id="info_premium")
    async def premium_btn(self, i: discord.Interaction, b: ui.Button):
        cog = i.client.get_cog("InfoCog")
        if cog:
            await cog._create_premium_ticket(i)
        else:
            await i.response.send_message(embed=error("Error", "System unavailable."), ephemeral=True)


def _info_embed(farsi: bool = True) -> discord.Embed:
    title = "✦ Vexa — اطلاعات ربات" if farsi else "✦ Vexa — Bot Information"
    desc = PERSIAN_INFO if farsi else ENGLISH_INFO
    e = discord.Embed(title=title, description=desc, color=0x5865F2, timestamp=discord.utils.utcnow())
    e.set_thumbnail(url=ASSETS_URL + "6.png")
    e.set_footer(text="Built by Vexa – Secure Bot Shop", icon_url=BOT_AVATAR)
    return e


class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self._ensure_info()

    async def _ensure_info(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        ch = guild.get_channel(INFO_CHANNEL_ID)
        if not ch:
            return
        if await EmbedTracker.get("info_panel"):
            return
        embed = _info_embed(farsi=True)
        view = InfoView()
        msg = await ch.send(embed=embed, view=view)
        await EmbedTracker.set("info_panel", msg.id)

    async def _create_premium_ticket(self, i: discord.Interaction):
        user = i.user
        guild = i.guild

        active = await get_active_ticket(user.id)
        if active:
            return await i.response.send_message(
                embed=error("Active", f"You already have ticket `{active}` open."), ephemeral=True)

        await i.response.defer(ephemeral=True)

        tid = ticket_id()
        cat = guild.get_channel(PREMIUM_CATEGORY_ID)
        if not cat or not isinstance(cat, discord.CategoryChannel):
            cat = discord.utils.get(guild.categories, name="🎫 TICKETS")
        if not cat:
            cat = await guild.create_category("🎫 TICKETS")

        ar = discord.utils.get(guild.roles, name="🛡️ Admin")
        sr = discord.utils.get(guild.roles, name="🟢 Support")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        if ar:
            overwrites[ar] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        if sr:
            overwrites[sr] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ch = await guild.create_text_channel(
            f"premium-{user.id}", category=cat, overwrites=overwrites, reason=f"Premium ticket {tid}"
        )
        await i.followup.send(embed=success("Opened", f"→ {ch.mention}"), ephemeral=True)

        await TicketModel.create(tid, user.id, "buy", ch.id, guild_id=GUILD_ID)
        await UserModel.upsert(user.id, user.name)
        await set_active_ticket(user.id, tid)

        embed = discord.Embed(
            title="⭐ Premium Purchase",
            description=f"{user.mention} wants to purchase a premium plan!",
            color=0xFFD700, timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=ASSETS_URL + "6.png")
        embed.add_field(name="🆔 Ticket", value=f"`{tid}`", inline=True)
        embed.add_field(name="👤 User", value=f"{user.mention}", inline=True)
        embed.add_field(name="📌 Status", value="🟢 Open", inline=True)
        embed.set_footer(text="Vexa • Premium", icon_url=BOT_AVATAR)

        from bot.cogs.tickets import TicketActions
        await ch.send(f"Welcome {user.mention}! Please let us know which plan you're interested in.", embed=embed, view=TicketActions(tid, "buy"))

        log_ch = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
        if log_ch:
            await log_ch.send(embed=discord.Embed(
                title="⭐ Premium Ticket",
                description=f"{user.mention} opened a premium purchase ticket.\nChannel: {ch.mention}",
                color=0xFFD700
            ))

async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCog(bot))
