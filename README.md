# Media controller, that observes and playes media on a dlna renderer.

Scripts are written for Python3.

Has endpoints to control a dlna media renderer via REST-ful commands.
/pause and /stop endpoints, as well as /state (to retrieve the current state) for renderer.

/play allowes to:
- define a url to play
- allowes to loop the playback
- allowes to define a title and/or artist search that is run against a mediaserver and play a random result

It is somehow interconnected to these other projects of mine:
- https://github.com/derHeinz/dlna (this project has a copy of this within it's own sources)
- https://github.com/derHeinz/voicecommand (that uses this project's server)

TODOs
- [x] has a /info endpoint to see config
- [x] should also observe "non-looping" playback, because it otherways thinks it's always running!
- [x] play should return a "description" describing the current state (e.g. 'spiele Lieder von Queen').
- [x] possibility to control 2 or more media renderers.
- [x] ability to search/play video also
- [ ] allow several media servers
- [ ] handle (connection) errors when communicating to player (get_state, play, pause, stop)
- [ ] handle (connection) errors when communicating to mediaserver -> and return text "cannot find on mediaserver" or sth.