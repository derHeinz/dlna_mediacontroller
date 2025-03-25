from dataclasses import dataclass


@dataclass
class Command:
    target: str = None


@dataclass
class PlayCommand(Command):
    url: str = None
    artist: str = None
    title: str = None
    target: str = None
    type: str = None
    loop: bool = False

    def isUrlBased(self):
        return self.url is not None
