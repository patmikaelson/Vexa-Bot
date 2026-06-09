import discord
from discord.ext import commands

from bot.config import GUILD_ID
from bot.models import TicketModel, TransactionModel, EmbedTracker
from bot.embeds import stats_embed, warn
from bot.utils import ch_name


class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def refresh(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
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

        mid = await EmbedTracker.get("stats")
        if mid:
            try:
                msg = await ch.fetch_message(mid)
                await msg.edit(embed=embed)
                return
            except:
                pass

        msg = await ch.send(embed=embed)
        await EmbedTracker.set("stats", msg.id)

        if open_tix > 3 and stale == open_tix:
            log = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
            ar = discord.utils.get(guild.roles, name="🛡️ Admin")
            if log and ar:
                await log.send(ar.mention, embed=warn("🚨 Stale",
                                                       f"{open_tix} tickets all unanswered >5 min!"))

    @commands.Cog.listener()
    async def on_ready(self):
        await self.refresh()

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.status != after.status:
            await self.refresh()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState, after: discord.VoiceState):
        if before.channel != after.channel:
            await self.refresh()


async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
