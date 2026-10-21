# -*- coding: utf-8 -*-
from flask import Flask
from threading import Thread
import os
import discord
from discord.ext import commands
import yt_dlp

app = Flask('')

@app.route('/')
def home():
    return "Music Bot is alive and running!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

class PureMusicBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("تمت مزامنة أوامر الموسيقى بنجاح!")

    async def on_ready(self):
        print(f"بوت الأغاني شغال الآن باسم {self.user}")

bot = PureMusicBot()

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

@bot.tree.command(name="join", description="دخول البوت للروم الصوتي")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("⚠️ يجب أن تكون بروم صوتي!", ephemeral=True)
        return
    channel = interaction.user.voice.channel
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
    else:
        await channel.connect()
    await interaction.response.send_message(f"✅ تم الانضمام إلى **{channel.name}**", ephemeral=True)

@bot.tree.command(name="play", description="تشغيل أغنية عبر رابط يوتيوب")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    if not interaction.user.voice:
        await interaction.followup.send("⚠️ يجب أن تكون بروم صوتي!")
        return
    channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client
    if not voice_client:
        voice_client = await channel.connect()
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']
            title = info.get('title', 'مقطع صوتي')
        if voice_client.is_playing():
            voice_client.stop()
        source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS)
        voice_client.play(source)
        await interaction.followup.send(f"🎵 جاري تشغيل: **{title}**")
    except Exception as e:
        await interaction.followup.send("❌ حدث خطأ أثناء تشغيل الرابط.")

@bot.tree.command(name="stop", description="إيقاف الأغنية وإخراج البوت")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("⏹️ تم إيقاف الأغنية ومغادرة الروم الصوتي.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ البوت ليس في أي روم صوتي حالياً.", ephemeral=True)

token = os.getenv('DISCORD_TOKEN') or os.getenv('TOKEN')
bot.run(token)
