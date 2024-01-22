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