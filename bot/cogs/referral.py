import discord
from discord.ext import commands
from discord import app_commands

from bot.config import GUILD_ID
from bot.models import UserModel, ReferralModel, invite_refs_col
from bot.embeds import success, error
from bot.utils import referral_code, ch_name


class ReferralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="referral", description="Referral system")
    @app_commands.choices(action=[
        app_commands.Choice(name="Link", value="link"),
        app_commands.Choice(name="Leaderboard", value="leaderboard"),
    ])
    async def referral(self, i: discord.Interaction, action: str = "link"):
        uid = i.user.id
        await UserModel.upsert(uid, i.user.name)
        u = await UserModel.get(uid)

        if action == "link":
            code = u.get("referral_code") or referral_code(uid)
            if not u.get("referral_code"):
                await UserModel.update(uid, referral_code=code)

            embed = discord.Embed(color=0x5865F2, timestamp=discord.utils.utcnow())
            embed.set_footer(text="Vexa • Secure Bot Shop")
            embed.set_thumbnail(url="https://i.imgur.com/6wX9F6p.png")
            embed.title = "🔗 Your Referral Link"
            embed.description = "Share this link! When someone joins and buys, you earn **10%** credit."
            embed.add_field(name="📋 Code", value=f"`{code}`", inline=True)

            ch = discord.utils.get(i.guild.text_channels, name=ch_name("👋・welcome")) or i.channel
            try:
                invite = await ch.create_invite(max_age=0, max_uses=0, reason=f"Referral {code}")
                embed.add_field(name="🔗 Invite", value=f"{invite.url}?ref={code}", inline=False)
            except:
                embed.add_field(name="🔗 Note", value=f"Use code `{code}` when someone joins.", inline=False)

            await i.response.send_message(embed=embed, ephemeral=True)

        elif action == "leaderboard":
            top = await ReferralModel.leaderboard(10)
            embed = discord.Embed(title="🏆 Referral Leaderboard", color=0x5865F2,
                                  timestamp=discord.utils.utcnow())
            embed.set_footer(text="Vexa • Secure Bot Shop")
            embed.set_thumbnail(url="https://i.imgur.com/6wX9F6p.png")

            if not top:
                embed.description = "No referrals yet. Be the first!"
            else:
                medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                for pos, e in enumerate(top, 1):
                    m = i.guild.get_member(e["_id"])
                    name = m.display_name if m else f"User {e['_id']}"
                    p = medals.get(pos, f"**{pos}.**")
                    embed.add_field(name=f"{p} {name}",
                                    value=f"👥 {e['count']} · 💰 ${e['total_earned']:.2f}",
                                    inline=False)

            lb = discord.utils.get(i.guild.text_channels, name=ch_name("🏆・referral-leaderboard"))
            if lb and i.channel != lb:
                await lb.send(embed=embed)

            await i.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.invite_create):
                if hasattr(entry.target, "code"):
                    doc = await invite_refs_col.find_one({"invite_code": entry.target.code})
                    if doc:
                        await UserModel.upsert(member.id, member.name)
                        await UserModel.update(member.id, referred_by=doc["referrer_id"])
                        await ReferralModel.create(doc["referrer_id"], member.id, doc["ref_code"])
                        break
        except:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(ReferralCog(bot))
