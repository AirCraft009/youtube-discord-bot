import discord
from discord.ext import commands
from discord import app_commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
import asyncio
import os

class MusicBot(commands.Bot):
    def __init__(self, command_prefix, intents, guild_id):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.guild_id = guild_id  # Store the guild ID
        self.music_queue = []
        self.is_playing = False
        self.vc = None
        self.FFMPEG_OPTIONS = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}
        self.ytdl = YoutubeDL({"format": "bestaudio", "quiet": True})
        self.previous = []

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        guild = discord.Object(id=self.guild_id)
        try:
            synced = await self.tree.sync(guild=guild)  # Sync commands to the guild
            print(f"Synced {len(synced)} commands to the server {self.guild_id}.")
        except Exception as e:
            print(f"An error occurred during syncing: {e}")
        print("something else happened")

    def search_yt(self, query):
        try:
            if query.startswith("https://"):
                info = self.ytdl.extract_info(query, download=False)
                return {"source": query, "title": info.get("title", "Unknown")}
            else:
                search = VideosSearch(query, limit=1)
                result = search.result()["result"][0]
                return {"source": result["link"], "title": result["title"]}
        except Exception as e:
            print(f"Error in search_yt: {e}")
            return None

    async def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue.pop(0)["source"]
            self.previous.append(m_url)
            try:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(m_url, download=False))
                song = data["url"]
                self.vc.play(discord.FFmpegPCMAudio(song, **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.loop))
            except Exception as e:
                print(f"Error in play_next: {e}")
                self.is_playing = False
        else:
            self.is_playing = False
            
    async def play_previous(self):
        if len(self.previous)  > 0:
            self.is_playing = True
            n_url = self.previous.pop(len(self.previous)-1)
            try:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(n_url, download=False))
                song = data["url"]
                self.vc.play(discord.FFmpegPCMAudio(song, **self.FFMPEG_OPTIONS), after= lambda e: asyncio.run_coroutine_threadsafe(self.play_previous(), self.loop))
            except Exception as e:
                print(f"Error in play_previous: {e}")
                self.is_playing = False
                
            else:
                 self.is_playing = False
                 
                 
    async def play_music(self, interaction, music):
        if not music:
            await interaction.response.send_message("Failed to find the song. Please try again.")
            return

        self.music_queue.append(music)

        if not self.is_playing:
            self.is_playing = True
            channel = interaction.user.voice.channel

            if self.vc is None or not self.vc.is_connected():
                self.vc = await channel.connect()
            await self.play_next()
            
    async def play_music_prev(self, interaction):
        if not self.is_playing:
            self.is_playing = True
            channel = interaction.user.voice.channel

            if self.vc is None or not self.vc.is_connected():
                self.vc = await channel.connect()
            await self.play_previous()
            
# Bot setup
GUILD_ID = discord.Object(id=982378999529484288)  # Replace with your actual guild ID
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Set your bot token as an environment variable

intents = discord.Intents.default()
intents.message_content = True
bot = MusicBot(command_prefix="^", intents=intents, guild_id=982378999529484288)

@bot.tree.command(name="play", description="Play music from YouTube", guild= GUILD_ID)
async def play(interaction: discord.Interaction, query: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("You must be in a voice channel to use this command.")
        return 0

    music = bot.search_yt(query)
    if music:
        # await interaction.response.send_message(f"Added to queue: {music['title']}")
        await bot.play_music(interaction, music)
        await interaction.response.send_message("playing")
    else:
        await interaction.response.send_message("Could not find the song. Please try again.")

@bot.tree.command(name="skip", description="Skip the current song", guild= GUILD_ID)
async def skip(interaction: discord.Interaction):
    if bot.vc and bot.vc.is_playing():
        bot.vc.stop()
        await interaction.response.send_message("Skipped the current song.")
    else:
        await interaction.response.send_message("No song is currently playing.")
        
@bot.tree.command(name="back", description="play the previous song", guild=GUILD_ID)
async def back(interaction: discord.Interaction):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("Must be in a voice channel")
        return 0
    else:
        await bot.play_music_prev(interaction=interaction)
    
        
@bot.tree.command(name="leave", description="leaves the vc", guild= GUILD_ID)
async def leave(interaction: discord.Interaction):
    if bot.vc != None:
        await interaction.guild.voice_client.disconnect()
        bot.vc = None
    else:
        await interaction.response.send_message("JP ist nicht in einem VC")


"""       
@bot.tree.command(name="loooooow", description="you know what else is massive", guild= GUILD_ID)
async def low_embed(interaction: discord.Interaction):
    embed = discord.Embed(title= "low taper fade", url="https://www.youtube.com/watch?v=ryNMM5pMPr0", color=discord.Color.red())
    embed.set_thumbnail(url="https://i.kym-cdn.com/photos/images/newsfeed/002/735/702/1e5.jpeg")
    
    """

bot.run("MTMyMDc0Nzc1MjY1NjczMjE2Mg.GMcjbz.LrB1m-AOJ8xqmUpzsqnVtC0yghcDQXstrHjNUE")

 

# bot.run("MTMyMDc0Nzc1MjY1NjczMjE2Mg.GMcjbz.LrB1m-AOJ8xqmUpzsqnVtC0yghcDQXstrHjNUE")


