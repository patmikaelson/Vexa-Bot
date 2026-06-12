import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from bot.config import CATEGORIES, ROLES, GUILD_ID, OWNER_ID
from bot.embeds import success, error, announcement_embed, bot_log
from bot.models import ProductModel, EmbedTracker, GuildSettings
from bot.utils import ch_name


class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def auto_setup(self, guild: discord.Guild):
        """Idempotent setup — creates missing, cleans duplicates, stores IDs."""
        changes = []
        role_map = {}

        # ── Roles ──────────────────────────────────────────────
        for name, data in ROLES.items():
            existing = [r for r in guild.roles if r.name == name]
            if len(existing) > 1:
                for r in existing[1:]:
                    await r.delete(reason="Vexa duplicate cleanup")
                changes.append(f"Cleaned duplicate role `{name}`")
                existing = [existing[0]]
            if existing:
                role_map[name] = existing[0]
            else:
                r = await guild.create_role(
                    name=name, color=discord.Color(data["color"]),
                    permissions=discord.Permissions(data["permissions"]),
                    hoist=data["hoist"], mentionable=data["mentionable"],
                    reason="Vexa setup"
                )
                role_map[name] = r
                changes.append(f"Created role `{name}`")

        # ── Categories & Channels ─────────────────────────────
        for idx, (cat_name, channels) in enumerate(CATEGORIES.items()):
            cats = [c for c in guild.categories if c.name == cat_name]
            if len(cats) > 1:
                for c in cats[1:]:
                    await c.delete(reason="Vexa duplicate cleanup")
                changes.append(f"Cleaned duplicate category `{cat_name}`")
                cats = [cats[0]]

            hidden = any(c[2].get("hidden") for c in channels)
            perms = {}
            if hidden:
                perms[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
                perms[guild.me] = discord.PermissionOverwrite(view_channel=True)

            if cats:
                cat = cats[0]
                await cat.edit(overwrites=perms)
            else:
                cat = await guild.create_category(cat_name, overwrites=perms, reason="Vexa setup")
                changes.append(f"Created category `{cat_name}`")
            await cat.edit(position=idx)

            for cname, chtype, copts in channels:
                lookup = cname.lower()
                matches = [c for c in cat.channels if c.name.lower() == lookup]
                if len(matches) > 1:
                    for c in matches[1:]:
                        await c.delete(reason="Vexa duplicate cleanup")
                    changes.append(f"Cleaned duplicate channel `{cname}`")
                    matches = [matches[0]]

                p = self._channel_perms(guild, role_map, copts)
                if matches:
                    ch = matches[0]
                    try:
                        await ch.edit(overwrites=p)
                    except:
                        pass
                else:
                    if chtype == "voice":
                        ch = await guild.create_voice_channel(
                            cname, category=cat, overwrites=p, reason="Vexa setup"
                        )
                    else:
                        ch = await guild.create_text_channel(
                            cname, category=cat, overwrites=p, reason="Vexa setup"
                        )
                    changes.append(f"Created channel `{cname}`")
                    # Store channel ID in guild_settings
                    key = f"ch_{cname.lower().replace(' ', '_').replace('・', '_')}"
                    await GuildSettings.set(key, ch.id)

        # Verification gate — restrict non-verified to #✅・verify only
        try:
            await self._setup_verification_gate(guild)
            changes.append("Verification gate configured.")
        except Exception as e:
            print(f"Verification gate error: {e}")

        # Log to bot-logs
        log_ch = discord.utils.get(guild.text_channels, name=ch_name("⚙️・bot-logs"))
        if log_ch and changes:
            await log_ch.send(embed=bot_log("🛠️ Auto-Setup", "\n".join(changes[:10])))

    def _channel_perms(self, guild, role_map, opts):
        p = {}
        if opts.get("admin_only"):
            ar = role_map.get("🛡️ Admin")
            p[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
            p[guild.me] = discord.PermissionOverwrite(view_channel=True)
            if ar:
                p[ar] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        elif opts.get("readonly"):
            p[guild.default_role] = discord.PermissionOverwrite(send_messages=False)
        elif opts.get("hidden"):
            p[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
            p[guild.me] = discord.PermissionOverwrite(view_channel=True)
        return p

    async def _setup_verification_gate(self, guild: discord.Guild):
        verify_role = guild.get_role(1513662326450950215)
        if not verify_role:
            verify_role = discord.utils.get(guild.roles, name="✦ VXM")
        if not verify_role:
            return

        verify_ch = discord.utils.get(guild.text_channels, name=ch_name("✅・verify"))

        for ch in guild.channels:
            if isinstance(ch, discord.CategoryChannel):
                continue
            if ch == verify_ch:
                await ch.set_permissions(guild.default_role, view_channel=True, send_messages=False)
            else:
                await ch.set_permissions(guild.default_role, overwrite=None)
                await ch.set_permissions(verify_role, view_channel=True)
                if isinstance(ch, discord.TextChannel):
                    await ch.set_permissions(verify_role, send_messages=True, read_message_history=True)

    async def _seed_content(self, guild: discord.Guild, force: bool = False):
        from bot.embeds import (rules_embed, pricing_embed, welcome_channel_embed,
                                voice_support_embed, support_chat_embed, flash_sale_embed)

        ch = discord.utils.get(guild.text_channels, name=ch_name("📌・rules"))
        if ch:
            if force:
                await EmbedTracker.refresh("rules", guild, ch_name("📌・rules"))
            if not await EmbedTracker.get("rules"):
                await self._send_once(ch, "rules", rules_embed())

        ch = discord.utils.get(guild.text_channels, name=ch_name("📢・announcements"))
        if ch:
            if force:
                await EmbedTracker.refresh("announcement", guild, ch_name("📢・announcements"))
            if not await EmbedTracker.get("announcement"):
                await self._send_once(ch, "announcement", announcement_embed(
                    "🚀 Vexa is Live!",
                    "Server is fully operational.\n• `/shop` — browse bots\n• `#🎫・create-ticket` — support\n• `/referral` — earn rewards",
                    "Vexa System"
                ))

        ch = discord.utils.get(guild.text_channels, name=ch_name("💰・pricing"))
        if ch:
            if force:
                await EmbedTracker.refresh("pricing", guild, ch_name("💰・pricing"))
            if not await EmbedTracker.get("pricing"):
                prods = await ProductModel.get_all()
                if prods:
                    await self._send_once(ch, "pricing", pricing_embed(prods))

        ch = discord.utils.get(guild.text_channels, name=ch_name("👋・welcome"))
        if ch:
            if force:
                await EmbedTracker.refresh("welcome", guild, ch_name("👋・welcome"))
            if not await EmbedTracker.get("welcome"):
                await self._send_once(ch, "welcome", welcome_channel_embed())

        ch = discord.utils.get(guild.text_channels, name=ch_name("🎧・voice-support"))
        if ch:
            if force:
                await EmbedTracker.refresh("voice_support", guild, ch_name("🎧・voice-support"))
            if not await EmbedTracker.get("voice_support"):
                await self._send_once(ch, "voice_support", voice_support_embed())

        ch = discord.utils.get(guild.text_channels, name=ch_name("💬・support-chat"))
        if ch:
            if force:
                await EmbedTracker.refresh("support_chat", guild, ch_name("💬・support-chat"))
            if not await EmbedTracker.get("support_chat"):
                await self._send_once(ch, "support_chat", support_chat_embed())

        ch = discord.utils.get(guild.text_channels, name=ch_name("🔥・flash-sales"))
        if ch:
            if force:
                await EmbedTracker.refresh("flash_sales", guild, ch_name("🔥・flash-sales"))
            if not await EmbedTracker.get("flash_sales"):
                product = await ProductModel.random()
                if product:
                    await self._send_once(ch, "flash_sales", flash_sale_embed(product))

    async def _send_once(self, channel, key: str, embed):
        msg = await channel.send(embed=embed)
        await EmbedTracker.set(key, msg.id)

    # ── Commands ──────────────────────────────────────────────

    @app_commands.command(name="setup", description="Create full server structure (owner only)")
    @app_commands.describe(mode="full = create missing, purge = delete all + recreate")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Full (create missing)", value="full"),
        app_commands.Choice(name="Purge (delete all + recreate)", value="purge"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_cmd(self, i: discord.Interaction, mode: str = "full"):
        if i.user.id != OWNER_ID:
            return await i.response.send_message(embed=error("Denied", "Owner only."), ephemeral=True)
        await i.response.defer(ephemeral=True)
        guild = i.guild

        if mode == "purge":
            await self._purge(guild)

        await self.auto_setup(guild)
        await i.followup.send(embed=success("Setup Complete", "All channels, categories, and roles are ready."), ephemeral=True)

    @app_commands.command(name="announce", description="Post an announcement (owner only)")
    @app_commands.describe(title="Title", message="Content")
    async def announce(self, i: discord.Interaction, title: str, message: str):
        if i.user.id != OWNER_ID:
            return await i.response.send_message(embed=error("Denied", "Owner only."), ephemeral=True)
        ch = discord.utils.get(i.guild.text_channels, name=ch_name("📢・announcements"))
        if not ch:
            return await i.response.send_message(embed=error("Not Found", "Announcements channel not found."), ephemeral=True)
        await ch.send(embed=announcement_embed(title, message, i.user.display_name))
        await i.response.send_message(embed=success("Posted", f"Sent to {ch.mention}"), ephemeral=True)

    async def _purge(self, guild: discord.Guild):
        d = 0
        for ch in guild.channels:
            try:
                await ch.delete(reason="Vexa purge")
                d += 1
            except:
                pass
        for cat in guild.categories:
            try:
                await cat.delete(reason="Vexa purge")
                d += 1
            except:
                pass
        for key in ["rules", "announcement", "pricing", "verify_panel", "ticket_panel",
                     "welcome", "voice_support", "support_chat", "flash_sales"]:
            await EmbedTracker.delete(key)
        print(f"Purge: deleted {d} channels/categories")


async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))
