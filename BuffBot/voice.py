from discord.ext import commands
from simpleeval import simple_eval
import math
import os
import random
import aiohttp
import hashlib
import database
import playlist
import botconfig




class Voice:
    def __init__(self, bot):
        self.bot = bot
        self.owners = botconfig.owners
        self.voice = None
        self.player = None
        self.volume = 1.0
        self.database = database.Database()
        self.playlist = playlist.Queue()
        self.people_voted = []
        

    @commands.command(name="summon", pass_context=True)
    async def summon(self, ctx):
        if self.voice:
            if self.voice.channel.id == ctx.message.author.voice.voice_channel.id:
                await self.bot.say("I'm already here ya dingus")
            else:
                await self.voice.move_to(ctx.message.author.voice.voice_channel)
        else:
            self.voice = await self.bot.join_voice_channel(ctx.message.author.voice.voice_channel)

    @commands.command(name="leaveChannel", pass_context=True)
    async def leaveChannel(self, ctx):
        await self.voice.disconnect()
        self.voice = None

    @commands.command(name="play", pass_context=True, help="Play some music!")
    async def play_audio(self, ctx, link):
        await self.play_music(ctx, link)

    @commands.command(name="votenext", pass_context=True)
    async def vote_next_song(self, ctx):
        if ctx.message.author.id in self.people_voted:
            await self.bot.repond("You've already voted to skip this song", ctx.message.author.mention)
        else:
            self.people_voted.append(ctx.message.author.id)
            self.people_voted.clear()
            if len(self.people_voted) == len((self.bot.voice_clients // 2) + 1):
                await self.play_next
            else:
                await self.bot.say(len((self.bot.voice_clients // 2) + 1) - len(self.people_voted),
                                       " more votes needed")

    @commands.command(name="stop", pass_context=True, help="Stop the audio player")
    async def stop_audio(self, ctx):
        if ctx.message.author.id not in self.owners:
            return None
        if self.player:
            self.player.stop()
        else:
            await self.bot.say("I'm not playing anything right now")

    @commands.command(name="setvolume", pass_context=True, help="Set the bot's volume (in percent)")
    async def set_volume(self, ctx, volume: int):
        if ctx.message.author.id not in self.owners:
            return None
        # Ensure the volume argument is between 0 and 100.
        if 0 > volume or volume > 100:
            await self.bot.say("I don't want to blow out your ears")
            return
        # Set the bot's volume value
        self.volume = float(volume/100)
        if self.player:
            # Set the volume to the player if it exists
            self.player.volume = self.volume
        else:
            await self.bot.say("I'm not playing anything right now, but I set the volume to {}% for next time".format(volume))

    @commands.command(name="flagChan", pass_context=True, help="Flag channels for games only. If you enter free, there is no restriction on the selected channel")
    async def flag_channel(self, ctx, free=None):
        if (free == "free") :
            # remove all restriction on selected channel and parse in free.
            self.database.remove_flagged_games(ctx.message.author.voice.voice_channel.id)

            # add free in as a title.
            self.database.flag_gaming_channel(ctx.message.author.voice.voice_channel.id, "free", 1)
            pass

        else :
            self.database.flag_gaming_channel(ctx.message.author.voice.voice_channel.id, ctx.message.author.game, 1)
        pass

    @commands.command(name="removeFlags", pass_context=True)
    async def remove_channel_flags(self, ctx):
        self.database.remove_flagged_games(ctx.message.author.voice.voice_channel.id)

    @commands.command(name="patrol", pass_context=True)
    async def patrol_channels(self, ctx):
        '''Patrol all voice channels from the calling channel.
                This method will go trough every channel and check each user. 
                    -> check if listed game is in the database
                        -> if not: move player to move queue.
                        -> if it is: Do nothing.
        '''

        if ctx.message.author.id not in self.owners:                       # Check if user is authorised to perform command.
            self.bot.say("You're not a big guy. :thinking: ")
            return None

        # User is authorised to perform command.. -> now perform actions.

        good_members = []
        move_queue = []                                            # to store the queue for later to move them.
        jail = self.get_jail(ctx)                                  # grab the jail, if not jail.. create one.

        # start to check channels.
        for channel in ctx.message.server.channels:
            if channel != jail:
                # If this returns 0, it means that either the room is empty or it isn't a voice channel
                if len(channel.voice_members) != 0:
                    voice_members = channel.voice_members

                    for member in voice_members:                        # for each member in the channel
                        if (len(self.database.get_flagged_games(channel_id=channel.id)) > 0) \
                        and self.database.get_flagged_games(channel_id=channel.id)[0] == "free":
                            #member is allowed.
                            pass
                        else :
                            print(self.database.get_flagged_games(channel.id))

                            if member.game not in self.database.get_flagged_games(channel.id):

                                if (not move_queue.__contains__(member)) :
                                    move_queue.append(member)
                                    print("added to move")

                            else:
                                good_members.append(member.mention)         # Add member too good boy list

        await self.sort_members_to_channels(members= move_queue, jail=jail)


    async def sort_members_to_channels(self, members, jail):
        '''For handling the move queue for patrol_channels..
           Move queue
           this is a queue for members that need to be moved to other channels because their has broken the game rule. 
                -> For each item of the move queue. Grab the game title and check it up with the database.
                    -> if no game match
                        -> move to jail.
                    -> if game match one channel..
                        -> move member to that channel.    
                            
        :param members:     The move queue
        :param jail:        Jail channel
        :return:            amount of moved members.
        '''
        for member in members :
            print("Handling " + member.mention)
            channel = self.database.get_game_channel(title=member.game)
            if (len(channel) == 0) :
                await self.bot.move_member(member, jail)
            else :
                await self.bot.move_member(member, self.bot.get_channel(channel[0]))
        pass





    async def respond(self, msg, author):
        await self.bot.say("{}, {}".format(msg, author))

    @commands.command(name="queue", pass_context=True, help="Add youtube link to music queue")
    async def add_to_queue(self, ctx, link):
        # TODO: find better solution for extracting link from message
        song = link
        # link added to next field in current song
        self.playlist.add_song(song)

    @commands.command(name="next", pass_context=True, help="Skip to next song in music queue")
    async def play_next(self, ctx):
        # if there is an item at the front of the queue, play it and get the next item
        if self.playlist.current:
            await self.play_music(ctx, self.playlist.pop())
        # nothing in queue
        elif self.playlist.current is None:
            await self.respond("Queue is empty", ctx.message.author.mention)

    @commands.command(name="start", pass_context=True, help="Start the music queue")
    async def start_queue(self, ctx):
        if self.playlist.current is None:
            await self.respond("Queue is empty", ctx.message.author.mention)
        else:
            await self.play_music(ctx, self.playlist.pop())

    @commands.command(name="peter", pass_context=True)
    async def peter(self, ctx):
        await self.play_music(ctx, self.playlist.peter())

    async def play_music(self, ctx, link):
        if ctx.message.author.id not in self.owners:
            return None
        # Get the voice channel the commanding user is in
        trigger_channel = ctx.message.author.voice.voice_channel
        # Return with a message if the user is not in a voice channel
        if trigger_channel is None:
            await self.bot.say("You're not in a voice channel right now")
            return
        if self.voice:
            if self.voice.channel.id != trigger_channel.id:
                # If the bot is in voice, but not in the same channel, move to the commanding user
                await self.voice.move_to(trigger_channel)
        else:
            # If the bot is not in a voice channel, join the commanding user
            self.voice = await self.bot.join_voice_channel(trigger_channel)
        # Stop the player if it is running, to make room for the next one
        if self.player:
            self.player.stop()
        # Create a StreamPlayer with the requested link
        self.player = await self.voice.create_ytdl_player(link)
        # Set the volume to the bot's volume value
        self.player.volume = self.volume
        self.player.start()

    # To check if the channel got a jail, return the channel. If channel do not have a jail voice channel.. create one.
    def get_jail (self, ctx) :
        #########
        # Collect the jail channel, if no channel found -> create one.
        #########
        jail = None
        for channel in ctx.message.server.channels:
            if channel.name == "Jail":
                jail = channel
                break
        if jail is None:  # if no jail exists
            self.bot.create_channel(name="Jail", server=ctx.message.server, type='voice')  # create jail
            for channel in ctx.message.server.channels:  # find the new channel
                if channel.name == "Jail":
                    jail = channel
                    break
        return jail

def setup(bot):
    bot.add_cog(Voice(bot))
