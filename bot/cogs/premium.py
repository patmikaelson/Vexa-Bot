import discord
from discord.ext import commands
from discord import app_commands

from bot.config import GUILD_ID, ASSETS_URL
from bot.models import premium_products_col, GuildPlanModel, PremiumProductModel
from bot.embeds import success, error, BOT_AVATAR
from bot.plan_utils import get_guild_plan, activate_plan, upgrade_plan, get_plan_features


class PremiumCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="premium", description="View your current premium plan")
    async def premium(self, i: discord.Interaction):
        guild_id = i.guild_id or GUILD_ID
        plan = await get_guild_plan(guild_id)
        plan_type = plan["plan_type"].title()
        features = plan["features"]

        embed = discord.Embed(title="⭐ Premium Plan", color=0xFFD700, timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=ASSETS_URL + "6.png")
        embed.add_field(name="📋 Current Plan", value=f"**{plan_type}**", inline=True)
        if plan.get("end_date"):
            embed.add_field(name="⏳ Expires", value=f"<t:{int(plan['end_date'].timestamp())}:R>", inline=True)

        feature_list = []
        for key, val in features.items():
            if isinstance(val, bool):
                feature_list.append(f"{'✅' if val else '❌'} {key.replace('_', ' ').title()}")
        if feature_list:
            embed.add_field(name="🔧 Features", value="\n".join(feature_list[:15]), inline=False)

        embed.set_footer(text="Vexa Premium", icon_url=BOT_AVATAR)
        await i.response.send_message(embed=embed)

    @app_commands.command(name="plans", description="List available premium plans")
    async def plans(self, i: discord.Interaction):
        await PremiumProductModel.seed()
        products = await PremiumProductModel.get_all()

        embed = discord.Embed(title="⭐ Premium Plans", color=0xFFD700, timestamp=discord.utils.utcnow())
        embed.set_thumbnail(url=ASSETS_URL + "6.png")

        for p in products:
            features = p.get("features", {})
            feature_str = ", ".join(k.replace("_", " ").title() for k, v in features.items() if isinstance(v, bool) and v)
            embed.add_field(
                name=f"{p['plan_name']} — {p['price_tomans']:,} Tomans/mo",
                value=f"{p['description']}\n{feature_str[:200]}",
                inline=False
            )

        embed.set_footer(text="Use /buy_premium to purchase", icon_url=BOT_AVATAR)
        await i.response.send_message(embed=embed)

    @app_commands.command(name="buy_premium", description="Purchase/upgrade your premium plan")
    @app_commands.describe(plan="Plan name")
    @app_commands.choices(plan=[
        app_commands.Choice(name="Silver (199K Tomans)", value="Silver"),
        app_commands.Choice(name="Gold (499K Tomans)", value="Gold"),
        app_commands.Choice(name="Platinum (999K Tomans)", value="Platinum"),
        app_commands.Choice(name="Ultimate (1999K Tomans)", value="Ultimate"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def buy_premium(self, i: discord.Interaction, plan: str):
        guild_id = i.guild_id or GUILD_ID
        current = await get_guild_plan(guild_id)
        current_type = current["plan_type"]

        plan_order = ["free", "silver", "gold", "platinum", "ultimate"]
        plan_lower = plan.lower()
        current_idx = plan_order.index(current_type) if current_type in plan_order else 0
        new_idx = plan_order.index(plan_lower) if plan_lower in plan_order else 0

        if new_idx <= current_idx and current_type != "free":
            return await i.response.send_message(
                embed=error("Downgrade", "You cannot downgrade. Contact support."), ephemeral=True)

        await PremiumProductModel.seed()
        product = await premium_products_col.find_one({"plan_name": plan})
        if not product:
            return await i.response.send_message(embed=error("Not Found", "Plan not found."), ephemeral=True)

        if current_type == "free":
            await activate_plan(guild_id, plan_lower, f"manual_{i.user.id}")
        else:
            await upgrade_plan(guild_id, plan_lower, f"manual_{i.user.id}")

        features = await get_plan_features(plan_lower)
        embed = discord.Embed(
            title="⭐ Premium Activated!",
            description=f"**{plan}** plan is now active for this server.",
            color=0xFFD700, timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=ASSETS_URL + "6.png")
        feature_list = [k.replace("_", " ").title() for k, v in features.items() if isinstance(v, bool) and v]
        if feature_list:
            embed.add_field(name="🔧 Unlocked Features", value="\n".join(feature_list[:10]), inline=False)
        embed.set_footer(text="Vexa Premium", icon_url=BOT_AVATAR)
        await i.response.send_message(embed=embed)

        log_ch = discord.utils.get(i.guild.text_channels, name="📊・admin-logs")
        if log_ch:
            await log_ch.send(embed=discord.Embed(
                title="⭐ Premium Purchase",
                description=f"{i.user.mention} activated **{plan}** plan for this server.",
                color=0xFFD700
            ))


async def setup(bot: commands.Bot):
    await bot.add_cog(PremiumCog(bot))
