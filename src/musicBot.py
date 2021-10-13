import discord
import os
from discord.ext import commands
from youtube_dl import YoutubeDL
import asyncio
from discord.utils import get
from discord.ext.commands.bot import Bot
from discord.member import VoiceState
from discord.ext.commands.context import Context
from src.CurrentSong import CurrentSong
from src.constants import HELP_MESSAGE


class EmptyPlaylistException(Exception):
    pass


class PlaylistBoundsException(Exception):
    pass


class MusicCog(commands.Cog):
    def __init__(self, bot: Bot):
        """Cog constructor.

        Args:
            bot (Bot): Discord bot refference.
        """
        self.YTDL_OPTIONS = {
            "format": "bestaudio",
            "noplaylist": True,
        }
        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        self.bot = bot
        self.help_message = HELP_MESSAGE
        self.is_playing_on_server = {}
        self.server_playlist = {}
        self.server_mutex_playlist = {}
        self.server_voice_channel = {}
        self.server_current_song = {}

    def init_channel(self, ctx: Context):
        """Initializing voice channel for bot.

        Args:
            ctx (Context): Context of executed discord command.
        """
        self.is_playing_on_server[ctx.guild.id] = False
        self.server_playlist[ctx.guild.id] = []
        self.server_mutex_playlist[ctx.guild.id] = asyncio.Lock()
        self.server_voice_channel[ctx.guild.id] = ctx.author.voice.channel
        self.server_current_song[ctx.guild.id] = CurrentSong("", "")

    def search_youtube(self, item: str) -> any:
        """Function search for given song in YouTube.

        Args:
            item (str): Specified song to search.

        Returns:
            any: Returns dict of song info if everything ok, else False.
        """
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)[
                    "entries"
                ][0]
            except Exception:
                return False

        return {
            "source": info["formats"][0]["url"],
            "title": info["title"],
            "duration": info["duration"],
            "yt_url": info["webpage_url"],
        }

    async def send_message(self, message_str: str, ctx: Context):
        """Sends message in correct template.

        Args:
            message_str (str): Specified message to send.
            ctx (Context): Context of executed discord command.
        """
        await ctx.send(f"```\n{message_str}\n```")

    def is_channel_specified(self, ctx: Context) -> bool:
        """Checks if sender of message is on any voice channel.

        Args:
            ctx (Context: Context of executed discord command.

        Returns:
            bool: True if voice channel on contextial server is specified.
        """
        if (
            ctx.guild.id in self.server_voice_channel.keys()
            and self.server_voice_channel[ctx.guild.id] != ""
        ):
            return True
        else:
            return False

    async def send_funny_gifs(self, query: str, song: dict, ctx):
        """Checks if song has key-words and sends funny gifs if True.

        Args:
            query (str): Searching quote.
            song (dict): Song info.
            ctx (Context): Context of executed discord command.
        """
        concat_str = query.upper() + song["title"].upper()
        gifx = False
        if concat_str.find("XAYOO") != -1:
            gifx = True
        gifb = False
        if (
            concat_str.find("BOXDEL") != -1
            or concat_str.find("MASN") != -1
            or concat_str.find("AFERKI") != -1
            or concat_str.find("MGNG") != -1
        ):
            gifb = True
        if gifx:
            await ctx.send("https://tenor.com/view/xayoo-twitch-idol-gif-22718834")
        if gifb:
            await ctx.send(
                "https://tenor.com/view/boxdel-kwatera-pszczulka-kofelina-jasper-gif-22735704"
            )

    def play_next(self, ctx: Context):
        """Plays next song on playlist.

        Args:
            ctx (Context): Context of executed discord command.
        """
        if len(self.server_playlist[ctx.guild.id]) > 0:
            self.is_playing_on_server[ctx.guild.id] = True
            song_url = self.server_playlist[ctx.guild.id][0][0]["source"]
            popped_song = self.server_playlist[ctx.guild.id].pop(0)
            self.server_current_song[ctx.guild.id].song_url = popped_song[0]["yt_url"]
            self.server_current_song[ctx.guild.id].song_name = popped_song[0]["title"]

            try:
                self.server_voice_channel[ctx.guild.id].play(
                    discord.FFmpegPCMAudio(song_url, **self.FFMPEG_OPTIONS),
                    after=lambda f: self.play_next(ctx),
                )
            except discord.errors.ClientException as e:
                if str(e) == "Already playing audio.":
                    print("~BOT ERROR~ | ~Already playing audio exception!~")
        else:
            self.is_playing_on_server[ctx.guild.id] = False
            self.server_current_song[ctx.guild.id].clear_info()

    async def reconnect(self, ctx: Context):
        """Provides reconnecting to channel after network error.

        Args:
            ctx (Context): Context of executed discord command.
        """
        print("~BOT STATE INFO~ | ~Bot is reconnecting~")
        self.server_voice_channel[ctx.guild.id] = await self.server_playlist[
            ctx.guild.id
        ][0][1].connect()

        self.server_voice_channel[ctx.guild.id].play(
            discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
            after=lambda f: self.play_next(ctx),
        )

    async def play_music(self, ctx: Context):
        """Function starts playing music on server.

        Args:
            ctx (Context): Context of executed discord command.
        """
        if len(self.server_playlist[ctx.guild.id]) > 0:
            self.is_playing_on_server[ctx.guild.id] = True
            await self.server_mutex_playlist[ctx.guild.id].acquire()
            try:
                song_url = self.server_playlist[ctx.guild.id][0][0]["source"]
            finally:
                self.server_mutex_playlist[ctx.guild.id].release()
            try:
                self.server_voice_channel[ctx.guild.id] = await self.server_playlist[
                    ctx.guild.id
                ][0][1].connect()
            except discord.errors.ClientException:
                await self.server_voice_channel[ctx.guild.id].move_to(
                    self.server_playlist[ctx.guild.id][0][1]
                )

            await self.server_mutex_playlist[ctx.guild.id].acquire()
            try:
                popped_song = self.server_playlist[ctx.guild.id].pop(0)
                self.server_current_song[ctx.guild.id].song_url = popped_song[0][
                    "yt_url"
                ]
                self.server_current_song[ctx.guild.id].song_name = popped_song[0][
                    "title"
                ]
            finally:
                self.server_mutex_playlist[ctx.guild.id].release()
            try:
                self.server_voice_channel[ctx.guild.id].play(
                    discord.FFmpegPCMAudio(song_url, **self.FFMPEG_OPTIONS),
                    after=lambda f: self.play_next(ctx),
                )
            except discord.errors.ClientException:
                self.reconnect(ctx)
        else:
            self.is_playing_on_server[ctx.guild.id] = False
            self.server_current_song[ctx.guild.id].clear_info()

    @commands.command(aliases=["p", "play", "P"])
    async def _play(self, ctx: Context, *args):
        """Reacts on '!play' command.

        Args:
            ctx (Context): Context of executed discord command.
        """
        query = " ".join(args)
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await self.send_message(
                "You need to be in any voice channel to invite me! 🤬", ctx
            )
            await ctx.send("https://j.gifs.com/qxjV50.gif")
        else:
            if ctx.guild.id not in self.is_playing_on_server.keys():
                self.init_channel(ctx)
            voice_channel = ctx.author.voice.channel
            song = self.search_youtube(query)
            if type(song) == bool:
                await self.send_message(
                    "Try other video, this one cant be played! 🤐", ctx
                )
                await ctx.send("https://c.tenor.com/ACD_2wFkA4QAAAAC/tssk-no.gif")
            else:
                await self.server_mutex_playlist[ctx.guild.id].acquire()
                try:
                    await self.send_funny_gifs(query, song, ctx)
                    await self.send_message(
                        "Song {} added to the queue, its current position: {}".format(
                            song["title"],
                            str(len(self.server_playlist[ctx.guild.id]) + 1),
                        ),
                        ctx,
                    )
                    self.server_playlist[ctx.guild.id].append([song, voice_channel])
                finally:
                    self.server_mutex_playlist[ctx.guild.id].release()
                if self.is_playing_on_server[ctx.guild.id] is False:
                    await self.play_music(ctx)

    @commands.command(aliases=["queue", "q", "playlist"])
    async def _queue(self, ctx: Context):
        """Shows queue/playlist.

        Args:
            ctx (Context): Context of executed discord command.
        """
        retval = ""
        for i in range(0, len(self.server_playlist[ctx.guild.id])):
            retval += (
                str(i + 1)
                + "-> "
                + self.server_playlist[ctx.guild.id][i][0]["title"]
                + " | "
                + f"{(self.server_playlist[ctx.guild.id][i][0]['duration'] // 60)}"
                + ":"
                + f"{(self.server_playlist[ctx.guild.id][i][0]['duration'] % 60):02}"
                + "\n"
            )

        if retval != "":
            await self.send_message(retval, ctx)
        else:
            await self.send_message("No music in queue! 🛑", ctx)

    @commands.command(aliases=["current", "current_song"])
    async def _current(self, ctx: Context):
        """Shows currently played song.

        Args:
            ctx (Context): Context of executed discord command.
        """
        if not self.server_current_song[ctx.guild.id].is_empty():
            await self.send_message(
                "Current song's name is: {} | [{}]".format(
                    self.server_current_song[ctx.guild.id].song_name,
                    self.server_current_song[ctx.guild.id].song_url,
                ),
                ctx,
            )
        else:
            await self.send_message("There is no current song! 🛑", ctx)

    @commands.command(aliases=["skip", "s"])
    async def _skip(self, ctx: Context):
        """Skips currently played song.

        Args:
            ctx (Context, optional): Context of executed discord command. Defaults to None.
        """
        if self.is_channel_specified(ctx):
            self.server_voice_channel[ctx.guild.id].pause()
            await self.play_music(ctx)

    @commands.command(aliases=["clear", "c"])
    async def _clear(self, ctx: Context):
        """Clears whole playlist and stop playing bot.

        Args:
            ctx (Context): Context of executed discord command.
        """
        if self.is_channel_specified(ctx):
            await self.server_mutex_playlist[ctx.guild.id].acquire()
            try:
                self.server_voice_channel[ctx.guild.id].stop()
                self.server_playlist[ctx.guild.id] = []
                self.is_playing_on_server[ctx.guild.id] = False
                self.server_current_song[ctx.guild.id].clear_info()
            finally:
                self.server_mutex_playlist[ctx.guild.id].release()

    @commands.command(aliases=["remove", "r"])
    async def _remove(self, ctx: Context, *args):
        """Removes song with given index from playlist.

        Args:
            ctx (Context): Context of executed discord command.
        """
        query = " ".join(args)
        try:
            if len(self.server_playlist[ctx.guild.id]) == 0:
                raise EmptyPlaylistException
            int_arg = int(query)
            if int_arg < 1 or int_arg > len(self.server_playlist[ctx.guild.id]):
                raise PlaylistBoundsException(f"{int_arg}")
            await self.server_mutex_playlist[ctx.guild.id].acquire()
            try:
                self.server_playlist[ctx.guild.id].pop(int_arg - 1)
            finally:
                self.server_mutex_playlist[ctx.guild.id].release()

        except (EmptyPlaylistException):
            await self.send_message("🛑 You can't remove from empty playlist! 🛑", ctx)
        except (ValueError):
            await self.send_message(
                "🛑 Hold on! You passed incorrect argument! 🛑\nExample use:\n\n====================\n!remove 2\n====================",
                ctx,
            )
        except (PlaylistBoundsException) as e:
            await self.send_message(
                f"🛑 There is no {e}. place on the playlist! Try numbers from 1 to {len(self.server_playlist[ctx.guild.id])} 🛑",
                ctx,
            )

    @commands.command(aliases=["help", "h"])
    async def _help(self, ctx: Context):
        """Shows help message.

        Args:
            ctx (Context): Context of executed discord command.
        """
        await self.send_message(self.help_message, ctx)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, ctx: Context, before: VoiceState, after: VoiceState
    ):
        """Function reacts on disconnection of bot from voice channel. It executes _clear method.

        Args:
            ctx (Context): Context of executed discord command.
            before (VoiceState): State of channel before disconnection.
            after (VoiceState): State of channel after disconnection.
        """
        if (
            before.channel is not None
            and after.channel is None
            and str(ctx) == "DJ WidziszMnie#0843"
        ):
            print("~BOT_INFO~ | Bot disconnected!")
            await self._clear(ctx)
