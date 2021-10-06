# OBS PSN Trophies

This is a WIP script for grabbing information from PSN and displaying it on stream. It only uses the Python standard library. I think this is a limitation of using Python shared libraries, which is the case with OBS.

[psn.py](psn.py) implements minimal functionality for calls to the Playstation Trophies API V2, which is documented [here](https://andshrew.github.io/PlayStation-Trophies/#/APIv2?id=playstation-trophies-api-v2). It's a little slow since afaik urllib doesn't let you make persistent connections. It looks like you can with http.client, so I might refactor this.

Once this becomes actually usable, I'll write more documentation 🙃