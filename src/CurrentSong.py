from dataclasses import dataclass


class IncorrectCurrentSongInstanceException(Exception):
    pass


@dataclass
class CurrentSong:
    song_name: str
    song_url: str

    def clear_info(self):
        self.song_name = ""
        self.song_url = ""

    def is_empty(self):
        if self.song_name == "" and self.song_url == "":
            return True
        elif self.song_name != "" and self.song_url != "":
            return False
        else:
            raise IncorrectCurrentSongInstanceException(
                "One of attributes is empty while other one isn't!"
            )
