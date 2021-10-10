import discord
import os
from discord.ext import commands
from youtube_dl import YoutubeDL
import asyncio


class EmptyPlaylistException(Exception):
    pass


class PlaylistBoundsException(Exception):
    pass


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.playlist = []
        self.mutex_playlist = asyncio.Lock()
        self.YTDL_OPTIONS = {
            "format": "bestaudio",
            "noplaylist": True,
        }
        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }

        self.voice_channel = ""
        self.current_song = ""

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

    def play_next(self):
        if len(self.playlist) > 0:
            self.is_playing = True
            m_url = self.playlist[0][0]["source"]
            self.current_song = self.playlist.pop(0)
            try:
                self.voice_channel.play(
                    discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                    after=lambda f: self.play_next(),
                )
            except discord.errors.ClientException as e:
                if str(e) == "Already playing audio.":
                    print("~ERROR~ | Weirdo exception :~")
        else:
            self.is_playing = False
            self.current_song = ""

    async def play_music(self):
        if len(self.playlist) > 0:
            self.is_playing = True
            await self.mutex_playlist.acquire()
            try:
                m_url = self.playlist[0][0]["source"]
            finally:
                self.mutex_playlist.release()
            if (
                self.voice_channel == ""
                or not self.voice_channel.is_connected()
                or self.voice_channel == None
            ):
                self.voice_channel = await self.playlist[0][1].connect()
            else:
                await self.voice_channel.move_to(self.playlist[0][1])

            await self.mutex_playlist.acquire()
            try:
                self.current_song = self.playlist.pop(0)
            finally:
                self.mutex_playlist.release()
            self.voice_channel.play(
                discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                after=lambda f: self.play_next(),
            )
        else:
            self.is_playing = False
            self.current_song = ""

    @commands.command(aliases=["p", "play", "P"])
    async def _play(self, ctx, *args):
        query = " ".join(args)
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("You need to be in any voice channel to invite me! 🤬")
            await ctx.send("https://j.gifs.com/qxjV50.gif")
        else:
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
                await self.mutex_playlist.acquire()
                try:
                    await ctx.send(
                        "Song {} added to the queue, its current position: {}".format(
                            song["title"], str(len(self.playlist) + 1)
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
                    self.playlist.append([song, voice_channel])
                finally:
                    self.mutex_playlist.release()
                if self.is_playing is False:
                    await self.play_music()

    @commands.command(aliases=["queue", "q", "playlist"])
    async def _queue(self, ctx):
        retval = ""
        for i in range(0, len(self.playlist)):
            retval += (
                str(i + 1)
                + "-> "
                + self.playlist[i][0]["title"]
                + " | "
                + f"{(self.playlist[i][0]['duration'] // 60)}"
                + ":"
                + f"{(self.playlist[i][0]['duration'] % 60):02}"
                + "\n"
            )

        if retval != "":
            await ctx.send("```\n" + retval + "```")
        else:
            await ctx.send("No music in queue! 🛑")

    @commands.command(aliases=["current", "current_song"])
    async def _current(self, ctx):
        if self.current_song != "":
            await ctx.send(
                "```\nCurrent song's name is: {}\n```".format(
                    self.current_song[0]["title"]
                )
            )
        else:
            await ctx.send("There is no current song! 🛑")

    @commands.command(aliases=["skip", "s"])
    async def _skip(self, ctx=None):
        if self.voice_channel != "" and self.voice_channel:
            self.voice_channel.pause()
            await self.play_music()

    @commands.command(aliases=["clear", "c"])
    async def _clear(self, ctx=None):
        if self.voice_channel != "" and self.voice_channel:
            await self.mutex_playlist.acquire()
            try:
                self.voice_channel.stop()
                self.playlist = []
                self.is_playing = False
                self.current_song = ""
            finally:
                self.mutex_playlist.release()

    @commands.command(aliases=["remove", "r"])
    async def _remove(self, ctx, *args):
        query = " ".join(args)
        try:
            if len(self.playlist) == 0:
                raise EmptyPlaylistException
            int_arg = int(query)
            if int_arg < 1 or int_arg > len(self.playlist):
                raise PlaylistBoundsException(f"{int_arg}")
            await self.mutex_playlist.acquire()
            try:
                self.playlist.pop(int_arg - 1)
            finally:
                self.mutex_playlist.release()

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
            await self._clear()
