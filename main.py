import discord
import asyncio
import websockets
import authDeets
import time
from discord.ext import commands
import random
#import logging
import youtube_dl
import csv
from threading import Timer
from datetime import datetime
#from checks import embed_perms, cmd_prefix_len

description = '''BunBot Help'''
client = commands.Bot(command_prefix='-', description=description)
bot = client
version = 'Version: 1.0' 

@client.event
async def on_ready():
    print("Logged in as: {0}, with the ID of: {1}".format(client.user, client.user.id))
    await client.change_presence(game=discord.Game(name='in the meadow'))
    print("--")

    if not discord.opus.is_loaded():
        # the 'opus' library here is opus.dll on windows
        # or libopus.so on linux in the current directory
        # you should replace this with the location the
        # opus library is located in and with the proper filename.
        # note that on windows this DLL is automatically provided for you
        discord.opus.load_opus('opus')
		
@client.event
async def on_member_join(member):
    server = member.server
    joinEmbed = discord.Embed(title="{} has joined the server.".format(member), description= 'Join Date: {} UTC'.format(member.joined_at), color=discord.Color.green())
    joinEmbed.set_footer(text='User Joined')
    joinEmbed.set_thumbnail(url=member.avatar_url)
    await bot.send_message(discord.utils.get(member.server.channels, name='joinleave'), embed=joinEmbed)
    await bot.add_roles(member, discord.utils.get(member.server.roles, name="Watcher"))
    logMsg = "{0} ({0.id}) has just joined {1}. Added the 'Watcher' Role to {0}.".format(member, server)
    log(logMsg)
	
@client.event
async def on_member_remove(member):
	server = member.server
	server = member.server
	leaveEmbed = discord.Embed(title="{} has left the server.".format(member), description= 'Leave Date: {} UTC'.format(datetime.utcnow()), color=discord.Color.red())
	leaveEmbed.set_footer(text='User Left')
	leaveEmbed.set_thumbnail(url=member.avatar_url)
	await bot.send_message(discord.utils.get(member.server.channels, name='joinleave'), embed=leaveEmbed)
	logMsg = "{0} ({0.id}) has just left {1}.".format(member, server)
	log(logMsg)

   # Who am I Command
@bot.command(pass_context = True)
async def whoami(ctx):
    """Tells you your identity"""
    whoamiEmbed = discord.Embed(title="{}'s Information".format(ctx.message.author.name), description='Join Date: {0.joined_at} \n User ID: {0.id} \n Discriminator: {0.discriminator}'.format(ctx.message.author), color=discord.Color.gold())
    whoamiEmbed.set_footer(text=version)
    whoamiEmbed.set_thumbnail(url=ctx.message.author.avatar_url)
    await bot.send_message(ctx.message.channel, embed=whoamiEmbed)
	
   # About Command
@bot.command(pass_context = True)
async def about(ctx):
    """Tells you about this bot."""
    aboutEmbed = discord.Embed(title='About BunBot', description="Custom Discord Bot", url="https://github.com/RockDHouse/BunBotPy", color=discord.Color.gold())
    aboutEmbed.set_footer(text=version)
    aboutEmbed.set_thumbnail(url=bot.user.avatar_url)
    await bot.send_message(ctx.message.channel, embed=aboutEmbed)

    # User Info Command
@bot.command()
async def userinfo(member : discord.Member):
    """Says when a member joined."""
    await bot.say('{0.name} joined in {0.joined_at}'.format(member))
    
    # Ping Command
@bot.command(pass_context = True)
async def ping(ctx):
    """Pong!"""
    msgTimeSent = ctx.message.timestamp
    msgNow = datetime.now()
    await bot.send_message(ctx.message.channel, "The message was sent at: " + str(msgNow - msgTimeSent))
	
    # XKCD Comic Command
@bot.command(pass_context = True)
async def x(ctx, cnumber : str):
	"""Returns the XKCD comic specified"""
	if isnumeric(cnumber):
		await bot.send_message(ctx.message.channel, "https://xkcd.com/" + cnumber + "/")
	else:
		await bot.send_message(ctx.message.channel, "Error: Not a comic number")
		
#@client.event
#async def on_message(ctx):
#	if(ctx.message.channel == discord.utils.get(ctx.member.server.channels, name='spottings')):
#		await bot.add_roles(ctx.member, discord.utils.get(ctx.member.server.roles, name="Spotter"))

	
class VoiceEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player

    def __str__(self):
        fmt = '*{0.title}* uploaded by {0.uploader} and requested by {1.display_name}'
        duration = self.player.duration
        if duration:
            fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
        return fmt.format(self.player, self.requester)

class VoiceState:
    def __init__(self, bot):
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        player = self.current.player
        return not player.is_done()

    @property
    def player(self):
        return self.current.player

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    async def audio_player_task(self):
        while True:
            self.play_next_song.clear()
            self.current = await self.songs.get()
            await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
            self.current.player.start()
            await self.play_next_song.wait()

class Music:
    """Voice related commands.
    Works in multiple servers at once.
    """
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx, *, channel : discord.Channel):
        """Joins a voice channel."""
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            await self.bot.say('Already in a voice channel...')
        except discord.InvalidArgument:
            await self.bot.say('This is not a voice channel...')
        else:
            await self.bot.say('Ready to play audio in ' + channel.name)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None: 
            await self.bot.say('You are not in a voice channel.')
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)

        return True

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, song : str):
        """Plays a song."""
        state = self.get_voice_state(ctx.message.server)
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        try:
            player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
        else:
            player.volume = 0.6
            entry = VoiceEntry(ctx.message, player)
            await self.bot.say('Enqueued ' + str(entry))
            await state.songs.put(entry)

    @commands.command(pass_context=True, no_pm=True)
    async def volume(self, ctx, value : int):
        """Sets the volume of the currently playing song."""

        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.volume = value / 100
            await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()

    @commands.command(pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        server = ctx.message.server
        state = self.get_voice_state(server)

        if state.is_playing():
            player = state.player
            player.stop()

        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Shows info about the currently played song."""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            await self.bot.say('Not playing anything.')
bot.add_cog(Music(bot))

client.run(authDeets.token)

