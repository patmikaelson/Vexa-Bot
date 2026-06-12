import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

from bot.config import GUILD_ID
from bot.embeds import success, error, BOT_AVATAR
from bot.plan_utils import is_feature_enabled


class FiveMCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="fivem", description="Check FiveM server status")
    @app_commands.describe(server_ip="Server IP:Port (e.g. 127.0.0.1:30120)")
    async def fivem(self, i: discord.Interaction, server_ip: str):
        guild_id = i.guild_id or GUILD_ID
        if not await is_feature_enabled(guild_id, "fivem_status"):
            return await i.response.send_message(embed=error("Locked", "FiveM Status requires Silver+ plan."), ephemeral=True)

        await i.response.defer()
        url = f"http://{server_ip}/info.json"
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        return await i.followup.send(embed=error("Offline", f"Server `{server_ip}` is offline or unreachable."))
                    data = await resp.json()
        except:
            return await i.followup.send(embed=error("Error", f"Could not reach `{server_ip}`."))

        embed = discord.Embed(title="🎮 FiveM Server Status", color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=BOT_AVATAR)
        embed.add_field(name="📡 Server", value=data.get("server", server_ip), inline=True)
        embed.add_field(name="👥 Players", value=f"{data.get('players', 0)}", inline=True)
        embed.add_field(name="🗺️ Map", value=data.get("mapname", "Unknown"), inline=True)
        embed.add_field(name="🆙 Version", value=data.get("version", "Unknown"), inline=True)
        embed.set_footer(text="Vexa FiveM", icon_url=BOT_AVATAR)
        await i.followup.send(embed=embed)

    @app_commands.command(name="fivem_whitelist", description="Apply for FiveM whitelist")
    @app_commands.describe(identifier="Your FiveM identifier", reason="Why should you be whitelisted?")
    async def whitelist(self, i: discord.Interaction, identifier: str, reason: str):
        guild_id = i.guild_id or GUILD_ID
        if not await is_feature_enabled(guild_id, "fivem_whitelist"):
            return await i.response.send_message(embed=error("Locked", "FiveM Whitelist requires Gold+ plan."), ephemeral=True)

        embed = discord.Embed(title="📋 Whitelist Application", color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.add_field(name="👤 User", value=i.user.mention, inline=True)
        embed.add_field(name="🆔 Identifier", value=identifier, inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.set_footer(text="Vexa FiveM", icon_url=BOT_AVATAR)

        log = discord.utils.get(i.guild.text_channels, name="📊・admin-logs")
        if log:
            await log.send(embed=embed)
        await i.response.send_message(embed=success("Submitted", "Your whitelist application has been sent to admins."), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(FiveMCog(bot))
