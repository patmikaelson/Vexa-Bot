import discord
from discord.ext import commands
from bot.config import BOT_TOKEN, GUILD_ID
from bot.embeds import bot_log, error
from bot.models import ProductModel
from bot.utils import ch_name
import time

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

_start_time = time.time()


async def update_presence():
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name="Vexa Bot",
        state=f"✅ Active on {len(bot.guilds)} servers",
        details="🛒 Vexa • Bot Shop & Security",
        timestamps={"start": int(_start_time)},
        assets={
            "large_image": "5852430520841604823",
            "large_text": "Vexa – Your Bot Business Partner",
            "small_image": "5852430520841604822",
            "small_text": "Secure • Fast • Modern",
        },
        party={"id": "ae488379-351d-4a4f-ad32-2b9b01c91657", "size": [1, 5]},
        secrets={"join": "VEXA_JOIN_SECRET"},
    )
    await bot.change_presence(activity=activity)


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        cid = interaction.data.get("custom_id", "")
        if cid.startswith("buy_now_"):
            product_id = cid.replace("buy_now_", "")
            product = None
            for p in await ProductModel.get_all():
                if str(p["_id"]) == product_id:
                    product = p
                    break
            if not product:
                return await interaction.response.send_message(
                    embed=error("Not Found", "Product no longer available."), ephemeral=True)

            cog = bot.get_cog("TicketCog")
            if cog:
                await cog._create(interaction, "buy")
            else:
                await interaction.response.send_message(
                    embed=error("Error", "Ticket system unavailable."), ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ Vexa bot online as {bot.user}")
    guild = bot.get_guild(GUILD_ID)

    # Sync commands
    synced = []
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild_obj)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Synced {len(synced)} slash commands to guild {GUILD_ID}")
    except Exception as e:
        print(f"Sync error: {e}")

    # Auto-setup
    if guild:
        from bot.cogs.setup import SetupCog
        cog = SetupCog(bot)
        await cog.auto_setup(guild)
        print("Auto-setup complete.")

    # Seed 50 products
    count = await ProductModel.seed_50()
    if count:
        print(f"Seeded {count} new products.")
    print(f"Total active products: {await ProductModel.count_active()}")

    await update_presence()

    # Log startup
    if guild:
        log_ch = discord.utils.get(guild.text_channels, name=ch_name("⚙️・bot-logs"))
        if log_ch:
            await log_ch.send(embed=bot_log(
                "🟢 Bot Online",
                f"Vexa bot started successfully.\n• Synced {len(synced)} commands\n• Active on {len(bot.guilds)} server(s)\n• {await ProductModel.count_active()} products in DB"
            ))


@bot.event
async def on_guild_join(guild):
    await update_presence()


@bot.event
async def on_guild_remove(guild):
    await update_presence()


@bot.tree.command(name="sync", description="Force sync all slash commands (owner only)")
async def sync_cmd(interaction: discord.Interaction):
    if interaction.user.id != (await bot.application_info()).owner.id and interaction.user.id != interaction.guild.owner_id:
        return await interaction.response.send_message("❌ Only the server owner can sync.", ephemeral=True)
    guild_obj = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild_obj)
    synced = await bot.tree.sync(guild=guild_obj)
    await interaction.response.send_message(f"✅ Synced {len(synced)} commands.", ephemeral=True)


async def load():
    await bot.load_extension("bot.cogs.setup")
    await bot.load_extension("bot.cogs.verification")
    await bot.load_extension("bot.cogs.tickets")
    await bot.load_extension("bot.cogs.referral")
    await bot.load_extension("bot.cogs.shop")
    await bot.load_extension("bot.cogs.stats")
    await bot.load_extension("bot.cogs.security")


async def main():
    await load()
    await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
