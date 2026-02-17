import discord
from discord.ext import commands
import time
import random
from discord.ext import tasks
import datetime

# ================= TOKEN =================

# ================= CONFIG =================
LOG_CHANNEL_ID = 1470417750319960168

ROLE_ID = 1069133664362963045  # บทบาทแชร์ดิส
CHANNEL_ID = 1472149753826377780  # ห้องแจ้งแชร์สำเร็จ
STICKY_CHANNEL_ID = 1227127117519519764 # ข้อความปักหมุดห้องส่งหลักฐาน

# ระบบรับยศยืนยัน (เพิ่มใหม่)
CONFIRM_ROLE_ID = 1049292011997503498 # ยศ Member
CONFIRM_CHANNEL_ID = 1472547979641749690

# ระบบซื้อยศสำเร็จ
SUCCESS_CHANNEL_ID = 1470997698004914197
ROLE_1_ID = 1082885961953853540
ROLE_2_ID = 1082668970718527508
ROLE_3_ID = 1082667309254054008
ROLE_4_ID = 1082667313163157515

# ระบบส่งข้อความทุกๆ 1 ชั่วโมง
LOOP_CHANNEL_ID = 1470417750319960168

EMBED_COLOR = 0x00ff88

# ================= INTENTS =================
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

cooldown = {}
sticky_messages = {}

# ================= READY =================
@bot.event
async def on_ready():
    bot.add_view(ConfirmRoleView())
    if not hourly_loop.is_running():
        hourly_loop.start()
    print(f"🤖 Logged in as {bot.user}")

# ==================================================

def create_base_embed(title, member):
    embed = discord.Embed(
        title=title,
        color=0x00ff00
    )

    embed.set_author(
        name=member.display_name,
        icon_url=member.display_avatar.url
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    return embed

# ==================================================

async def send_share_success(member: discord.Member, role: discord.Role):

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        return

    giver = None
    async for entry in member.guild.audit_logs(
        limit=5,
        action=discord.AuditLogAction.member_role_update
    ):
        if entry.target.id == member.id:
            giver = entry.user
            break

    status_messages = [
        "🎀 เย้! คุณได้แชร์สำเร็จแล้ว~",
        "💖 ขอบคุณที่แชร์ดิสนะ!",
        "🌟 แชร์เก่งมากเลย!",
        "✨ ได้รับยศเรียบร้อยแล้ว!",
        "🎉 สำเร็จแล้ว! ขอบคุณมากนะ~"
    ]

    random_status = random.choice(status_messages)

    embed = create_base_embed(
        "<a:Verify:1145246019668418620>  __แชร์สำเร็จเรียบร้อยแล้ว!__  <a:bell_2:1472134346449354844>",
        member
    )

    embed.add_field(
        name=" ",
        value=f"`👤 ผู้ใช้ :` {member.mention}",
        inline=False
    )

    embed.add_field(
        name=" ",
        value=f"`🏅 ได้รับยศ :` {role.mention}",
        inline=False
    )

    if giver:
        embed.add_field(
            name=" ",
            value=f"`👮 ให้โดย :` {giver.mention}",
            inline=False
        )

        embed.add_field(
            name=" ",
            value=f" ",
            inline=False
        )

    # 🔥 รวมสถานะในกรอบดำเดียว
    embed.add_field(
        name=" ",
        value=f"```🟢 สถานะแชร์ดิส : {random_status}```",
        inline=False
    )

    embed.set_image(
        url="https://i.postimg.cc/8PjM2Y45/rainbow-water-falling.gif"
    )

    embed.timestamp = discord.utils.utcnow()

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")

# ==================================================
# 1️⃣ ระบบอั่งเปา (ของเดิมคุณครบ)
# ==================================================

class AngpaoModal(discord.ui.Modal, title="ส่งลิงก์อั่งเปา"):
    link = discord.ui.TextInput(
        label="ลิงก์ซองอั่งเปา",
        placeholder="https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):

        if not self.link.value.startswith("https://gift.truemoney.com/"):
            await interaction.response.send_message(
                "❌ ลิงก์ไม่ถูกต้อง",
                ephemeral=True
            )
            return

        cooldown[interaction.user.id] = time.time()
        log_channel = await bot.fetch_channel(LOG_CHANNEL_ID)

        embed = discord.Embed(
            title="🧧 มีการส่งลิงก์อั่งเปา ",
            color=0x00ff99
        )

        embed.add_field(name="ผู้ส่ง", value=interaction.user.mention)
        embed.add_field(name="เซิร์ฟเวอร์", value=interaction.guild.name)
        embed.add_field(name="ลิงก์", value=self.link.value)

        await log_channel.send(
            content=f"📢 แจ้งเตือนถึง <@848068744303083551>",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=True)
        )

        await interaction.response.send_message(
            "✅ ส่งซองอั่งเปาเรียบร้อยแล้ว",
            ephemeral=True
        )

class MainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🧧 ส่งลิงก์อั่งเปา", style=discord.ButtonStyle.green)
    async def send_angpao(self, interaction: discord.Interaction, _):

        user_id = interaction.user.id
        now = time.time()

        if user_id in cooldown and now - cooldown[user_id] < 10:
            await interaction.response.send_message(
                "⏱️ กรุณารอ 10 วินาทีก่อนส่งใหม่",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(AngpaoModal())

    @discord.ui.button(label="🛒 ดูราคายศ", style=discord.ButtonStyle.gray)
    async def rank_info(self, interaction: discord.Interaction, _):

        embed = discord.Embed(
            title="🛒 รายละเอียดราคายศ 🔻",
            description=(
                "<@&1082885961953853540>\n"
                "• ราคายศรวมทั้งหมด : __**100฿**__ *(คุ้มกว่า!)* 🔥 🔥 🔥\n\n"
                "<@&1082668970718527508>\n"
                "• ตัวอย่างห้อง: <#1051070486500626502>\n"
                "• ราคายศ : __**79฿**__\n\n"
                "<@&1082667309254054008>\n"
                "• ตัวอย่างห้อง: <#1064082990990381127>\n"
                "• ราคายศ : __**40฿**__\n\n"
                "<@&1082667313163157515>\n"
                "• ตัวอย่างห้อง: <#1049681634728869949>\n"
                "• ราคายศ : __**20฿**__"
            ),
            color=0xFFD700
        )

        embed.set_footer(text="🧧 ชำระผ่านซองอั่งเปา TrueWallet เท่านั้น")

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

@bot.command()
async def setup(ctx):

    embed = discord.Embed(
        title="🧧 ซื้อยศด้วยซองอั่งเปา __TrueWallet !__",
        description="* ใส่จำนวนเงินในซองตามราคายศที่กำหนด",
        color=0xffc0cb
    )

    embed.set_image(url="https://i.postimg.cc/9FqtF8fq/aungpao-truewallet-01.png")

    embed.set_footer(
        text=" ชำระผ่านซองอั่งเปา TrueWallet 24ชม.",
        icon_url="https://i.postimg.cc/c6GHg5YB/image.png"
    )

    await ctx.send(embed=embed, view=MainView())

# ==================================================
# 2️⃣ ระบบแชร์ดิส (ครบสุ่มข้อความ + embed เดิมคุณ)
# ==================================================

@bot.event
async def on_member_update(before, after):

    added_roles = [r for r in after.roles if r not in before.roles]

    if not added_roles:
        return

    for role in added_roles:

        # ระบบแชร์
        if role.id == ROLE_ID:
            await send_share_success(after, role)

        # ระบบซื้อยศ
        elif role.id in [ROLE_1_ID, ROLE_2_ID, ROLE_3_ID, ROLE_4_ID]:
            await send_purchase_success(after, role, after)

# ================= STICKY SYSTEM =================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id == STICKY_CHANNEL_ID:

        old_message = sticky_messages.get(message.channel.id)

        if old_message:
            try:
                await old_message.delete()
            except discord.HTTPException:
                pass

        sticky_embed = discord.Embed(
            title=" <a:loading_1:1145245426304417823> ส่งหลักฐานการแชร์ได้ที่นี่ <a:star_1:1472134208993497202>",
            description=" ``` โปรดรอแอดมินตรวจสอบหลักฐานสักครู่ 💖```",
            color=0xff66cc
        )

        new_message = await message.channel.send(embed=sticky_embed)
        sticky_messages[message.channel.id] = new_message

    await bot.process_commands(message)

# ================= ระบบให้ยศซื้อสำเร็จ =================

async def send_purchase_success(member: discord.Member, role: discord.Role, giver: discord.Member):
    channel = bot.get_channel(SUCCESS_CHANNEL_ID)
    if channel is None:
        return

    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    embed = create_base_embed(
        "<a:correct3:1472134441248751788>  __ซื้อยศสำเร็จเรียบร้อยแล้ว!__  <a:bell_2:1472134346449354844>",
        member
    )

    embed.add_field(
        name=" ",
        value=f"`👤 ผู้ใช้ :` {member.mention}",
        inline=False
    )

    embed.add_field(
        name=" ",
        value=f"`🏅 ได้รับยศ :` {role.mention}",
        inline=False
    )

    embed.add_field(
        name=" ",
        value=f"`👮 ให้โดย :` {giver.mention}",
        inline=False
    )

    embed.add_field(
        name=" ",
        value=f" ",
        inline=False
    )

    embed.set_image(
        url="https://i.postimg.cc/3JkfNzdk/standard.gif"
    )

    # 👇 Footer เป็นโปรไฟล์เซิร์ฟ + ชื่อ + เวลา
    guild = member.guild
    embed.set_footer(
        text=f"{guild.name} • {now}",
        icon_url=guild.icon.url if guild.icon else None
    )

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")

# ==================================================
# 3️⃣ ระบบรับยศยืนยัน (เพิ่มใหม่)
# ==================================================

class ConfirmRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="กดรับยศ",
        style=discord.ButtonStyle.success,
        custom_id="confirm_role_button_v2",
        emoji=discord.PartialEmoji(
            name="correct_2",
            id=1472134441248751788
        )
    )
    async def confirm_role(self, interaction: discord.Interaction, _):

        if interaction.channel.id != CONFIRM_CHANNEL_ID:
            await interaction.response.send_message(
                "❌ กดได้เฉพาะห้องที่กำหนด",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(CONFIRM_ROLE_ID)

        if role is None:
            await interaction.response.send_message(
                "❌ ไม่พบบทบาท",
                ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "❌ คุณกดรับยศนี้ไปแล้ว",
                ephemeral=True
            )
            return

        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"✅ คุณได้รับยศ {role.mention} เรียบร้อยแล้ว",
            ephemeral=True
        )

@bot.command()
async def test(ctx):

    if ctx.channel.id != CONFIRM_CHANNEL_ID:
        return

    embed = discord.Embed(
        title="กดที่อีโมจิ  <a:correct_2:1472134441248751788>  เพื่อรับยศสมาชิก <a:gift_1:1472607090705961041> ",
        description=" <a:star_1:1472134208993497202> กดปุ่มด้านล่างเพื่อรับยศ <@&1049292011997503498>  <a:star_1:1472134208993497202> ",
        color=0xFF0000  # สีแดง

    )
    embed.set_image(
        url="https://i.postimg.cc/Cx4ybpLQ/standard.gif"
    )

    embed.set_footer(
        text=" ! เซิร์ฟนี้มีระบบซื้อยศผ่านซองอั่งเปา TrueWallet ตลอด 24ชม.",
        icon_url="https://i.postimg.cc/CM8jvhy7/DOHEE-icon-png.png"
    )

    await ctx.send(embed=embed, view=ConfirmRoleView())

# ================= ระบบส่งข้อความทุกๆ 1 ชั่วโมง =================

@bot.command()
async def testloop(ctx):
    await ctx.send("ทดสอบระบบลูป...")
    await hourly_loop()

last_messages = []

@tasks.loop(minutes=1)
async def hourly_loop():

    now = datetime.datetime.now()

    # เช็คว่าเป็นต้นชั่วโมงไหม (นาที = 0)
    if now.minute != 0:
        return

    channel = bot.get_channel(LOOP_CHANNEL_ID)
    if channel is None:
        return

    global last_messages

    # ลบข้อความเก่า
    for msg in last_messages:
        try:
            await msg.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            pass

    last_messages = []

    # ข้อความที่ 1
    msg1 = await channel.send("""
    # <a:star_1:1472134208993497202> วิธีการซื้อ <a:star_1:1472134208993497202>
    ### <a:correct2:1472846699495034981> ขั้นตอนที่ 1 : เข้า "__TrueWallet__" กดสร้างซองอั่งเปาใส่ราคาตามยศนั้นๆ <:truewallet:1472134849019248782>
    ### <a:correct2:1472846699495034981> ขั้นตอนที่ 2 : นำลิงก์ซองอั่งเปามาใส่ใน "__ส่งลิงก์อั่งเปา__" ได้เลยครับ! <a:angpao:1472134389763932350>
    > **<a:flower8:1472928911594885142> เช็คการซื้อยศสำเร็จได้ที่ <a:flower8:1472928911594885142>**
    ** <a:correct3:1472134441248751788> <#1470997698004914197> <a:vip1:1472132052026527754>**
    ||@everyone|| ||@everyone||
    """)

    # ข้อความที่ 2 (รูป GIF 1 รูป)
    gif1 = await channel.send("https://i.postimg.cc/7Lt8PrZM/rainbow-water-falling.gif")

    last_messages = [msg1, gif1]

# ================= RUN =================
bot.run(TOKEN)
