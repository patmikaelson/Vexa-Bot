import discord
from discord.ext import commands
from bot.config import BOT_TOKEN, GUILD_ID
from bot.embeds import bot_log, error
from bot.models import ProductModel, EmbedTracker
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
            "large_image": "vexalarge",
            "large_text": "Vexa – Your Bot Business Partner",
            "small_image": "vexasmall",
            "small_text": "Secure • Fast • Modern",
        },
        party={"id": "ae488379-351d-4a4f-ad32-2b9b01c91657", "size": [1, 5]},
        secrets={"join": "VEXA_JOIN_SECRET"},
    )
    await bot.change_presence(activity=activity)


@bot.listen("on_interaction")
async def handle_components(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return
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


async def _register_persistent_views():
    """Register persistent views so component callbacks work after restart."""
    try:
        from bot.cogs.verification import VerifyView
        bot.add_view(VerifyView())
    except Exception as e:
        print(f"Register VerifyView error: {e}")
    try:
        from bot.cogs.tickets import TicketSelectView, TicketActions
        bot.add_view(TicketSelectView())
        open_tickets = await TicketModel.get_all_open()
        for t in open_tickets:
            mid = t.get("message_id")
            if mid:
                view = TicketActions(t["ticket_id"], t["type"])
                bot.add_view(view, message_id=mid)
    except Exception as e:
        print(f"Register ticket views error: {e}")



@bot.event
async def on_ready():
    print(f"✅ Vexa bot online as {bot.user}")
    guild = bot.get_guild(GUILD_ID)

    # Sync commands (guild-only to avoid duplicates)
    synced = []
    try:
        guild_obj = discord.Object(id=GUILD_ID)
        bot.tree.clear_commands(guild=guild_obj)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"Synced {len(synced)} slash commands to guild {GUILD_ID}")
    except Exception as e:
        print(f"Sync error: {e}")

    # Auto-setup (wrapped to prevent crash on failure)
    try:
        if guild:
            from bot.cogs.setup import SetupCog
            cog = SetupCog(bot)
            await cog.auto_setup(guild)
            print("Auto-setup complete.")
    except Exception as e:
        print(f"Auto-setup error: {e}")

    # Seed 50 products
    try:
        count = await ProductModel.seed_50()
        if count:
            print(f"Seeded {count} new products.")
        print(f"Total active products: {await ProductModel.count_active()}")
    except Exception as e:
        print(f"Seed/count error: {e}")

    # Clear old embed trackers so fresh embeds with correct images are sent
    try:
        if guild:
            await EmbedTracker.clear_all(guild)
            print("Old trackers cleared.")
    except Exception as e:
        print(f"Clear trackers error: {e}")

    # Send fresh embeds
    try:
        if guild:
            from bot.cogs.setup import SetupCog
            cog = SetupCog(bot)
            await cog._seed_content(guild, force=False)
            print("Static embeds seeded.")
    except Exception as e:
        print(f"Refresh embeds error: {e}")

    try:
        if guild:
            from bot.cogs.verification import VerificationCog
            vcog = VerificationCog(bot)
            await vcog._ensure(force=False)
            print("Verify panel seeded.")
    except Exception as e:
        print(f"Refresh verify panel error: {e}")

    try:
        if guild:
            from bot.cogs.tickets import TicketCog
            tcog = TicketCog(bot)
            await tcog._ensure_panel(force=False)
            print("Ticket panel seeded.")
    except Exception as e:
        print(f"Refresh ticket panel error: {e}")

    try:
        if guild:
            from bot.cogs.shop import ShopCog
            scog = ShopCog(bot)
            await scog._ensure_live_demo(force=False)
            print("Live demo seeded.")
    except Exception as e:
        print(f"Refresh live demo error: {e}")

    # Register persistent views
    try:
        await _register_persistent_views()
    except Exception as e:
        print(f"Register views error: {e}")

    try:
        await update_presence()
    except Exception as e:
        print(f"Presence error: {e}")

    # Log startup
    if guild:
        log_ch = discord.utils.get(guild.text_channels, name=ch_name("⚙️・bot-logs"))
        if log_ch:
            try:
                await log_ch.send(embed=bot_log(
                    "🟢 Bot Online",
                    f"Vexa bot started successfully.\n• Synced {len(synced)} commands\n• Active on {len(bot.guilds)} server(s)\n• {await ProductModel.count_active()} products in DB"
                ))
            except Exception as e:
                print(f"Startup log error: {e}")


@bot.event
async def on_guild_join(guild):
    await update_presence()


@bot.event
async def on_guild_remove(guild):
    await update_presence()


async def load():
    await bot.load_extension("bot.cogs.admin")
    await bot.load_extension("bot.cogs.setup")
    await bot.load_extension("bot.cogs.verification")
    await bot.load_extension("bot.cogs.tickets")
    await bot.load_extension("bot.cogs.referral")
    await bot.load_extension("bot.cogs.shop")
    await bot.load_extension("bot.cogs.stats")
    await bot.load_extension("bot.cogs.security")
    await bot.load_extension("bot.cogs.voice_support")


async def main():
    await load()
    await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
