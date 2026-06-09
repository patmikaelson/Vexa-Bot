import discord
from discord.ext import commands
from discord import app_commands, ui

from bot.config import GUILD_ID, VERIFIED_ROLE_ID
from bot.models import UserModel, EmbedTracker
from bot.embeds import verify_panel, welcome_dm, success, error, bot_log
from bot.utils import ch_name


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Verify Me", style=discord.ButtonStyle.success, custom_id="vxm_verify")
    async def verify_btn(self, i: discord.Interaction, b: discord.ui.Button):
        guild = i.guild

        # Try the specific role ID first, fall back to name
        role = guild.get_role(VERIFIED_ROLE_ID)
        if not role:
            role = discord.utils.get(guild.roles, name="✦ VXM")
        if not role:
            return await i.response.send_message(
                embed=error("Not Found", "Verified role not found. Run `/setup full` first."), ephemeral=True)

        if role in i.user.roles:
            return await i.response.send_message(embed=error("Already", "You are already verified."), ephemeral=True)

        await i.user.add_roles(role, reason="Vexa verify")
        await UserModel.upsert(i.user.id, i.user.name)
        await UserModel.set_verified(i.user.id)

        try:
            await i.user.send(embed=welcome_dm(i.user.name))
        except:
            pass

        log_ch = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
        if log_ch:
            await log_ch.send(embed=bot_log("✅ Verification",
                                            f"{i.user.mention} (`{i.user.id}`) verified and received {role.mention}."))

        await i.response.send_message(embed=success("Verified!", f"You now have {role.mention}."), ephemeral=True)


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self._ensure()

    async def _ensure(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        ch = discord.utils.get(guild.text_channels, name=ch_name("✅・verify"))
        if not ch:
            return
        if await EmbedTracker.get("verify_panel"):
            return
        msg = await ch.send(embed=verify_panel(), view=VerifyView())
        await EmbedTracker.set("verify_panel", msg.id)

    @app_commands.command(name="verify", description="(Re)send verification panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def cmd_verify(self, i: discord.Interaction):
        await EmbedTracker.delete("verify_panel")
        await self._ensure()
        await i.response.send_message(embed=success("Sent", "Panel placed in #✅・verify"), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VerificationCog(bot))
