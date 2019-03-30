import discord

class MarcelPlugin:
    
    plugin_name = "Music Player"
    plugin_description = "Default Music Player to listen to music."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `join` or `leave` to join the voice channel you are in / leave the one I am in.
    `play` [request] plays the requested link (supports these: https://rg3.github.io/youtube-dl/supportedsites.html), or searches the request on YouTube. (Playlists are not supported yet)
    `stop`, `pause` and `resume` do as they say on the media playing.
    `skip` skips to the next song in the player queue (if any).
    `add` [request] add a request to the player queue.
    `clear` clears the player queue.
    `queue` displays the player queue.
    `playing` displays what's currently playing.
    `volume` [0 - 200] sets the volume (in %).

    **The following commands are only for administrators/moderators.**
    `max_volume` [0 - 200] sets a maximum volume value (default is 200%), to prevent bleeding ears.
    """
    bot_commands = [
        'join',
        'leave',
        'play',
        'stop',
        'skip',
        'pause',
        'resume',
        'add',
        'clear',
        'queue',
        'volume',
        'playing',
        'max_volume',
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        if self.marcel.verbose : print("Music plugin loaded.")


    async def join(self, message, args):
        await self.marcel.voice_client_join(message)

    async def leave(self, message, args):
        await self.marcel.voice_client_leave(message)

    async def play(self, message, args):
        if args:
            await self.marcel.voice_client_play(message, ' '.join(args).strip())
        else:
            await self.marcel.voice_client_skip(message)

    async def stop(self, message, args):
        await self.marcel.voice_client_stop(message)

    async def skip(self, message, args):
        await self.marcel.voice_client_skip(message)
    
    async def pause(self, message, args):
        await self.marcel.voice_client_pause(message)

    async def resume(self, message, args):
        await self.marcel.voice_client_resume(message)

    async def add(self, message, args):
        if args:
            await self.marcel.voice_client_queue_add(message, ' '.join(args).strip())
        else:
            await self.marcel.bot.send_message(message.channel, "You can't add nothingness.")

    async def clear(self, message, args):
        await self.marcel.voice_client_queue_clear(message)
    
    async def queue(self, message, args):
        queue_embed=discord.Embed(color=0x0050ff)
        queue_embed.set_author(name="Player queue")
        if message.server.id in self.marcel.voice_clients:
            if len(self.marcel.voice_clients[message.server.id].player_queue) > 0:
                for i in range(0, len(self.marcel.voice_clients[message.server.id].player_queue)):
                    playerinfo = self.marcel.voice_clients[message.server.id].player_queue[i]
                    if i == 0:
                        queue_embed.title = playerinfo['title']
                        queue_embed.description = playerinfo['author']
                        queue_embed.url = playerinfo['url']
                        queue_embed.set_thumbnail(url=playerinfo['thumbnail'])

                    else:
                        queue_embed.add_field(name=playerinfo['title'], value=playerinfo['author'], inline=False)
                
            else:
                queue_embed.title = "The player queue is empty."
        else:
            queue_embed.title = "The player queue is empty."
        
        await self.marcel.bot.send_message(message.channel, embed=queue_embed)
    
    async def playing(self, message, args):
        queue_embed=discord.Embed(color=0x0050ff)
        queue_embed.set_author(name="Currently playing")
        if message.server.id in self.marcel.voice_clients:
            playerinfo = self.marcel.voice_clients[message.server.id].player_info
            if 'title' in playerinfo:
                queue_embed.title = playerinfo['title']
                queue_embed.description = playerinfo['author']
                queue_embed.url = playerinfo['url']
                queue_embed.set_thumbnail(url=playerinfo['thumbnail'])
                
            else:
                queue_embed.title = "Nothing is playing at the moment."

        else:
            queue_embed.title = "Nothing is playing at the moment."
        
        await self.marcel.bot.send_message(message.channel, embed=queue_embed)

    async def volume(self, message, args):
        if args:
            try:
                new_volume = round(float(args[0]), 0)
                max_volume = self.marcel.get_setting(message.server, 'music_max_volume', 200)
                if max_volume >= new_volume >= 0:
                    await self.marcel.voice_client_volume(message, new_volume)
                    await self.marcel.bot.send_message(message.channel, "Volume changed to : **" + str(new_volume) + "%**.")

                else:
                    await self.marcel.bot.send_message(message.channel, "The volume cannot be less than **0%** and cannot exceed **" + str(max_volume) + "%**.")

            except:
                await self.marcel.bot.send_message(message.channel, "Incorrect volume value.")
        else:
            if message.server.id in self.marcel.voice_clients:
                await self.marcel.bot.send_message(message.channel, "Current volume : **" + str(self.marcel.voice_clients[message.server.id].player_volume * 100) + "%**.")

    async def max_volume(self, message, args):
        if args:
            if self.marcel.is_admin(message) or self.marcel.is_moderator(message):
                try:
                    new_volume = round(float(args[0]), 0)
                    if 200 >= new_volume >= 0:
                        self.marcel.set_setting(message.server, 'music_max_volume', new_volume)
                        await self.marcel.bot.send_message(message.channel, "Maximum volume changed to : **" + str(new_volume) + "%**.")
                        if message.server.id in self.marcel.voice_clients:
                            if self.marcel.voice_clients[message.server.id].player_volume * 100 > new_volume:
                                await self.volume(message, [new_volume])

                    else:
                        await self.marcel.bot.send_message(message.channel, "The volume cannot be less than **0%** and cannot exceed **200%**.")

                except:
                    await self.marcel.bot.send_message(message.channel, "Incorrect volume value.")
            else:
                await self.marcel.bot.send_message(message.channel, "Only administrators and moderators can change the maximum volume value.")

        else:
            await self.marcel.bot.send_message(message.channel, "Maximum volume is at : **" + str(self.marcel.get_setting(message.server, 'music_max_volume', 200)) + "%**.")
