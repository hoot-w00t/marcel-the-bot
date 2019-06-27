import discord, youtube_dl, os

class MarcelPlugin:
    
    plugin_name = "Music Player"
    plugin_description = "Default Music Player to listen to music."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `join` or `leave` to join the voice channel you are in / leave the one I am in.
    `play` [request] plays the requested link (supports these: https://rg3.github.io/youtube-dl/supportedsites.html), or searches the request on YouTube. (Playlists are not supported yet)
    `stop`, `pause` and `resume` do as they say on the media playing.
    `skip` skips to the next song in the player queue (if any).
    `add` [request] add a request to the player queue.
    `search` [request] searches for your request. You can later add it to the player queue using `add`.
    `download` [request] sends your request in the MP3 format (files >8MB can't be sent due to Discord's limitations).
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
        'search',
        'download',
        'clear',
        'queue',
        'volume',
        'playing',
        'max_volume',
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        if self.marcel.verbose : self.marcel.print_log("[Music] Plugin loaded.")


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
        await self.marcel.voice_client_queue_add(message, ' '.join(args).strip())

    async def search(self, message, args):
        if args:
            await self.marcel.voice_client_search(message, ' '.join(args).strip())
        else:
            await message.channel.send("You can't search nothingness.")

    async def download(self, message, args): # youtube-dl -f bestaudio --extract-audio --audio-format mp3 https://www.youtube.com/watch?v=qfqA1sTKhmw -o djadja.mp3
        if args:
            await self.marcel.voice_client_search(message, ' '.join(args).strip(), True)
        
        if str(message.guild.id) in self.marcel.voice_clients:
            if self.marcel.voice_clients[str(message.guild.id)].player_last_search == None:
                await message.channel.send('Nothing to download.')
            else:
                search_info = self.marcel.voice_clients[str(message.guild.id)].player_last_search
                async with message.channel.typing():
                    output_file = self.ytdl_download(search_info['url'])
                    if not output_file == None:
                        filename = os.path.basename(output_file)

                        if os.path.exists(output_file):
                            await message.channel.send("Here you go.", file=discord.File(output_file, filename=filename))
                            os.unlink(output_file)

                    else:
                        await message.channel.send("I couldn't process your request because the file size is over 8MB.")

        else:
            await message.channel.send('Nothing to download.')

    def ytdl_download(self, url):
        try:
            ytdl = youtube_dl.YoutubeDL({
                'format': 'bestaudio[filesize<8M]',
                'audio-format': 'mp3',
                'outtmpl': os.path.join(self.marcel.temp_folder, '%(title)s.%(ext)s'),
                'restrictfilenames': True,
                'noplaylist': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'quiet': True,
                'no_warnings': True,
                'default_search': 'auto',
                'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
            })
            dl = ytdl.extract_info(url, download=True)
            return ytdl.prepare_filename(dl)
        except:
            return None

    async def clear(self, message, args):
        await self.marcel.voice_client_queue_clear(message)
    
    async def queue(self, message, args):
        queue_embed=discord.Embed(color=0x0050ff)
        queue_embed.set_author(name="Player queue")
        guild_id = str(message.guild.id)
        if guild_id in self.marcel.voice_clients:
            if len(self.marcel.voice_clients[guild_id].player_queue) > 0:
                for i in range(0, len(self.marcel.voice_clients[guild_id].player_queue)):
                    playerinfo = self.marcel.voice_clients[guild_id].player_queue[i]
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
        
        await message.channel.send(embed=queue_embed)
    
    async def playing(self, message, args):
        queue_embed=discord.Embed(color=0x0050ff)
        queue_embed.set_author(name="Currently playing")
        guild_id = str(message.guild.id)
        if guild_id in self.marcel.voice_clients:
            playerinfo = self.marcel.voice_clients[guild_id].player_info
            if 'title' in playerinfo:
                queue_embed.title = playerinfo['title']
                queue_embed.description = playerinfo['author']
                queue_embed.url = playerinfo['url']
                queue_embed.set_thumbnail(url=playerinfo['thumbnail'])
                
            else:
                queue_embed.title = "Nothing is playing at the moment."

        else:
            queue_embed.title = "Nothing is playing at the moment."
        
        await message.channel.send(embed=queue_embed)

    async def volume(self, message, args):
        guild_id = str(message.guild.id)
        if args:
            try:
                new_volume = round(float(args[0]) / 100, 2)
                max_volume = self.marcel.get_setting(message.guild, 'maximum_volume', self.marcel.default_settings['maximum_volume'])
                if max_volume >= new_volume >= 0:
                    await self.marcel.voice_client_volume(message, new_volume)
                    await message.channel.send("Volume changed to : **" + str(new_volume * 100) + "%**.")

                else:
                    await message.channel.send("The volume cannot be less than **0%** and cannot exceed **" + str(max_volume * 100) + "%**.")

            except:
                await message.channel.send("Incorrect volume value.")
        else:
            if guild_id in self.marcel.voice_clients:
                await message.channel.send("Current volume : **" + str(self.marcel.voice_clients[guild_id].player_volume * 100) + "%**.")

    async def max_volume(self, message, args):
        if args:
            if self.marcel.is_admin(message) or self.marcel.is_moderator(message):
                try:
                    new_volume = round(float(args[0]) / 100, 2)
                    if 2 >= new_volume >= 0:
                        self.marcel.set_setting(message.guild, 'maximum_volume', new_volume)
                        await self.marcel.voice_client_max_volume(message, new_volume)
                        await message.channel.send("Maximum volume changed to : **" + str(new_volume * 100) + "%**.")

                    else:
                        await message.channel.send("The volume cannot be less than **0%** and cannot exceed **200%**.")

                except:
                    await message.channel.send("Incorrect volume value.")
            else:
                await message.channel.send("Only administrators and moderators can change the maximum volume value.")

        else:
            await message.channel.send("Maximum volume is at : **" + str(self.marcel.get_setting(message.guild, 'maximum_volume', self.marcel.default_settings['maximum_volume']) * 100) + "%**.")
