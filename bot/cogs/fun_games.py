import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

from bot.config import GUILD_ID
from bot.models import EconomyModel, WerewolfGameModel
from bot.embeds import success, error, BOT_AVATAR
from bot.plan_utils import is_feature_enabled


class FunGamesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.giveaway_cache = {}

    @app_commands.command(name="trivia", description="Answer a trivia question and earn coins")
    async def trivia(self, i: discord.Interaction):
        questions = [
            {"q": "What is the capital of France?", "a": "paris"},
            {"q": "How many continents are there?", "a": "7"},
            {"q": "What color are bananas?", "a": "yellow"},
            {"q": "What is 5 + 3?", "a": "8"},
            {"q": "What planet is known as the Red Planet?", "a": "mars"},
        ]
        q = random.choice(questions)
        await i.response.send_message(
            embed=discord.Embed(title="🧠 Trivia", description=f"**{q['q']}**\n\nYou have 15 seconds!", color=0x5865F2),
        )

        def check(m):
            return m.author == i.user and m.channel == i.channel

        try:
            msg = await self.bot.wait_for("message", timeout=15.0, check=check)
            if msg.content.strip().lower() == q["a"]:
                reward = random.randint(50, 200)
                await EconomyModel.inc(i.user.id, balance=reward)
                await msg.reply(embed=success("Correct!", f"You earned **{reward} coins**!"))
            else:
                await msg.reply(embed=error("Wrong!", f"The answer was: **{q['a']}**"))
        except asyncio.TimeoutError:
            await i.channel.send(embed=error("Time's up!", f"The answer was: **{q['a']}**"))

    @app_commands.command(name="dice", description="Roll a dice and bet coins")
    @app_commands.describe(bet="Amount to bet")
    async def dice(self, i: discord.Interaction, bet: int):
        if bet <= 0:
            return await i.response.send_message(embed=error("Invalid", "Bet must be positive."), ephemeral=True)
        eco = await EconomyModel.ensure(i.user.id)
        bal = eco.get("balance", 0)
        if bal < bet:
            return await i.response.send_message(embed=error("Insufficient", f"You have **{bal:,} coins**."), ephemeral=True)

        roll = random.randint(1, 6)
        if roll >= 4:
            winnings = bet * 2
            await EconomyModel.inc(i.user.id, balance=winnings - bet)
            await i.response.send_message(embed=success("🎲 You Win!", f"Rolled **{roll}**! You won **{winnings:,} coins**!"))
        else:
            await EconomyModel.inc(i.user.id, balance=-bet)
            await i.response.send_message(embed=error("🎲 You Lose!", f"Rolled **{roll}**. Lost **{bet:,} coins**."))

    @app_commands.command(name="rps", description="Rock Paper Scissors against the bot")
    @app_commands.describe(choice="Your choice")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock 🪨", value="rock"),
        app_commands.Choice(name="Paper 📄", value="paper"),
        app_commands.Choice(name="Scissors ✂️", value="scissors"),
    ])
    async def rps(self, i: discord.Interaction, choice: str):
        bot_choice = random.choice(["rock", "paper", "scissors"])
        beats = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        result = "tie"
        if beats[choice] == bot_choice:
            result = "win"
        elif beats[bot_choice] == choice:
            result = "lose"

        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        embed = discord.Embed(title="Rock Paper Scissors", color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.add_field(name="You", value=f"{emojis[choice]} {choice.title()}", inline=True)
        embed.add_field(name="Bot", value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)

        if result == "win":
            reward = 100
            await EconomyModel.inc(i.user.id, balance=reward)
            embed.description = f"**You win!** +{reward} coins"
            embed.color = 0x00C853
        elif result == "lose":
            embed.description = "**You lose!**"
            embed.color = 0xFF1744
        else:
            embed.description = "**It's a tie!**"
            embed.color = 0xFFAB00

        embed.set_footer(text="Vexa Games", icon_url=BOT_AVATAR)
        await i.response.send_message(embed=embed)

    @app_commands.command(name="giveaway", description="Start a giveaway (Gold+ plan)")
    @app_commands.describe(prize="Prize description", winners="Number of winners", duration_minutes="Duration in minutes")
    async def giveaway(self, i: discord.Interaction, prize: str, winners: int = 1, duration_minutes: int = 60):
        guild_id = i.guild_id or GUILD_ID
        if not await is_feature_enabled(guild_id, "giveaway"):
            return await i.response.send_message(embed=error("Locked", "Giveaway requires Gold+ plan."), ephemeral=True)
        if winners < 1 or winners > 10:
            return await i.response.send_message(embed=error("Invalid", "Winners: 1-10."), ephemeral=True)
        if duration_minutes < 1 or duration_minutes > 1440:
            return await i.response.send_message(embed=error("Invalid", "Duration: 1-1440 minutes."), ephemeral=True)

        embed = discord.Embed(
            title="🎉 Giveaway",
            description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{int(discord.utils.utcnow().timestamp() + duration_minutes * 60)}:R>",
            color=0xFFD700, timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="React with 🎉 to enter!", icon_url=BOT_AVATAR)
        msg = await i.channel.send(embed=embed)
        await msg.add_reaction("🎉")
        self.giveaway_cache[msg.id] = {"prize": prize, "winners": winners, "end": duration_minutes * 60}
        await i.response.send_message(embed=success("Started", f"Giveaway for **{prize}** is live!"), ephemeral=True)

        await asyncio.sleep(duration_minutes * 60)
        msg = await i.channel.fetch_message(msg.id)
        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        if not reaction:
            return
        users = [u async for u in reaction.users() if not u.bot]
        if len(users) < winners:
            winners = len(users)
        if winners == 0:
            return await i.channel.send(embed=error("Giveaway", "No participants."))
        chosen = random.sample(users, min(winners, len(users)))
        await i.channel.send(
            embed=success("🎉 Giveaway Ended",
                          f"**Prize:** {prize}\n**Winners:** {', '.join(u.mention for u in chosen)}")
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(FunGamesCog(bot))
