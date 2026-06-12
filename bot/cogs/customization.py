import discord
from discord.ext import commands
from discord import app_commands

from bot.config import GUILD_ID
from bot.models import GuildSettingsManager
from bot.embeds import success, error
from bot.plan_utils import is_feature_enabled, get_custom_command_limit


class CustomizationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="set_embed_color", description="Set custom embed color (Silver+ plan)")
    @app_commands.describe(hex_color="Hex color code (e.g. #FF5733)")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_embed_color(self, i: discord.Interaction, hex_color: str):
        guild_id = i.guild_id or GUILD_ID
        if not await is_feature_enabled(guild_id, "custom_embed_color"):
            return await i.response.send_message(embed=error("Locked", "Custom embed color requires Silver+ plan."), ephemeral=True)
        try:
            color = int(hex_color.lstrip("#"), 16)
            if not (0 <= color <= 0xFFFFFF):
                raise ValueError
        except:
            return await i.response.send_message(embed=error("Invalid", "Use format `#RRGGBB`."), ephemeral=True)
        await GuildSettingsManager.set(guild_id, embed_color=color)
        await i.response.send_message(embed=success("Set", f"Embed color changed to `{hex_color}`."), ephemeral=True)

    @app_commands.command(name="set_footer", description="Set custom embed footer (Silver+ plan)")
    @app_commands.describe(text="Footer text")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_footer(self, i: discord.Interaction, text: str):
        guild_id = i.guild_id or GUILD_ID
        if not await is_feature_enabled(guild_id, "custom_footer"):
            return await i.response.send_message(embed=error("Locked", "Custom footer requires Silver+ plan."), ephemeral=True)
        if len(text) > 100:
            return await i.response.send_message(embed=error("Too Long", "Max 100 characters."), ephemeral=True)
        await GuildSettingsManager.set(guild_id, embed_footer=text)
        await i.response.send_message(embed=success("Set", f"Footer changed to: `{text}`"), ephemeral=True)

    @app_commands.command(name="set_welcome_gif", description="Set custom welcome GIF (Silver+ plan)")
    @app_commands.describe(url="GIF URL")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome_gif(self, i: discord.Interaction, url: str):
        guild_id = i.guild_id or GUILD_ID
        if not await is_feature_enabled(guild_id, "custom_welcome_gif"):
            return await i.response.send_message(embed=error("Locked", "Custom welcome GIF requires Silver+ plan."), ephemeral=True)
        if not url.startswith("http"):
            return await i.response.send_message(embed=error("Invalid", "Must be a valid URL."), ephemeral=True)
        await GuildSettingsManager.set(guild_id, welcome_gif=url)
        await i.response.send_message(embed=success("Set", "Welcome GIF updated."), ephemeral=True)

    @app_commands.command(name="add_command", description="Add a custom command")
    @app_commands.describe(trigger="Command trigger", response="Bot response")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_command(self, i: discord.Interaction, trigger: str, response: str):
        guild_id = i.guild_id or GUILD_ID
        limit = await get_custom_command_limit(guild_id)
        if limit <= 0:
            return await i.response.send_message(embed=error("Locked", "Custom commands require a premium plan."), ephemeral=True)
        existing = await GuildSettingsManager.get(guild_id, "custom_commands", [])
        if len(existing) >= limit:
            return await i.response.send_message(embed=error("Limit", f"Max {limit} custom commands on your plan."), ephemeral=True)
        existing.append({"trigger": trigger, "response": response})
        await GuildSettingsManager.set(guild_id, custom_commands=existing)
        await i.response.send_message(embed=success("Added", f"Command `{trigger}` added. ({len(existing)}/{limit})"), ephemeral=True)

    @app_commands.command(name="remove_command", description="Remove a custom command")
    @app_commands.describe(trigger="Command trigger to remove")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_command(self, i: discord.Interaction, trigger: str):
        guild_id = i.guild_id or GUILD_ID
        existing = await GuildSettingsManager.get(guild_id, "custom_commands", [])
        new_list = [c for c in existing if c["trigger"] != trigger]
        if len(new_list) == len(existing):
            return await i.response.send_message(embed=error("Not Found", f"No command `{trigger}`."), ephemeral=True)
        await GuildSettingsManager.set(guild_id, custom_commands=new_list)
        await i.response.send_message(embed=success("Removed", f"Command `{trigger}` removed."), ephemeral=True)

    @app_commands.command(name="list_commands", description="List custom commands")
    async def list_commands(self, i: discord.Interaction):
        guild_id = i.guild_id or GUILD_ID
        existing = await GuildSettingsManager.get(guild_id, "custom_commands", [])
        if not existing:
            return await i.response.send_message(embed=error("Empty", "No custom commands configured."), ephemeral=True)
        desc = "\n".join(f"**!{c['trigger']}** → {c['response'][:50]}" for c in existing)
        await i.response.send_message(embed=discord.Embed(title="📋 Custom Commands", description=desc, color=0x5865F2), ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or not msg.guild:
            return
        prefix = "!"
        if not msg.content.startswith(prefix):
            return
        trigger = msg.content[len(prefix):].split()[0].lower()
        guild_id = msg.guild.id
        existing = await GuildSettingsManager.get(guild_id, "custom_commands", [])
        for c in existing:
            if c["trigger"].lower() == trigger:
                await msg.channel.send(c["response"])
                return


async def setup(bot: commands.Bot):
    await bot.add_cog(CustomizationCog(bot))
