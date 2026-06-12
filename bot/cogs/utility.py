import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from bot.config import GUILD_ID
from bot.models import UserModel
from bot.embeds import success, error, BOT_AVATAR
from bot.plan_utils import is_feature_enabled


class UtilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.temp_voice_channels = {}

    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(question="Poll question", option1="Option 1", option2="Option 2", option3="Option 3", option4="Option 4")
    async def poll(self, i: discord.Interaction, question: str,
                   option1: str, option2: str,
                   option3: str = None, option4: str = None):
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)

        desc = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))
        embed = discord.Embed(title=f"📊 {question}", description=desc, color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.set_footer(text=f"Poll by {i.user.display_name}", icon_url=BOT_AVATAR)
        msg = await i.channel.send(embed=embed)
        for idx in range(len(options)):
            await msg.add_reaction(emojis[idx])
        await i.response.send_message(embed=success("Poll Created", f"Check {i.channel.mention}"), ephemeral=True)

    @app_commands.command(name="remind", description="Set a reminder")
    @app_commands.describe(minutes="Minutes from now", text="Reminder text")
    async def remind(self, i: discord.Interaction, minutes: int, text: str):
        if minutes < 1 or minutes > 10080:
            return await i.response.send_message(embed=error("Invalid", "Minutes: 1-10080 (7 days)."), ephemeral=True)
        await i.response.send_message(
            embed=success("Reminder Set", f"I'll remind you about **{text}** in {minutes} minute(s)."), ephemeral=True)
        await asyncio.sleep(minutes * 60)
        try:
            await i.user.send(embed=discord.Embed(
                title="⏰ Reminder", description=text, color=0x5865F2))
        except:
            await i.channel.send(f"{i.user.mention} ⏰ **Reminder:** {text}")

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, i: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await i.response.send_message(embed=discord.Embed(
            title="🏓 Pong!",
            description=f"**Latency:** {latency}ms",
            color=0x00C853 if latency < 200 else 0xFFAB00
        ))

    @app_commands.command(name="serverinfo", description="Show server information")
    async def serverinfo(self, i: discord.Interaction):
        g = i.guild
        embed = discord.Embed(title=f"📋 {g.name}", color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=g.icon.url if g.icon else BOT_AVATAR)
        embed.add_field(name="👑 Owner", value=g.owner.mention if g.owner else "Unknown", inline=True)
        embed.add_field(name="👥 Members", value=g.member_count, inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(g.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📁 Channels", value=len(g.channels), inline=True)
        embed.add_field(name="🎭 Roles", value=len(g.roles), inline=True)
        embed.set_footer(text=f"ID: {g.id}", icon_url=BOT_AVATAR)
        await i.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(member="Target member")
    async def avatar(self, i: discord.Interaction, member: discord.Member = None):
        member = member or i.user
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=0x5865F2)
        embed.set_image(url=member.display_avatar.url)
        await i.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
