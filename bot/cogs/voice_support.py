import discord
from discord.ext import commands
from discord import ui
import asyncio

from bot.config import GUILD_ID
from bot.embeds import voice_request_embed, voice_accepted_dm, voice_rejected_dm, success, error
from bot.utils import ch_name

ADMIN_CHANNEL_ID = 1513662365399519333
TARGET_VOICE_ID = 1514948383910137967


class RejectModal(ui.Modal, title="Reject Voice Request"):
    reason = ui.TextInput(
        label="Rejection Reason",
        placeholder="Explain why the request is rejected...",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True
    )

    def __init__(self, member: discord.Member, view_msg: discord.Message):
        super().__init__()
        self.member = member
        self.view_msg = view_msg

    async def on_submit(self, i: discord.Interaction):
        reason = self.reason.value.strip()
        if not reason:
            return await i.response.send_message(embed=error("Error", "Please enter a reason."), ephemeral=True)

        try:
            await self.member.send(embed=voice_rejected_dm(reason))
        except:
            pass

        try:
            await self.member.move_to(None)
        except:
            pass

        for child in self.view_msg.components:
            for c in child.children:
                c.disabled = True
        await self.view_msg.edit(view=self.view_msg)

        await i.response.send_message(embed=success("Rejected", f"**{self.member}** rejected. Reason sent via DM."), ephemeral=True)


class VoiceRequestView(ui.View):
    def __init__(self, member: discord.Member, target_vc: discord.VoiceChannel, view_msg: discord.Message):
        super().__init__(timeout=300)
        self.member = member
        self.target_vc = target_vc
        self.view_msg = view_msg

    @ui.button(label="✅ Accept", style=discord.ButtonStyle.success)
    async def accept(self, i: discord.Interaction, b: ui.Button):
        try:
            await self.member.move_to(self.target_vc)
        except Exception as e:
            return await i.response.send_message(embed=error("Error", f"Could not move user: {e}"), ephemeral=True)

        try:
            await self.member.send(embed=voice_accepted_dm(self.target_vc))
        except:
            pass

        for child in self.view_msg.components:
            for c in child.children:
                c.disabled = True
        await self.view_msg.edit(view=self.view_msg)

        await i.response.send_message(
            embed=success("Accepted", f"**{self.member}** moved to {self.target_vc.mention}."), ephemeral=True)

    @ui.button(label="❌ Reject", style=discord.ButtonStyle.danger)
    async def reject(self, i: discord.Interaction, b: ui.Button):
        modal = RejectModal(self.member, self.view_msg)
        await i.response.send_modal(modal)


class VoiceSupportCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._pending = set()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        if member.guild.id != GUILD_ID:
            return

        support_ch = discord.utils.get(member.guild.voice_channels, name=ch_name("🎧・voice-support"))
        if not support_ch:
            return

        if after.channel == support_ch and before.channel != support_ch:
            if member.id in self._pending:
                return
            self._pending.add(member.id)

            await asyncio.sleep(5)

            if member.voice and member.voice.channel == support_ch:
                admin_ch = self.bot.get_channel(ADMIN_CHANNEL_ID)
                target_vc = self.bot.get_channel(TARGET_VOICE_ID)
                if not admin_ch or not target_vc:
                    self._pending.discard(member.id)
                    return

                embed = voice_request_embed(member)
                view_msg = await admin_ch.send(embed=embed, view=VoiceRequestView(member, target_vc, None))
                view = VoiceRequestView(member, target_vc, view_msg)
                await view_msg.edit(view=view)

            self._pending.discard(member.id)

        elif before.channel == support_ch and after.channel != support_ch:
            self._pending.discard(member.id)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceSupportCog(bot))
