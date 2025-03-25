# Media controller, that observes and playes media on a dlna renderer.
When given a command it infinitely plays items from your media-servers' library to a TV set or media-player.

### Technical details
Scripts are written for Python >= 3.10

Uses DLNA renderers as playback devices and DLNA media-servers as media libraries.

Has endpoints to control a dlna media renderer via REST-ful commands.
/play, /pause and /stop endpoints, as well as /state (to retrieve the current state) for renderer.

/play allowes to:
- define a url to play
- play an item or url once
- allowes to loop the playback
- allowes to define a title and/or artist, searches that in the media-server, and plays resulting items.

### References
It is somehow interconnected to these other projects of mine:
- https://github.com/derHeinz/dlna (this project has a copy of this within it's own sources) -> hopefully beeing replaced by library upnpclient soon.
- https://github.com/derHeinz/voicecommand (that uses this project's server)

### Features and Planned/Wanted Features:
- [x] has a /info endpoint to see config
- [x] should also observe "non-looping" playback, because it otherways thinks it's always running!
- [x] play should return a "description" describing the current state (e.g. 'spiele Lieder von Queen').
- [x] possibility to control 2 or more media renderers.
- [x] ability to search/play video also
- [x] use dlna/upnpn library, for fewer code: upnpclient
- [x] use "SetNextAVTransportURI" for smoother transitions between tracks
- [ ] allow several media servers
- [ ] handle (connection) errors when communicating to player (get_state, play, pause, stop)
- [ ] handle (connection) errors when communicating to mediaserver -> and return text "cannot find on mediaserver" or sth.