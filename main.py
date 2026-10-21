import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import urllib.request
import urllib.parse
import json
import re

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

def search_youtube(query):
    try:
        # البحث الآمن عن الفيديو بدون أخطاء يوتيوب أو الحظر
        query_string = urllib.parse.urlencode({'search_query': query})
        html_content = urllib.request.urlopen(f"https://www.youtube.com/results?{query_string}")
        search_results = re.findall(r'/watch\?v=(.{11})', html_content.read().decode())
        if search_results:
            video_id = search_results[0]
            return f"https://www.youtube.com/watch?v={video_id}"
    except Exception:
        pass
    return None

@bot.tree.command(name="play", description="Play a song from YouTube")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.send_message(f"🔍 Searching: `{query}`...")
    
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
        url = query
        if not query.startswith("http"):
            url = search_youtube(query)
            if not url:
                await interaction.edit_original_response(content="❌ لم يتم العثور على مقطع مطابق.")
                return

        import yt_dlp
        ytdl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'extractor_args': {'youtube': {'player_client': ['android']}},
        }
        
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
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
        await interaction.edit_original_response(content=f"Error: تعذر تشغيل المقطع، جرب اسماً آخر.")

TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
