import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

from bot.config import GUILD_ID
from bot.embeds import success, error, BOT_AVATAR
from bot.plan_utils import is_feature_enabled


class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ask", description="Ask GPT-4 a question (Platinum+ plan)")
    @app_commands.describe(question="Your question")
    async def ask(self, i: discord.Interaction, question: str):
        guild_id = i.guild_id or GUILD_ID
        if not await is_feature_enabled(guild_id, "gpt4_chat"):
            return await i.response.send_message(embed=error("Locked", "GPT-4 Chat requires Platinum+ plan."), ephemeral=True)

        await i.response.defer(ephemeral=True)
        embed = discord.Embed(title="🤖 GPT-4 Response", color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.add_field(name="❓ Question", value=question[:1000], inline=False)

        api_key = (await self.bot.get_cog("AICog"))._get_api_key() if hasattr(self, '_get_api_key') else ""
        if api_key:
            try:
                async with aiohttp.ClientSession() as s:
                    payload = {
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": question}],
                        "max_tokens": 500,
                    }
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    async with s.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            answer = data["choices"][0]["message"]["content"]
                            embed.add_field(name="💡 Answer", value=answer[:1024], inline=False)
                        else:
                            embed.add_field(name="💡 Answer", value="AI service currently unavailable.", inline=False)
            except:
                embed.add_field(name="💡 Answer", value="Could not reach AI service.", inline=False)
        else:
            embed.add_field(name="💡 Answer", value="AI service not configured.", inline=False)

        embed.set_footer(text="Vexa AI", icon_url=BOT_AVATAR)
        await i.followup.send(embed=embed)

    @app_commands.command(name="imagine", description="Generate an image with DALL-E (Platinum+ plan)")
    @app_commands.describe(prompt="Image description")
    async def imagine(self, i: discord.Interaction, prompt: str):
        guild_id = i.guild_id or GUILD_ID
        if not await is_feature_enabled(guild_id, "dalle"):
            return await i.response.send_message(embed=error("Locked", "DALL-E requires Platinum+ plan."), ephemeral=True)

        await i.response.defer(ephemeral=True)
        embed = discord.Embed(title="🎨 AI Generated Image", color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.add_field(name="📝 Prompt", value=prompt[:1000], inline=False)

        api_key = ""
        if api_key:
            try:
                async with aiohttp.ClientSession() as s:
                    payload = {
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1024",
                    }
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    async with s.post("https://api.openai.com/v1/images/generations", json=payload, headers=headers, timeout=60) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            image_url = data["data"][0]["url"]
                            embed.set_image(url=image_url)
                        else:
                            embed.add_field(name="💡 Result", value="Image generation unavailable.", inline=False)
            except:
                embed.add_field(name="💡 Result", value="Could not reach image service.", inline=False)
        else:
            embed.add_field(name="💡 Result", value="Image generation not configured (API key required).", inline=False)

        embed.set_footer(text="Vexa AI", icon_url=BOT_AVATAR)
        await i.followup.send(embed=embed)

    @app_commands.command(name="summarize", description="Summarize recent messages (Gold+ plan)")
    @app_commands.describe(limit="Number of messages (max 50)")
    async def summarize(self, i: discord.Interaction, limit: int = 20):
        guild_id = i.guild_id or GUILD_ID
        if not await is_feature_enabled(guild_id, "summarizer"):
            return await i.response.send_message(embed=error("Locked", "Summarizer requires Gold+ plan."), ephemeral=True)

        await i.response.defer(ephemeral=True)
        limit = min(max(limit, 5), 50)
        messages = []
        async for m in i.channel.history(limit=limit, oldest_first=False):
            if not m.author.bot:
                messages.append(f"{m.author.display_name}: {m.content[:100]}")
        summary = "\n".join(messages[-20:]) if messages else "No messages to summarize."
        embed = discord.Embed(title=f"📋 Channel Summary (last {limit} messages)", description=summary[:2000], color=0x5865F2)
        embed.set_footer(text="Vexa AI", icon_url=BOT_AVATAR)
        await i.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AICog(bot))
