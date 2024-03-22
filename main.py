import discord
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl
import os
from keep_alive import keep_alive
import asyncio

from random import choice

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


client = commands.Bot(command_prefix='/')

status = ['Jamming out to music!', 'Eating!', 'Sleeping!']
queue = []

@client.event
async def on_ready():
    change_status.start()
    print('I am online!')

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    await channel.send(f'Welcome {member.mention}!  Ready to have fun darling? See `/help` command for details!')
        
@client.command(name='ping', help="let's play Ping Pong")
async def ping(ctx):
    await ctx.send(f'**Pong!** Latency: {round(client.latency * 1000)}ms')

@client.command(name='hello', help="You know what I'll do")
async def hello(ctx):
    responses = ["***Ohiyo*** Let's eat together, okay?", 'Found you.', "We're the only ones here, so we gotta obey them.", 'No peeking, darling.', '**DARLING!!!!**']
    await ctx.send(choice(responses))

@client.command(name='die', help='I will give you my last words')
async def die(ctx):
    responses = ["Once we die, we’ll only be a statistic. It won’t matter what we were called.", 'Don’t worry, we’ll always be together, Until the day we die.', 'If you have anything you wanna say, you better spit it out while you can. Because you’re all going to die sooner or later.']
    await ctx.send(choice(responses))

@client.command(name='credits', help='I will show you the credits darling!')
async def credits(ctx):
    await ctx.send('Edited by `@Darkhorizon`')
    

@client.command(name='creditz', help='I will show the TRUE credits darling!')
async def creditz(ctx):
    await ctx.send("""**If you don’t belong here, just a build a place where you do.
    If you don’t have a partner, just find another one. If you can’t find one, just take one by force!**""")

@client.command(name='join', help='I will join your voice channel darling!')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("Join a voice channel darling!")
        return
    
    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

@client.command(name='queue', help='I will add a song to the queue darling!')
async def queue_(ctx, url):
    global queue

    queue.append(url)
    await ctx.send(f'`{url}` is now queued darling!')

@client.command(name='remove', help='I will remove an item from the list darling!')
async def remove(ctx, aurl):
    global queue

    try:
        os.remove(aurl+".webm")
    
    except:
        await ctx.send('Your queue is either **empty** or is not there darling')
        
@client.command(name='play', help='I will play songs for you!')
async def play(ctx):
    global queue

    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(queue[0], loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send("**Now I'm playing:** {}".format(player.title))
    del(queue[0])

@client.command(name='pause', help='I will pause the song for you!')
async def pause(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.pause()

@client.command(name='resume', help='I will resume the song!')
async def resume(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.resume()

@client.command(name='view', help='I will show you the queue!')
async def view(ctx):
    await ctx.send(f'Your queue is now `{queue}!`')

@client.command(name='leave', help='I will leave the voice channel**:(**')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()

@client.command(name='stop', help='I will stop the song!')
async def stop(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.stop()

@tasks.loop(seconds=20)
async def change_status():
    await client.change_presence(activity=discord.Game(choice(status)))


keep_alive()     
client.run(os.getenv('TOKEN'))  

