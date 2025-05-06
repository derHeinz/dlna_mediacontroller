from dataclasses import dataclass
import datetime

from dlna.items import Item
from controller.data.command import PlayCommand


@dataclass
class StateView():
    looping: bool
    last_played_url: str
    last_played_artist: str
    last_played_title: str
    running: bool
    running_start_datetime: str
    played_count: int
    description: str
    stop_reason: str


class State():

    # the command beeing issued
    current_command: PlayCommand

    # current state for the command beeing issued
    running: bool
    looping: bool
    running_start_datetime: str
    search_response: any
    played_count: int
    description: str
    stop_reason: str

    # items for next play
    next_play_url: str
    next_play_item: Item

    # historical info
    last_played_url: str
    last_played_item: Item

    def __init__(self) -> None:
        self._initial_values()

        self.last_played_url = None
        self.last_played_item: Item = None

    def _initial_values(self):
        # reset request
        self.current_command = None

        # reset current state
        self.running = False
        self.looping = False
        self.running_start_datetime = None
        self.search_response = None
        self.played_count = 0
        self.description = "Aus"
        self.stop_reason = None

        self.next_play_url = None
        self.next_play_item: Item = None

    def _title_and_artist(self):
        title = self.last_played_item.get_title() if self.last_played_item is not None else None
        artist = self.last_played_item.get_actor() if self.last_played_item is not None else None
        return (title, artist)

    def _type_text(self, type: str):
        if type == "audio":
            return "Lieder"
        elif type == "video":
            return "Videos"
        elif type == "image":
            return "Bilder"
        else:
            return "Medien"

    def _calculate_description(self):
        if self.current_command.loop:
            if self.current_command.url:
                return "Wiederholt " + self.current_command.url

            msg = "Spielt " + self._type_text(self.current_command.type)
            # take the information from request
            if self.current_command.artist:
                msg += " von " + self.current_command.artist
            if self.current_command.title:
                msg += " mit '" + self.current_command.title + "'"
            return msg
        else:
            msg = "Spielt"
            if self.current_command.url:
                return msg + " " + self.current_command.url
            title, artist = self._title_and_artist()
            if (title):
                # only plays once, so write full name
                msg += " " + title
                if (artist):
                    msg += " von " + artist
                return msg
            if (artist):
                msg += " etwas von " + artist
        return msg

    def is_url_mode(self):
        """url mode plays the same url, differece to item_mode"""
        if self.current_command is None:
            return False

        if self.current_command.url:
            return True
        return False

    def is_item_mode(self):
        """item mode the mode that search via mediaserver"""
        if self.current_command is None:
            return False

        if self.current_command.url:
            return False
        return True

    def command(self, command: PlayCommand):
        """set the last command issued"""
        self.current_command = command

    def now_playing(self, url, item):
        """it is playing now"""
        self.running = True
        self.looping = self.current_command.loop

        if self.running_start_datetime is None:
            self.running_start_datetime = datetime.datetime.now().isoformat()
        self.played_count += 1
        self.last_played_url = url
        self.last_played_item = item
        self.description = self._calculate_description()

    def next_track_is_playing(self):
        """the next planned track is beeing played, the last one is finished"""
        # move over last
        self.last_played_url = self.next_play_url
        self.last_played_item = self.next_play_item
        # counter
        self.played_count += 1

    def next_play(self, url, item):
        """sets the track played after the current one"""
        self.next_play_url = url
        self.next_play_item = item

    def stop(self, reason: str = None):
        """the playing is stopped NOW"""
        self._initial_values()
        self.stop_reason = reason

    def view(self):
        """function that renders an immutable view"""
        title, artist = self._title_and_artist()
        return StateView(self.looping, self.last_played_url, artist, title, self.running, self.running_start_datetime,
                         self.played_count, self.description, self.stop_reason)
