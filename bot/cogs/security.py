import discord
from discord.ext import commands
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import re
import asyncio

from bot.config import PROFANITY_LIST, GUILD_ID
from bot.embeds import warn
from bot.utils import ch_name


INVITE_RE = re.compile(
    r'(?:https?://)?(?:www\.)?'
    r'(?:discord\.(?:gg|io|me|li)|discordapp\.com/invite)/[\w-]+',
    re.IGNORECASE
)


class SecurityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.join_times = []
        self.raid_mode = False
        self.msg_counts = defaultdict(list)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        now = datetime.now(timezone.utc)
        self.join_times.append(now)
        recent = [t for t in self.join_times if t > now - timedelta(seconds=10)]
        if len(recent) >= 5 and not self.raid_mode:
            await self._lockdown(member.guild)

    async def _lockdown(self, guild: discord.Guild):
        self.raid_mode = True
        vxm = discord.utils.get(guild.roles, name="✦ VXM")
        for ch in guild.channels:
            try:
                await ch.set_permissions(guild.default_role,
                                         overwrite=discord.PermissionOverwrite(view_channel=False))
                if vxm:
                    await ch.set_permissions(vxm,
                                             overwrite=discord.PermissionOverwrite(view_channel=True, send_messages=True))
            except:
                pass

        log = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
        ar = discord.utils.get(guild.roles, name="🛡️ Admin")
        if log:
            await log.send(
                (ar.mention + "\n" if ar else "") +
                "🚨 **Anti-Raid** — >5 joins/10s. Lockdown active (only ✦ VXM+ can see channels).")

        await asyncio.sleep(300)
        self.raid_mode = False
        for ch in guild.channels:
            try:
                await ch.set_permissions(guild.default_role, overwrite=None)
            except:
                pass
        if log:
            await log.send("✅ **Raid mode deactivated.**")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or not msg.guild or msg.guild.id != GUILD_ID:
            return
        if msg.author.guild_permissions.administrator:
            return

        reason = None
        content = msg.content

        if INVITE_RE.search(content):
            reason = "Invite link"
        if not reason:
            for pat in PROFANITY_LIST:
                if re.search(pat, content, re.IGNORECASE):
                    reason = "Profanity"
                    break
        if not reason:
            key = f"{msg.author.id}:{msg.channel.id}"
            self.msg_counts[key].append(datetime.now(timezone.utc))
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=3)
            self.msg_counts[key] = [t for t in self.msg_counts[key] if t > cutoff]
            if len(self.msg_counts[key]) >= 5:
                reason = "Mass spam"

        if reason:
            await msg.delete()
            try:
                await msg.channel.send(f"{msg.author.mention} ❌ **{reason}**", delete_after=4)
            except:
                pass

            log = discord.utils.get(msg.guild.text_channels, name=ch_name("📊・admin-logs"))
            if log:
                await log.send(embed=warn("🚨 Auto-Mod",
                                          f"**User:** {msg.author.mention} (`{msg.author.id}`)\n"
                                          f"**Channel:** {msg.channel.mention}\n**Reason:** {reason}\n"
                                          f"**Content:** `{content[:300]}`"))

            if reason == "Mass spam":
                muted = discord.utils.get(msg.guild.roles, name="🚫 Muted")
                if muted:
                    await msg.author.add_roles(muted, reason="Auto-mute spam")
                    await asyncio.sleep(600)
                    await msg.author.remove_roles(muted, reason="Auto-unmute")


async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityCog(bot))
