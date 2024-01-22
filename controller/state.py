from dataclasses import dataclass

from dlna.mediaserver import SearchResponse, Item


@dataclass
class StateView():
    loop: bool
    last_played_url: str
    last_played_artist: str
    last_played_title: str
    running: bool
    played_count: int


class State():

    def __init__(self) -> None:
        # TODO rename to initial or request or sth.
        self.url: str = None
        self.title: str = None
        self.artist: str = None
        self.loop: bool = False

        # TODO rename to current state variables
        self.running: bool = False
        self.search_response: SearchResponse = None
        self.last_played_url = None
        self.last_played_item: Item = None
        self.played_count: int = 0

    def stop(self):
        # reset request
        self.url = None
        self.title = None
        self.artist = None
        self.loop = False

        # reset current state
        self.search_response = None
        self.played_count = 0
        self.running = False

    def now_playing(self, url, item):
        self.running = True
        self.played_count += 1
        self.last_played_url = url
        self.last_played_item = item

    def view(self):
        title = self.last_played_item.get_title() if self.last_played_item is not None else None
        artist = self.last_played_item.get_actor() if self.last_played_item is not None else None
        return StateView(self.loop, self.last_played_url, artist, title, self.running, self.played_count)
