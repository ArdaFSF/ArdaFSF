import discord
from discord.ext import commands
from discord import app_commands
from sms import SendSms
import asyncio
import threading
import time
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Sms servis metodlarını listele
servisler_sms = []
for attribute in dir(SendSms):
    attribute_value = getattr(SendSms, attribute)
    if callable(attribute_value) and not attribute.startswith("__"):
        servisler_sms.append(attribute)

PREMIUM_ROLE_ID = 1378504273083633785
ALLOWED_CHANNELS = [1378504347976990830, 1378526060718592020]
TICKET_ALLOWED_ROLE_ID = 1378504271083077642
TICKET_CATEGORY_ID = 1378650450605248542
aktif_gonderimler = {}


@bot.event
async def on_ready():
    print(f'{bot.user} Aktif!')
    try:
        synced = await bot.tree.sync()
        print(f"Slash komutları senkronize edildi: {len(synced)} komut.")
    except Exception as e:
        print(f"Slash komut senkronizasyon hatası: {e}")


async def turbo(interaction: discord.Interaction, telefon: str, sayi: int):
    user_id = interaction.user.id

    if user_id in aktif_gonderimler:
        await interaction.response.send_message(
            "🛑 Zaten bir gönderiminiz aktif!", ephemeral=False)
        msg = await interaction.original_response()
        await asyncio.sleep(5)
        await msg.delete()
        return

    if len(telefon) != 10 or not telefon.isdigit():
        await interaction.response.send_message("🛑 Telefon numarası geçersiz!",
                                                ephemeral=False)
        msg = await interaction.original_response()
        await asyncio.sleep(5)
        await msg.delete()
        return

    if sayi <= 0:
        await interaction.response.send_message("🛑 SMS sayısı pozitif olmalı!",
                                                ephemeral=False)
        msg = await interaction.original_response()
        await asyncio.sleep(5)
        await msg.delete()
        return

    member = interaction.guild.get_member(user_id)
    has_premium = PREMIUM_ROLE_ID in [role.id for role in member.roles]

    if not has_premium and sayi > 40:
        await interaction.response.send_message(
            f"🛑 <@&{PREMIUM_ROLE_ID}> üyesi değilsiniz. Max 40 SMS!",
            ephemeral=False)
        msg = await interaction.original_response()
        await asyncio.sleep(5)
        await msg.delete()
        return

    embed_start = discord.Embed(title="discord.gg/yakında",
                                color=discord.Color.purple())
    embed_start.add_field(name="📶 Durum",
                          value="Gönderiliyor...",
                          inline=False)
    embed_start.add_field(name="👤 Gönderen",
                          value=f"{interaction.user.mention}",
                          inline=True)
    embed_start.add_field(name="💣 Miktar", value=f"{sayi}", inline=True)
    embed_start.add_field(
        name="⭐ Üyelik",
        value=f"<@&{PREMIUM_ROLE_ID}>" if has_premium else "Free",
        inline=True)
    embed_start.add_field(name="⏳ Kalan Üyelik Süresi",
                          value="Sınırsız",
                          inline=True)
    embed_start.set_image(url="https://i.postimg.cc/FH8x5Y1w/Sms.png")
    embed_start.set_footer(text="Made by scher4851 | discord.gg/yakında")

    await interaction.response.send_message(embed=embed_start)
    msg = await interaction.original_response()

    def turbo_gonder():
        sms = SendSms(telefon, "")
        sent_count = 0

        while sent_count < sayi:
            for servis in servisler_sms:
                if sent_count >= sayi:
                    break
                try:
                    result = getattr(sms, servis)()
                    if result:  # Başarılı ise say
                        sent_count += 1
                    time.sleep(0.01)
                except Exception:
                    pass

        aktif_gonderimler.pop(user_id, None)

        embed_done = discord.Embed(title="discord.gg/yakında",
                                   color=discord.Color.purple())
        embed_done.add_field(name="📶 Durum", value="Gönderildi", inline=False)
        embed_done.add_field(name="👤 Gönderen",
                             value=f"{interaction.user.mention}",
                             inline=True)
        embed_done.add_field(name="💣 Miktar", value=f"{sayi}", inline=True)
        embed_done.add_field(
            name="⭐ Üyelik",
            value=f"<@&{PREMIUM_ROLE_ID}>" if has_premium else "Free",
            inline=True)
        embed_done.add_field(name="⏳ Kalan Üyelik Süresi",
                             value="Sınırsız",
                             inline=True)
        embed_done.set_image(url="https://i.postimg.cc/FH8x5Y1w/Sms.png")
        embed_done.set_footer(text="Made by scher4851 | discord.gg/yakında")

        async def mesaj_sil():
            try:
                await msg.edit(embed=embed_done)
                await asyncio.sleep(10)
                await msg.delete()
            except Exception:
                pass

        asyncio.run_coroutine_threadsafe(mesaj_sil(), bot.loop)

    thread = threading.Thread(target=turbo_gonder, daemon=True)
    aktif_gonderimler[user_id] = thread
    thread.start()


@bot.tree.command(name="sms", description="Turbo SMS gönderimini başlatır.")
@app_commands.describe(telefon="Telefon numarası (10 haneli)",
                       sayi="Gönderilecek SMS sayısı")
async def slash_turbo(interaction: discord.Interaction, telefon: str,
                      sayi: int):
    if interaction.channel.id not in ALLOWED_CHANNELS:
        await interaction.response.send_message(
            "🛑 Bu komutu sadece belirli kanallarda kullanabilirsin.",
            ephemeral=True)
        return

    await turbo(interaction, telefon, sayi)


class TicketResponseButtons(discord.ui.View):

    def __init__(self, label: str, ticket_owner: discord.Member):
        super().__init__(timeout=None)
        self.label = label
        self.ticket_owner = ticket_owner

        if label.lower() == "satın alım":
            self.add_item(self.SatinAlindiButton(self))
            self.add_item(self.SatinAlinmadiButton(self))
        else:
            self.add_item(self.OnaylandiButton(self))
            self.add_item(self.OnaylanmadiButton(self))

    async def interaction_check(self,
                                interaction: discord.Interaction) -> bool:
        has_permission = any(role.id == TICKET_ALLOWED_ROLE_ID
                             for role in interaction.user.roles)
        if not has_permission:
            await interaction.response.send_message(
                "❌ Bu butona tıklamak için yetkin yok!", ephemeral=True)
            return False
        return True

    class SatinAlindiButton(discord.ui.Button):

        def __init__(self, parent):
            super().__init__(label="Satın Alındı",
                             style=discord.ButtonStyle.gray,
                             custom_id="satinalindi")
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message(
                "✅ Satın alım tamamlandı olarak işaretlendi.", ephemeral=True)
            # Buraya istersen log kanalı bildirimi koyabilirsin

    class SatinAlinmadiButton(discord.ui.Button):

        def __init__(self, parent):
            super().__init__(label="Satın Alınmadı",
                             style=discord.ButtonStyle.gray,
                             custom_id="satinalinmadi")
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message(
                "❌ Satın alım tamamlanmadı olarak işaretlendi.",
                ephemeral=True)
            # Buraya istersen log kanalı bildirimi koyabilirsin

    class OnaylandiButton(discord.ui.Button):

        def __init__(self, parent):
            super().__init__(label="Onaylandı",
                             style=discord.ButtonStyle.gray,
                             custom_id="onaylandi")
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message("✅ Talep onaylandı.",
                                                    ephemeral=True)
            await self.send_log(interaction, approved=True)

        async def send_log(self, interaction: discord.Interaction,
                           approved: bool):
            log_channel_id = 1378504325571022880
            guild = interaction.guild
            log_channel = guild.get_channel(log_channel_id)
            if not log_channel:
                return

            embed = discord.Embed(title="🎫 Ticket Onay Durumu",
                                  color=discord.Color.green()
                                  if approved else discord.Color.red(),
                                  timestamp=discord.utils.utcnow())
            embed.add_field(
                name="Ticket Sahibi",
                value=
                f"{self.parent.ticket_owner.mention} ({self.parent.ticket_owner})",
                inline=False)
            embed.add_field(name="Talep Türü",
                            value=self.parent.label,
                            inline=False)
            embed.add_field(name="Durum", value="Onaylandı ✅", inline=False)
            embed.add_field(name="Onaylayan Yetkili",
                            value=interaction.user.mention,
                            inline=False)
            embed.set_footer(text="Made by scher4851")

            await log_channel.send(embed=embed)

    class OnaylanmadiButton(discord.ui.Button):

        def __init__(self, parent):
            super().__init__(label="Onaylanmadı",
                             style=discord.ButtonStyle.gray,
                             custom_id="onaylanmadi")
            self.parent = parent

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message("❌ Talep onaylanmadı.",
                                                    ephemeral=True)
            await self.send_log(interaction, approved=False)

        async def send_log(self, interaction: discord.Interaction,
                           approved: bool):
            log_channel_id = 1378504325571022880
            guild = interaction.guild
            log_channel = guild.get_channel(log_channel_id)
            if not log_channel:
                return

            embed = discord.Embed(title="🎫 Ticket Onay Durumu",
                                  color=discord.Color.red()
                                  if not approved else discord.Color.green(),
                                  timestamp=discord.utils.utcnow())
            embed.add_field(
                name="Ticket Sahibi",
                value=
                f"{self.parent.ticket_owner.mention} ({self.parent.ticket_owner})",
                inline=False)
            embed.add_field(name="Talep Türü",
                            value=self.parent.label,
                            inline=False)
            embed.add_field(name="Durum", value="Onaylanmadı ❌", inline=False)
            embed.add_field(name="Onaylayan Yetkili",
                            value=interaction.user.mention,
                            inline=False)
            embed.set_footer(text="Made by scher4851")

            await log_channel.send(embed=embed)


class TicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket_channel(self, interaction: discord.Interaction,
                                    category_id: int, label: str):
        try:
            category = await interaction.guild.fetch_channel(category_id)
        except discord.NotFound:
            await interaction.response.send_message("❌ Kategori bulunamadı.",
                                                    ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Bu kategoriye erişim iznim yok.", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"❌ Beklenmeyen hata: {e}",
                                                    ephemeral=True)
            return

        overwrites = {
            interaction.guild.default_role:
            discord.PermissionOverwrite(view_channel=False),
            interaction.user:
            discord.PermissionOverwrite(view_channel=True,
                                        send_messages=True,
                                        read_messages=True),
        }

        channel_name = f"{interaction.user.name}-{label}".lower().replace(
            " ", "-")

        existing_channel = discord.utils.get(category.channels,
                                             name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"Zaten aynı isimde bir ticket kanalınız var: {existing_channel.mention}",
                ephemeral=True)
            return

        ticket_channel = await category.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            topic=f"{interaction.user} - {label} talebi")

        embed = discord.Embed(
            title="🎟️ Ticket Açıldı",
            description=
            f"Merhaba {interaction.user.mention}, **{label}** talebiniz alındı. En kısa sürede ilgilenilecektir!",
            color=discord.Color.green())
        embed.set_footer(text="Made by: scher4851")

        view = TicketResponseButtons(label=label)

        await ticket_channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            f"✅ Ticket oluşturuldu: {ticket_channel.mention}", ephemeral=True)

    @discord.ui.button(label="Satın Alım",
                       style=discord.ButtonStyle.secondary,
                       custom_id="ticket_buy")
    async def buy_button(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
        await self.create_ticket_channel(interaction, TICKET_CATEGORY_ID,
                                         "Satın Alım")

    @discord.ui.button(label="Destek",
                       style=discord.ButtonStyle.secondary,
                       custom_id="ticket_support")
    async def support_button(self, interaction: discord.Interaction,
                             button: discord.ui.Button):
        await self.create_ticket_channel(interaction, TICKET_CATEGORY_ID,
                                         "Destek")

    @discord.ui.button(label="Hata Bug",
                       style=discord.ButtonStyle.secondary,
                       custom_id="ticket_bug")
    async def bug_button(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
        await self.create_ticket_channel(interaction, TICKET_CATEGORY_ID,
                                         "Hata Bug")


@bot.tree.command(name="ticket", description="Destek ticket sistemi.")
async def ticket(interaction: discord.Interaction):
    member = interaction.guild.get_member(interaction.user.id)
    if TICKET_ALLOWED_ROLE_ID not in [role.id for role in member.roles]:
        await interaction.response.send_message(
            "🛑 Bu komutu kullanmak için izniniz yok!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎟️ Ticket Açıldı",
        description=
        f"Merhaba {interaction.user.mention}, en kısa sürede yetkililer ilgilenecektir!",
        color=discord.Color.green())
    embed.set_footer(text="Made by: scher4851")

    view = TicketView()
    await interaction.response.send_message(embed=embed,
                                            view=view,
                                            ephemeral=False)


keep_alive()
Token = "MTM3MjE4NTE5ODQ5MzcwMDIwNw.G5xdJt.pxlNwyMS9YWQmUjNO9sUyeXgF9wG69joVsgXzU"
bot.run(Token)
