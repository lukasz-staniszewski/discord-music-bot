import discord
import os
from discord.ext import commands
from youtube_dl import YoutubeDL
import asyncio
from discord.utils import get


class EmptyPlaylistException(Exception):
    pass


class PlaylistBoundsException(Exception):
    pass


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.is_playing_on_server = False
        self.is_playing_on_server = {}
        # self.playlist = []
        self.server_playlist = {}
        # self.mutex_playlist = asyncio.Lock()
        self.server_mutex_playlist = {}
        self.YTDL_OPTIONS = {
            "format": "bestaudio",
            "noplaylist": True,
        }
        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }

        # self.voice_channel = ""
        self.server_voice_channel = {}
        self.server_current_song = {}

    def connect_channel(self, ctx):
        self.is_playing_on_server[ctx.guild.id] = False
        self.server_playlist[ctx.guild.id] = []
        self.server_mutex_playlist[ctx.guild.id] = asyncio.Lock()
        self.server_voice_channel[ctx.guild.id] = ctx.author.voice.channel
        print(f"AFTER CONNECTION:\n{self.server_voice_channel[ctx.guild.id]=}\n")
        self.server_current_song[ctx.guild.id] = ""

    def search_youtube(self, item):
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
        }

    def play_next(self, ctx):
        if len(self.server_playlist[ctx.guild.id]) > 0:
            self.is_playing_on_server[ctx.guild.id] = True
            m_url = self.server_playlist[ctx.guild.id][0][0]["source"]
            self.server_current_song[ctx.guild.id] = self.server_playlist[
                ctx.guild.id
            ].pop(0)
            try:
                self.server_voice_channel[ctx.guild.id].play(
                    discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                    after=lambda f: self.play_next(ctx),
                )
            except discord.errors.ClientException as e:
                if str(e) == "Already playing audio.":
                    print("~ERROR~ | Weirdo exception :~")
        else:
            self.is_playing_on_server[ctx.guild.id] = False
            self.server_current_song[ctx.guild.id] = ""

    async def play_music(self, ctx):
        if len(self.server_playlist[ctx.guild.id]) > 0:
            self.is_playing_on_server[ctx.guild.id] = True
            await self.server_mutex_playlist[ctx.guild.id].acquire()
            try:
                m_url = self.server_playlist[ctx.guild.id][0][0]["source"]
            finally:
                self.server_mutex_playlist[ctx.guild.id].release()
            try:
                self.server_voice_channel[ctx.guild.id] = await self.server_playlist[
                    ctx.guild.id
                ][0][1].connect()
            except discord.errors.ClientException:
                self.server_voice_channel[ctx.guild.id].move_to(
                    self.server_playlist[ctx.guild.id][0][1]
                )

            await self.server_mutex_playlist[ctx.guild.id].acquire()
            try:
                self.server_current_song[ctx.guild.id] = self.server_playlist[
                    ctx.guild.id
                ].pop(0)
            finally:
                self.server_mutex_playlist[ctx.guild.id].release()
            self.server_voice_channel[ctx.guild.id].play(
                discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                after=lambda f: self.play_next(ctx),
            )
        else:
            self.is_playing_on_server[ctx.guild.id] = False
            self.server_current_song[ctx.guild.id] = ""

    @commands.command(aliases=["p", "play", "P"])
    async def _play(self, ctx, *args):
        query = " ".join(args)
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("You need to be in any voice channel to invite me! 🤬")
            await ctx.send("https://j.gifs.com/qxjV50.gif")
        else:
            if ctx.guild.id not in self.is_playing_on_server.keys():
                self.connect_channel(ctx)
            voice_channel = ctx.author.voice.channel
            song = self.search_youtube(query)
            if type(song) == bool:
                await ctx.send("Try other video, this one cant be played! 🤐")
                await ctx.send("https://c.tenor.com/ACD_2wFkA4QAAAAC/tssk-no.gif")
            else:
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
                await self.server_mutex_playlist[ctx.guild.id].acquire()
                try:
                    await ctx.send(
                        "Song {} added to the queue, its current position: {}".format(
                            song["title"],
                            str(len(self.server_playlist[ctx.guild.id]) + 1),
                        )
                    )
                    if gifx:
                        await ctx.send(
                            "https://tenor.com/view/xayoo-twitch-idol-gif-22718834"
                        )
                    if gifb:
                        await ctx.send(
                            "https://tenor.com/view/boxdel-kwatera-pszczulka-kofelina-jasper-gif-22735704"
                        )
                    self.server_playlist[ctx.guild.id].append([song, voice_channel])
                finally:
                    self.server_mutex_playlist[ctx.guild.id].release()
                if self.is_playing_on_server[ctx.guild.id] is False:
                    await self.play_music(ctx)

    @commands.command(aliases=["queue", "q", "playlist"])
    async def _queue(self, ctx):
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
            await ctx.send("```\n" + retval + "```")
        else:
            await ctx.send("No music in queue! 🛑")

    @commands.command(aliases=["current", "current_song"])
    async def _current(self, ctx):
        if self.server_current_song[ctx.guild.id] != "":
            await ctx.send(
                "```\nCurrent song's name is: {}\n```".format(
                    self.server_current_song[ctx.guild.id][0]["title"]
                )
            )
        else:
            await ctx.send("There is no current song! 🛑")

    @commands.command(aliases=["skip", "s"])
    async def _skip(self, ctx=None):
        if (
            self.server_voice_channel[ctx.guild.id] != ""
            and self.server_voice_channel[ctx.guild.id]
        ):
            self.server_voice_channel[ctx.guild.id].pause()
            await self.play_music(ctx)

    @commands.command(aliases=["clear", "c"])
    async def _clear(self, ctx):
        if (
            self.server_voice_channel[ctx.guild.id] != ""
            and self.server_voice_channel[ctx.guild.id]
        ):
            await self.server_mutex_playlist[ctx.guild.id].acquire()
            try:
                self.server_voice_channel[ctx.guild.id].stop()
                self.server_playlist[ctx.guild.id] = []
                self.is_playing_on_server[ctx.guild.id] = False
                self.server_current_song[ctx.guild.id] = ""
            finally:
                self.server_mutex_playlist[ctx.guild.id].release()

    @commands.command(aliases=["remove", "r"])
    async def _remove(self, ctx, *args):
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
            await ctx.send("🛑 You can't remove from empty playlist! 🛑")
        except (ValueError):
            await ctx.send(
                "🛑 Hold on! You passed incorrect argument! 🛑\nExample use:\n```\n!remove 2\n```"
            )
        except (PlaylistBoundsException) as e:
            await ctx.send(
                f"🛑 There is no {e}. place on the playlist! Try numbers from 1 to {len(self.playlist)} 🛑"
            )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if (
            before.channel is not None
            and after.channel is None
            and str(member) == "DJ WidziszMnie#0843"
        ):
            print("~BOT_INFO~ | Bot disconnected!")
            await self._clear(member)
