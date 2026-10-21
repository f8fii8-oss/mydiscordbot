import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import yt_dlp

app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name}")

@bot.tree.command(name="join", description="Join voice channel")
async def join(interaction: discord.Interaction):
    await interaction.response.defer()
    if interaction.user.voice and interaction.user.voice.channel:
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        await interaction.followup.send(f"Joined {channel.name}")
    else:
        await interaction.followup.send("You must be in a voice channel first.")

@bot.tree.command(name="play", description="Play audio from URL or search")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.send_message(f"🔍 Loading: `{query}`...")
    
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.edit_original_response(content="You must be in a voice channel first.")
        return

    channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    try:
        # إذا كان الرابط مباشر لملف صوتي (.mp3 أو غيره) شغله فوراً بدون يوتيوب
        if query.startswith("http") and not ("youtube.com" in query or "youtu.be" in query):
            audio_url = query
            title = "Direct Audio Link"
        else:
            # البحث عبر yt-dlp مع تجاوز الحظر
            ytdl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'default_search': 'ytsearch',
                'extractor_args': {'youtube': {'player_client': ['android']}},
            }
            
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                audio_url = info['url']
                title = info.get('title', 'Audio')

        if voice_client.is_playing():
            voice_client.stop()

        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        audio_source = discord.FFmpegPCMAudio(audio_url, executable="ffmpeg", **ffmpeg_options)
        voice_client.play(audio_source)
        
        await interaction.edit_original_response(content=f"🎶 Now playing: **{title}**")
    except Exception as e:
        await interaction.edit_original_response(content=f"Error: حدث خطأ في تشغيل المقطع، جرب رابط مباشر أو اسم آخر.")

TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
