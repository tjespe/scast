#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import soco, os, sys, subprocess, socket, http, time, shutil, string

def clear():
    os.system("clear")

def i_to_c(i):
    return string.ascii_uppercase[i]
def c_to_i(c):
    return (c in string.ascii_uppercase and string.ascii_uppercase.index(c)) or (c in string.ascii_lowercase and string.ascii_lowercase.index(c)) or 0

# Clear terminal and start clock
clear()
start = time.time()
# Record voice
if shutil.which("arecord"):
    rec_proc = subprocess.Popen(["arecord", "-f", "cd"], stdout=open(".lyd.wav", "w"), stderr=open("/dev/null"))
    volume = 35
elif shutil.which("sox"):
    rec_proc = subprocess.Popen(["sox", "-e", "u-law", "-d", ".lyd.wav"], stdout=open("/dev/null"), stderr=open("/dev/null"))
    volume = 70
else:
    print("You need to install either arecord or sox to use this program.")
    quit()
input("Trykk ENTER når du er ferdig å ta opp lyd")
recording_length = time.time() - start
rec_proc.terminate()
print("Done!")

# Start webserver
server_proc = subprocess.Popen(["python3", "-m", "http.server", "8318"], stdout=open("/dev/null"), stderr=open("/dev/null"))

# Get local IP of machine
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip = s.getsockname()[0]
s.close()

# Play on Sonos zone selected by user
clear()
print("Hvilken sone vil du spille lyden på?\n")
zones = []
for i, zone in enumerate(soco.discover()):
    zones.append(zone)
    print(i_to_c(i)+":  ", zone.player_name)
class dummy_zone():
    def play_uri(a,b):
        server_proc.terminate()
        os.remove(".lyd.wav")
        quit()
    volume = 0
print(i_to_c(len(zones))+":   Ikke spill av likevel")
zones.append(dummy_zone())
zone = zones[c_to_i(input("\nSkriv bokstaven til ønsket sone: "))]
old_vol = zone.volume
track_info = zone.group.coordinator.get_current_track_info()
queue_index = int(track_info["playlist_position"]) - 1
pos = track_info["position"]
old_uri = track_info["uri"]
was_playing = zone.group.coordinator.get_current_transport_info()['current_transport_state'] == "PLAYING"
zone.group.coordinator.play_uri("http://"+ip+":8318/.lyd.wav")
zone.volume = volume

# Wait some seconds and revert state of player into previous state
time.sleep(recording_length)
zone.volume = old_vol
try:
    zone.group.coordinator.play_from_queue(queue_index)
    zone.group.coordinator.seek(pos)
except soco.exceptions.SoCoUPnPException:
    try:
        zone.group.coordinator.play_uri(old_uri)
    except soco.exceptions.SoCoUPnPException:
        pass
if not was_playing:
    try:
        zone.group.coordinator.pause()
    except soco.exceptions.SoCoUPnPException:
        pass
server_proc.terminate()
os.remove(".lyd.wav")
