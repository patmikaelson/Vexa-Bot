import discord
from discord.ext import commands
from discord import app_commands

from bot.config import GUILD_ID
from bot.embeds import success, error
from bot.utils import ch_name


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sync", description="Force sync all slash commands (owner only)")
    async def sync_cmd(self, i: discord.Interaction):
        if i.user.id != i.guild.owner_id:
            return await i.response.send_message("❌ Only the server owner can sync.", ephemeral=True)
        guild_obj = discord.Object(id=GUILD_ID)
        self.bot.tree.copy_global_to(guild=guild_obj)
        synced = await self.bot.tree.sync(guild=guild_obj)
        await i.response.send_message(f"✅ Synced {len(synced)} commands.", ephemeral=True)

    @app_commands.command(name="embed", description="Send a custom embed to a channel")
    @app_commands.describe(
        title="Embed title",
        description="Embed description",
        image="Optional image URL",
        channel="Target channel (defaults to current)",
    )
    async def embed_cmd(
        self,
        i: discord.Interaction,
        title: str,
        description: str,
        image: str = None,
        channel: discord.TextChannel = None,
    ):
        if not i.user.guild_permissions.administrator:
            return await i.response.send_message(embed=error("Denied", "Admin only."), ephemeral=True)

        target = channel or i.channel
        if not isinstance(target, discord.TextChannel):
            return await i.response.send_message(embed=error("Invalid", "Target must be a text channel."), ephemeral=True)

        e = discord.Embed(title=title, description=description, color=0x5865F2, timestamp=discord.utils.utcnow())
        e.set_footer(text=f"Sent by {i.user.display_name}")
        if image:
            e.set_image(url=image)

        await target.send(embed=e)
        await i.response.send_message(
            embed=success("Sent", f"Embed delivered to {target.mention}"), ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
