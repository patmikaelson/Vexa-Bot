import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
from datetime import datetime, timezone, timedelta

from bot.config import GUILD_ID
from bot.models import TicketModel, UserModel, EmbedTracker
from bot.embeds import ticket_panel, ticket_created, ticket_archived, success, error, warn, bot_log
from bot.utils import ticket_id, set_active_ticket, get_active_ticket, del_active_ticket, ch_name


class TicketSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Buy a Bot", value="buy", emoji="🛒",
                                 description="Purchase inquiries & sales"),
            discord.SelectOption(label="Support", value="support", emoji="❓",
                                 description="Technical help & issues"),
            discord.SelectOption(label="Referral Question", value="referral", emoji="🤝",
                                 description="Referral & wallet issues"),
        ]
        super().__init__(placeholder="🎫 Select ticket type…",
                         min_values=1, max_values=1, options=options,
                         custom_id="ticket_type_select")

    async def callback(self, i: discord.Interaction):
        cog = i.client.get_cog("TicketCog")
        if cog:
            await cog._create(i, self.values[0])


class TicketSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class PrioritySelect(ui.Select):
    def __init__(self, tid: str):
        opts = [
            discord.SelectOption(label="Low", value="low", emoji="🟢"),
            discord.SelectOption(label="Medium", value="medium", emoji="🟡"),
            discord.SelectOption(label="High", value="high", emoji="🔴"),
        ]
        super().__init__(placeholder="Set priority…", options=opts, custom_id=f"prio_{tid}")
        self.tid = tid

    async def callback(self, i: discord.Interaction):
        await TicketModel.update(self.tid, priority=self.values[0])
        await i.response.send_message(embed=success("Priority", f"Set to **{self.values[0].title()}**"), ephemeral=True)


class CloseBtn(ui.Button):
    def __init__(self, tid: str):
        super().__init__(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id=f"close_{tid}")
        self.tid = tid

    async def callback(self, i: discord.Interaction):
        cog = i.client.get_cog("TicketCog")
        if cog:
            await cog._close(i, self.tid)


class EscalateBtn(ui.Button):
    def __init__(self, tid: str):
        super().__init__(label="Escalate to Admin", style=discord.ButtonStyle.danger, emoji="📌", custom_id=f"esc_{tid}")
        self.tid = tid

    async def callback(self, i: discord.Interaction):
        cog = i.client.get_cog("TicketCog")
        if cog:
            await cog._escalate(i, self.tid)


class VoiceBtn(ui.Button):
    def __init__(self, tid: str):
        super().__init__(label="Request Voice Support", style=discord.ButtonStyle.secondary,
                         emoji="🎧", custom_id=f"voice_{tid}")
        self.tid = tid

    async def callback(self, i: discord.Interaction):
        cog = i.client.get_cog("TicketCog")
        if cog:
            await cog._request_voice(i, self.tid)


class TicketActions(ui.View):
    def __init__(self, tid: str, ttype: str):
        super().__init__(timeout=None)
        self.add_item(PrioritySelect(tid))
        self.add_item(CloseBtn(tid))
        self.add_item(EscalateBtn(tid))
        if ttype == "support":
            self.add_item(VoiceBtn(tid))


class TicketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self._ensure_panel()

    async def _ensure_panel(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        ch = discord.utils.get(guild.text_channels, name=ch_name("🎫・create-ticket"))
        if not ch:
            return
        if await EmbedTracker.get("ticket_panel"):
            return
        msg = await ch.send(embed=ticket_panel(), view=TicketSelectView())
        await EmbedTracker.set("ticket_panel", msg.id)

    async def _create(self, i: discord.Interaction, ttype: str):
        user = i.user
        guild = i.guild

        active = await get_active_ticket(user.id)
        if active:
            return await i.response.send_message(
                embed=error("Active", f"You already have ticket `{active}` open."), ephemeral=True)

        await i.response.defer(ephemeral=True)

        tid = ticket_id()

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
            f"ticket-{user.id}", category=cat, overwrites=overwrites, reason=f"Ticket {tid}"
        )
        await i.followup.send(embed=success("Opened", f"→ {ch.mention}"), ephemeral=True)

        await TicketModel.create(tid, user.id, ttype, ch.id)
        await UserModel.upsert(user.id, user.name)
        await set_active_ticket(user.id, tid)

        embed = ticket_created(tid, ttype, user.id)
        msg = await ch.send(f"Welcome {user.mention}!", embed=embed, view=TicketActions(tid, ttype))
        await TicketModel.update(tid, message_id=msg.id)

        log_ch = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
        if log_ch:
            await log_ch.send(embed=bot_log("🎫 New Ticket",
                                            f"**{tid}** — {ttype}\nUser: {user.mention}\nChannel: {ch.mention}"))

        self.bot.loop.create_task(self._inactivity(tid, ch))

    async def _inactivity(self, tid: str, ch: discord.TextChannel):
        await asyncio.sleep(600)
        t = await TicketModel.get(tid)
        if t and t["status"] == "open":
            log = discord.utils.get(ch.guild.text_channels, name=ch_name("📊・admin-logs"))
            ar_role = discord.utils.get(ch.guild.roles, name="🛡️ Admin")
            if log:
                mention = ar_role.mention if ar_role else ""
                await log.send(mention, embed=warn("⏰ Inactive",
                                                   f"Ticket `{tid}` in {ch.mention} – no response for 10min."))

    async def _close(self, i: discord.Interaction, tid: str):
        t = await TicketModel.get(tid)
        if not t:
            return await i.response.send_message(embed=error("Not Found", "Ticket not found."), ephemeral=True)
        if t["status"] == "closed":
            return await i.response.send_message(embed=error("Closed", "Already closed."), ephemeral=True)

        await TicketModel.close(tid)
        await del_active_ticket(t["user_id"])

        if t.get("voice_channel_id"):
            vc = i.guild.get_channel(t["voice_channel_id"])
            if vc:
                await vc.delete(reason=f"Ticket {tid} closed")

        await TicketModel.archive_messages(tid, i.channel)

        # Move channel to archived category
        archived_cat = discord.utils.get(i.guild.categories, name="📁 Archived Tickets")
        if not archived_cat:
            archived_cat = await i.guild.create_category("📁 Archived Tickets")
        await i.channel.edit(category=archived_cat, sync_permissions=True)

        await i.response.send_message(embed=success("Closed", f"Ticket `{tid}` archived."))
        log_ch = discord.utils.get(i.guild.text_channels, name=ch_name("📊・admin-logs"))
        if log_ch:
            await log_ch.send(embed=bot_log("🔒 Ticket Closed",
                                            f"`{tid}` closed by {i.user.mention}"))

    async def _escalate(self, i: discord.Interaction, tid: str):
        await TicketModel.update(tid, priority="high")
        ar_role = discord.utils.get(i.guild.roles, name="🛡️ Admin")
        mention = ar_role.mention if ar_role else ""
        await i.response.send_message(embed=warn("🚨 Escalated",
                                                 f"{mention}Priority set to **High**."))
        log_ch = discord.utils.get(i.guild.text_channels, name=ch_name("📊・admin-logs"))
        if log_ch:
            await log_ch.send(embed=bot_log("📌 Escalated",
                                            f"Ticket `{tid}` escalated by {i.user.mention}"))

    async def _request_voice(self, i: discord.Interaction, tid: str):
        t = await TicketModel.get(tid)
        if not t or t["status"] != "open":
            return await i.response.send_message(embed=error("Error", "Ticket not found or closed."), ephemeral=True)
        if t["type"] != "support":
            return await i.response.send_message(embed=error("N/A", "Only for support tickets."), ephemeral=True)

        guild = i.guild
        sc = discord.utils.get(guild.categories, name="👥 ──── 𝗦𝗨𝗣𝗣𝗢𝗥𝗧")
        if not sc:
            return await i.response.send_message(embed=error("Error", "Support category not found."), ephemeral=True)

        if t.get("voice_channel_id") and guild.get_channel(t["voice_channel_id"]):
            return await i.response.send_message(embed=error("Exists", "Voice channel already exists."), ephemeral=True)

        ar = discord.utils.get(guild.roles, name="🛡️ Admin")
        sr = discord.utils.get(guild.roles, name="🟢 Support")
        member = guild.get_member(t["user_id"])
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False, speak=False, view_channel=False),
            guild.me: discord.PermissionOverwrite(connect=True, speak=True, manage_channels=True),
        }
        if member:
            overwrites[member] = discord.PermissionOverwrite(connect=True, speak=True, view_channel=True)
        if ar:
            overwrites[ar] = discord.PermissionOverwrite(connect=True, speak=True, manage_channels=True)
        if sr:
            overwrites[sr] = discord.PermissionOverwrite(connect=True, speak=True)

        vc = await guild.create_voice_channel(f"voice-{tid[-8:]}", category=sc, overwrites=overwrites,
                                              reason=f"Voice {tid}")
        await TicketModel.set_voice_channel(tid, vc.id)

        if member and member.voice:
            try:
                await member.move_to(vc)
            except:
                pass
        if i.user.voice:
            try:
                await i.user.move_to(vc)
            except:
                pass

        await i.response.send_message(embed=success("🎧 Voice", f"Created {vc.mention}."))

    # ── /reopen ───────────────────────────────────────────────

    @app_commands.command(name="reopen", description="Reopen an archived ticket (admin only)")
    @app_commands.describe(ticket_id="Ticket ID to reopen")
    async def reopen(self, i: discord.Interaction, ticket_id: str):
        ar = discord.utils.get(i.guild.roles, name="🛡️ Admin")
        if ar not in i.user.roles and i.user.id != i.guild.owner_id:
            return await i.response.send_message(embed=error("Denied", "Admin only."), ephemeral=True)

        t = await TicketModel.get(ticket_id)
        if not t:
            return await i.response.send_message(embed=error("Not Found", f"Ticket `{ticket_id}` not found."), ephemeral=True)

        ch = i.guild.get_channel(t["channel_id"])
        if not ch:
            return await i.response.send_message(embed=error("Not Found", "Original channel no longer exists."), ephemeral=True)

        active_cat = discord.utils.get(i.guild.categories, name="🎫 TICKETS")
        if not active_cat:
            active_cat = await i.guild.create_category("🎫 TICKETS")

        await ch.edit(category=active_cat, sync_permissions=True)
        await TicketModel.reopen(ticket_id)
        await set_active_ticket(t["user_id"], ticket_id)

        await i.response.send_message(embed=success("Reopened", f"Ticket `{ticket_id}` is now active."), ephemeral=True)
        await ch.send(embed=warn("🔄 Reopened", f"Ticket reopened by {i.user.mention}"))

        log_ch = discord.utils.get(i.guild.text_channels, name=ch_name("📊・admin-logs"))
        if log_ch:
            await log_ch.send(embed=bot_log("🔄 Ticket Reopened",
                                            f"`{ticket_id}` reopened by {i.user.mention}"))


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketCog(bot))
