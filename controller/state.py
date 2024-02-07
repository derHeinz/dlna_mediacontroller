from dataclasses import dataclass
import datetime

from dlna.mediaserver import Item


@dataclass
class StateView():
    loop: bool
    last_played_url: str
    last_played_artist: str
    last_played_title: str
    running: bool
    running_start_datetime: str
    played_count: int
    description: str
    stop_reason: str


class State():

    # reset request
    url: str
    title: str
    artist: str
    loop: bool

    # reset current state
    running: bool
    running_start_datetime: str
    search_response: any
    played_count: int
    description: str
    stop_reason: str

    def __init__(self) -> None:
        self._initial_values()

        # these are historical information
        self.last_played_url = None
        self.last_played_item: Item = None

    def _initial_values(self):
        # reset request
        self.url = None
        self.title = None
        self.artist = None
        self.loop = False

        # reset current state
        self.running = False
        self.running_start_datetime = None
        self.search_response = None
        self.played_count = 0
        self.description = "Aus"
        self.stop_reason = None

    def stop(self, reason: str = None):
        self._initial_values()
        self.stop_reason = reason

    def _title_and_artist(self):
        title = self.last_played_item.get_title() if self.last_played_item is not None else None
        artist = self.last_played_item.get_actor() if self.last_played_item is not None else None
        return (title, artist)

    def _calculate_description(self):
        if self.loop:
            if self.url:
                return "Wiederholt " + self.url
            msg = "Spielt Lieder"
            # take the information from request
            if self.artist:
                msg += " von " + self.artist
            if self.title:
                msg += " mit '" + self.title + "'"
            return msg
        else:
            msg = "Spielt"
            if self.url:
                return msg + " " + self.url
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

    def now_playing(self, url, item):
        self.running = True
        self.running_start_datetime = datetime.datetime.now().isoformat()
        self.played_count += 1
        self.last_played_url = url
        self.last_played_item = item
        self.description = self._calculate_description()

    def view(self):
        title, artist = self._title_and_artist()
        return StateView(self.loop, self.last_played_url, artist, title, self.running, self.running_start_datetime,
                         self.played_count, self.description, self.stop_reason)
