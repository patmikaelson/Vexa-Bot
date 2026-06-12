import discord
from discord.ext import commands
from discord import app_commands
import random
from datetime import datetime, timezone, timedelta

from bot.config import GUILD_ID
from bot.models import EconomyModel, UserModel
from bot.embeds import success, error, BOT_AVATAR
from bot.plan_utils import is_feature_enabled


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, i: discord.Interaction):
        guild_id = i.guild_id or GUILD_ID
        eco = await EconomyModel.ensure(i.user.id)
        last = eco.get("last_daily")
        now = datetime.now(timezone.utc)

        if last and (now - last).total_seconds() < 86400:
            remaining = 86400 - (now - last).total_seconds()
            h, m = divmod(int(remaining), 3600)
            m, s = divmod(m, 60)
            return await i.response.send_message(
                embed=error("Cooldown", f"Next daily in **{h}h {m}m {s}s**"), ephemeral=True)

        streak = eco.get("daily_streak", 0) + 1
        bonus = min(streak * 50, 500)
        amount = 500 + bonus

        rpg_enabled = await is_feature_enabled(guild_id, "rpg")
        if not rpg_enabled:
            amount = min(amount, 100)

        await EconomyModel.update(i.user.id, daily_streak=streak, last_daily=now)
        await EconomyModel.inc(i.user.id, balance=amount)

        embed = discord.Embed(
            title="🎁 Daily Reward",
            description=f"You received **{amount:,} coins**!\nStreak: **{streak} day{'s' if streak > 1 else ''}**",
            color=0x00C853, timestamp=now
        )
        embed.set_footer(text="Vexa Economy", icon_url=BOT_AVATAR)
        await i.response.send_message(embed=embed)

    @app_commands.command(name="balance", description="Check your coin balance")
    async def balance(self, i: discord.Interaction):
        eco = await EconomyModel.ensure(i.user.id)
        bal = eco.get("balance", 0)
        await i.response.send_message(
            embed=discord.Embed(title="💰 Your Balance", description=f"**{bal:,} coins**", color=0x5865F2),
            ephemeral=True
        )

    @app_commands.command(name="transfer", description="Send coins to another user")
    @app_commands.describe(member="Recipient", amount="Amount to send")
    async def transfer(self, i: discord.Interaction, member: discord.Member, amount: int):
        if amount <= 0:
            return await i.response.send_message(embed=error("Invalid", "Amount must be positive."), ephemeral=True)
        if member.bot or member == i.user:
            return await i.response.send_message(embed=error("Invalid", "Cannot send to yourself or bots."), ephemeral=True)

        eco = await EconomyModel.ensure(i.user.id)
        bal = eco.get("balance", 0)
        if bal < amount:
            return await i.response.send_message(embed=error("Insufficient", f"You have **{bal:,} coins**."), ephemeral=True)

        await EconomyModel.inc(i.user.id, balance=-amount)
        await EconomyModel.ensure(member.id)
        await EconomyModel.inc(member.id, balance=amount)

        await i.response.send_message(
            embed=success("Sent", f"Transferred **{amount:,} coins** to {member.mention}."), ephemeral=True)

    @app_commands.command(name="shop_economy", description="Browse the economy shop")
    async def shop_economy(self, i: discord.Interaction):
        items = [
            {"name": "🎲 Lucky Dice", "price": 500, "desc": "Roll for a chance to win big!"},
            {"name": "🛡️ Shield", "price": 2000, "desc": "Protects you from being robbed."},
            {"name": "🎣 Fishing Rod", "price": 1500, "desc": "Catch fish and sell them."},
            {"name": "🌱 Seed Pack", "price": 300, "desc": "Plant and harvest crops."},
        ]
        embed = discord.Embed(title="🏪 Economy Shop", color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.set_footer(text="Vexa Economy", icon_url=BOT_AVATAR)
        for item in items:
            embed.add_field(name=item["name"], value=f"{item['desc']}\n💰 {item['price']:,} coins", inline=False)
        await i.response.send_message(embed=embed)

    @app_commands.command(name="rob", description="Attempt to rob another user")
    @app_commands.describe(member="Target")
    async def rob(self, i: discord.Interaction, member: discord.Member):
        guild_id = i.guild_id or GUILD_ID
        if not await is_feature_enabled(guild_id, "rpg"):
            return await i.response.send_message(embed=error("Locked", "This feature requires RPG (Gold+ plan)."), ephemeral=True)
        if member.bot or member == i.user:
            return await i.response.send_message(embed=error("Invalid", "Pick a real user."), ephemeral=True)

        target_eco = await EconomyModel.ensure(member.id)
        target_bal = target_eco.get("balance", 0)
        if target_bal < 100:
            return await i.response.send_message(embed=error("Poor", "Target is too poor to rob."), ephemeral=True)

        chance = random.random()
        if chance < 0.4:
            stolen = min(target_bal // 4, 5000)
            await EconomyModel.inc(i.user.id, balance=stolen)
            await EconomyModel.inc(member.id, balance=-stolen)
            await i.response.send_message(
                embed=success("Robbery", f"You stole **{stolen:,} coins** from {member.mention}!"))
        else:
            fine = 200
            await EconomyModel.inc(i.user.id, balance=-fine)
            await i.response.send_message(
                embed=error("Failed", f"You got caught! Paid **{fine:,} coins** fine."))


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
