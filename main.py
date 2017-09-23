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

description = '''BunBot Help'''
client = commands.Bot(command_prefix='-', description=description)
bot = client
version = 'Version: 1.1' 

@client.event
async def on_ready():
    print("Logged in as: {0}, with the ID of: {1}".format(client.user, client.user.id))
    await client.change_presence(game=discord.Game(name='in the meadow'))
    print("--")
		
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
	if is_number(cnumber):
		await bot.send_message(ctx.message.channel, "https://xkcd.com/" + cnumber + "/")
	else:
		await bot.send_message(ctx.message.channel, "Error: Not a comic number")
		
@client.event
async def on_message(message):
	if(message.channel == discord.utils.get(message.server.channels, name='spottings')):
		for role in message.author.roles:
			if(role.name == "Watcher"):
				await bot.add_roles(message.author, discord.utils.get(message.server.roles, name="Spotter"))
				await bot.remove_roles(message.author, discord.utils.get(message.server.roles, name="Watcher"))
				logMsg = "{} was upgraded to Spotter".format(message.author)
				log(logMsg)
	else:
		await bot.process_commands(message)

def is_number(s):
	try:
		float(s)
		return True
	except ValueError:
		return False
		
def log(message):
    print(datetime.now(), message)

client.run(authDeets.token)
