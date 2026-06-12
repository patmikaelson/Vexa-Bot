import discord
from discord.ext import commands
from discord import app_commands, ui
import aiohttp

from bot.config import PAYMENT_API_URL, GUILD_ID, ASSETS_URL
from bot.embeds import BOT_AVATAR
from bot.models import ProductModel, TransactionModel, UserModel, ReferralModel, WalletDeposit, EmbedTracker
from bot.embeds import success, error, wallet_embed, deposit_success, bot_log, live_demo_embed
from bot.utils import tx_id, referral_code, ch_name, get_redis


CATEGORIES_LIST = ["Music", "Ticket", "Giveaway", "Security", "Game", "Utility", "AI", "FiveM"]


class AddProductModal(ui.Modal, title="🤖 Add New Bot Product"):
    name_inp = ui.TextInput(label="Bot Name", placeholder="e.g. MyAwesomeBot", max_length=60)
    desc_inp = ui.TextInput(label="Description", placeholder="Selling description...",
                            style=discord.TextStyle.paragraph, max_length=400)
    price_inp = ui.TextInput(label="Price (Tomans)", placeholder="e.g. 1500000", max_length=12)
    image_inp = ui.TextInput(label="Image URL (optional)", placeholder="https://...",
                             required=False, max_length=300)
    category_inp = ui.TextInput(label="Category", placeholder="Music, Ticket, Security, AI, etc.",
                                max_length=30)

    async def on_submit(self, i: discord.Interaction):
        try:
            price = int(self.price_inp.value.replace(",", ""))
            if price <= 0:
                raise ValueError
        except ValueError:
            return await i.response.send_message(
                embed=error("Invalid", "Price must be a positive integer (Tomans)."), ephemeral=True)

        await ProductModel.create(
            name=self.name_inp.value.strip(),
            description=self.desc_inp.value.strip(),
            price_tomans=price,
            category=self.category_inp.value.strip().capitalize(),
            image_url=self.image_inp.value.strip(),
        )

        # Increment remaining counter
        r = await get_redis()
        rem = await r.get("live_demo_remaining")
        if rem:
            await r.set("live_demo_remaining", int(rem) + 1)

        await i.response.send_message(
            embed=success("Product Added", f"**{self.name_inp.value}** added to the database."), ephemeral=True)

        guild = i.client.get_guild(GUILD_ID)
        if guild:
            log_ch = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
            if log_ch:
                await log_ch.send(embed=bot_log("📦 Product Added",
                                                f"{i.user.mention} added **{self.name_inp.value}** ({price:,} Tomans, {self.category_inp.value.strip().capitalize()})."))


class DepositModal(ui.Modal, title="💳 Deposit Credits"):
    def __init__(self, method: str):
        super().__init__()
        self.method = method
        self.amount_inp = ui.TextInput(
            label="Amount (USD)",
            placeholder="Enter amount, e.g. 10.00",
            min_length=1, max_length=10,
            required=True
        )
        self.add_item(self.amount_inp)

    async def on_submit(self, i: discord.Interaction):
        try:
            amount = float(self.amount_inp.value.replace(",", "."))
            if amount <= 0 or amount > 9999:
                return await i.response.send_message(
                    embed=error("Invalid", "Amount must be between $0.01 and $9,999."), ephemeral=True)
        except ValueError:
            return await i.response.send_message(embed=error("Invalid", "Enter a valid number."), ephemeral=True)

        tid = tx_id()
        await WalletDeposit.create(i.user.id, amount, self.method, tid)
        await UserModel.add_wallet(i.user.id, amount)
        await TransactionModel.create(tid, i.user.id, f"deposit_{self.method}", amount, "USD", self.method, "deposit")
        await TransactionModel.complete(tid)

        u = await UserModel.get(i.user.id)
        bal = u.get("wallet_balance", 0) if u else amount

        await i.response.send_message(
            embed=deposit_success(amount, self.method.capitalize(), bal), ephemeral=True)

        guild = i.client.get_guild(GUILD_ID)
        if guild:
            log_ch = discord.utils.get(guild.text_channels, name=ch_name("📊・admin-logs"))
            if log_ch:
                await log_ch.send(embed=bot_log("💰 Deposit",
                                                f"{i.user.mention} deposited **${amount:.2f}** via {self.method}. Balance: **${bal:.2f}**"))


class DepositView(ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @ui.button(label="Crypto", style=discord.ButtonStyle.primary, emoji="💳")
    async def crypto_btn(self, i: discord.Interaction, b: ui.Button):
        await i.response.send_modal(DepositModal("crypto"))

    @ui.button(label="PayPal", style=discord.ButtonStyle.success, emoji="💸")
    async def paypal_btn(self, i: discord.Interaction, b: ui.Button):
        await i.response.send_modal(DepositModal("paypal"))

    @ui.button(label="Iranian Bank", style=discord.ButtonStyle.secondary, emoji="🏦")
    async def bank_btn(self, i: discord.Interaction, b: ui.Button):
        await i.response.send_modal(DepositModal("iranian_bank"))


class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self._ensure_live_demo()

    async def _ensure_live_demo(self, force: bool = False):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        ch = discord.utils.get(guild.text_channels, name=ch_name("🎬・live-demo"))
        if not ch:
            return
        if force:
            await EmbedTracker.refresh("live_demo", guild, ch_name("🎬・live-demo"))
        if await EmbedTracker.get("live_demo"):
            return
        # Send first product immediately
        product = await ProductModel.random()
        if not product:
            return
        total = await ProductModel.count_active()
        r = await get_redis()
        await r.set("live_demo_index", 0)
        await r.set("live_demo_remaining", total)
        view = ui.View(timeout=None)
        btn = ui.Button(label="🛒 Buy Now", style=discord.ButtonStyle.primary,
                        custom_id=f"buy_now_{product['_id']}")
        view.add_item(btn)
        embed = live_demo_embed(product, total)
        msg = await ch.send(embed=embed, view=view)
        await EmbedTracker.set("live_demo", msg.id)

    # ── Commands ──────────────────────────────────────────────

    @app_commands.command(name="shop", description="Browse available bots")
    async def shop(self, i: discord.Interaction):
        products = await ProductModel.get_all()
        if not products:
            return await i.response.send_message(embed=error("Empty", "No products yet."), ephemeral=True)

        embed = discord.Embed(title="🛒 Bot Shop", color=0x5865F2, timestamp=discord.utils.utcnow())
        embed.set_footer(text="Built by Vexa – Secure Bot Shop", icon_url=BOT_AVATAR)
        embed.set_thumbnail(url=ASSETS_URL + "6.png")
        for p in products:
            embed.add_field(
                name=f"🤖 {p['name']}",
                value=f"**{p.get('price_tomans', 0):,} Tomans**\n{p.get('description', '')[:60]}…\n`/buy {p['_id']}`",
                inline=False
            )
        await i.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase a bot")
    @app_commands.describe(product_id="Product ID")
    async def buy(self, i: discord.Interaction, product_id: str):
        from bson.objectid import ObjectId
        try:
            product = await ProductModel.get_all()
            product = next((p for p in product if str(p["_id"]) == product_id), None)
        except:
            product = None
        if not product:
            return await i.response.send_message(
                embed=error("Not Found", f"`{product_id}` doesn't exist. Use `/shop` to see products."), ephemeral=True)

        await i.response.defer(ephemeral=True)
        tid = tx_id()
        price_usd = round(product["price_tomans"] / 42000, 2)
        await TransactionModel.create(tid, i.user.id, str(product["_id"]), price_usd, "USD", "wallet")
        u = await UserModel.get(i.user.id)

        if u and u.get("wallet_balance", 0) >= price_usd:
            view = ui.View(timeout=30)

            async def wallet_cb(interaction: discord.Interaction):
                ok = await UserModel.deduct_wallet(interaction.user.id, price_usd)
                if not ok:
                    return await interaction.response.send_message(
                        embed=error("Insufficient", "Not enough balance."), ephemeral=True)
                await TransactionModel.complete(tid)
                await self._grant_customer(interaction.user)
                await self._process_ref_bonus(interaction.user.id, price_usd)
                await interaction.response.send_message(
                    embed=success("Purchased!",
                                  f"**{product['name']}** for **${price_usd:.2f}** via wallet."),
                    ephemeral=True)
                log_ch = discord.utils.get(interaction.guild.text_channels, name=ch_name("📊・admin-logs"))
                if log_ch:
                    await log_ch.send(embed=bot_log("🛒 Purchase",
                                                    f"{interaction.user.mention} bought **{product['name']}** for ${price_usd:.2f}"))

            btn = ui.Button(label=f"Pay with Wallet (${u['wallet_balance']:.2f})",
                            style=discord.ButtonStyle.success, emoji="💳")
            btn.callback = wallet_cb
            view.add_item(btn)

            await i.followup.send(
                embed=success("Checkout",
                              f"**{product['name']}** – ${price_usd:.2f}\nWallet: **${u['wallet_balance']:.2f}**"),
                view=view
            )
            return

        await self._gateway_payment(i, tid, product, price_usd)

    async def _gateway_payment(self, i: discord.Interaction, tid: str, product: dict, amount: float):
        async with aiohttp.ClientSession() as session:
            payload = {
                "tx_id": tid, "user_id": i.user.id, "product_id": str(product["_id"]),
                "amount": amount, "currency": "USD", "gateway": "nowpayments",
            }
            try:
                async with session.post(f"{PAYMENT_API_URL}/create-payment", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        link = data.get("payment_url") or data.get("pay_link") or ""
                        embed = success("🌐 Payment Link", f"**{product['name']}** – ${amount:.2f}")
                        embed.add_field(name="🔗 Link", value=f"[Click to Pay]({link})", inline=False)
                        await i.followup.send(embed=embed)
                    else:
                        txt = await resp.text()
                        await i.followup.send(embed=error("API Error", txt[:200]))
            except Exception as e:
                await i.followup.send(embed=error("Connection Error", str(e)[:200]))

    @app_commands.command(name="wallet", description="View your wallet")
    async def wallet(self, i: discord.Interaction):
        uid = i.user.id
        await UserModel.upsert(uid, i.user.name)
        u = await UserModel.get(uid)
        refs = await ReferralModel.get_by_referrer(uid)
        code = u.get("referral_code")
        if not code:
            code = referral_code(uid)
            await UserModel.update(uid, referral_code=code)
        earned = sum(r.get("bonus_earned", 0) for r in refs)
        txs = await TransactionModel.by_user(uid, 5)

        embed = wallet_embed(
            balance=u.get("wallet_balance", 0),
            code=code, refs=len(refs), earned=earned,
            transactions=txs
        )
        view = DepositView()
        await i.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="add_product", description="Add a new product to the database (admin only)")
    async def add_product(self, i: discord.Interaction):
        admin_role = discord.utils.get(i.guild.roles, name="🛡️ Admin")
        if admin_role not in i.user.roles and i.user.id != i.guild.owner_id:
            return await i.response.send_message(embed=error("Denied", "Admin or Owner only."), ephemeral=True)
        await i.response.send_modal(AddProductModal())

    async def _grant_customer(self, member):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        m = guild.get_member(member.id)
        if not m:
            return
        r = discord.utils.get(guild.roles, name="⭐ Customer")
        if r:
            await m.add_roles(r, reason="Vexa purchase")
        await UserModel.update(member.id, customer=True)

    async def _process_ref_bonus(self, buyer_id: int, amount: float):
        u = await UserModel.get(buyer_id)
        if u and u.get("referred_by"):
            bonus = await ReferralModel.add_purchase(u["referred_by"], buyer_id, amount)
            await UserModel.add_wallet(u["referred_by"], bonus)


async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))
