import discord
import os
from discord.ext import commands
from youtube_dl import YoutubeDL


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = False
        self.playlist = []
        self.YTDL_OPTIONS = {
            "format": "bestaudio",
            "noplaylist": True,
        }
        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }

        self.voice_channel = ""

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
            self.playlist.pop(0)
            self.voice_channel.play(
                discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                after=lambda f: self.play_next(),
            )
        else:
            self.is_playing = False

    async def play_music(self):
        if len(self.playlist) > 0:
            self.is_playing = True
            m_url = self.playlist[0][0]["source"]

            if (
                self.voice_channel == ""
                or not self.voice_channel.is_connected()
                or self.voice_channel == None
            ):
                self.voice_channel = await self.playlist[0][1].connect()
            else:
                await self.voice_channel.move_to(self.playlist[0][1])

            print(self.playlist)
            self.playlist.pop(0)
            self.voice_channel.play(
                discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                after=lambda f: self.play_next(),
            )
        else:
            self.is_playing = False

    @commands.command()
    async def p(self, ctx, *args):
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
                await ctx.send(
                    "Song {} added to the queue, its current position: {}".format(
                        song["title"], str(len(self.playlist) + 1)
                    )
                )
                self.playlist.append([song, voice_channel])

                if self.is_playing is False:
                    await self.play_music()

    @commands.command()
    async def q(self, ctx):
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

        print(retval)
        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue! 🛑")

    @commands.command()
    async def skip(self, ctx):
        if self.voice_channel != "" and self.voice_channel:
            self.voice_channel.stop()
            await self.play_music()

