#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import soco, os, sys, subprocess, socket, http, time, shutil, string

def clear():
    os.system("clear")

def i_to_c(i):
    return string.ascii_uppercase[i]
def c_to_i(c):
    return (c in string.ascii_uppercase and string.ascii_uppercase.index(c)) or (c in string.ascii_lowercase and string.ascii_lowercase.index(c)) or 0

# Record voice
clear()
start = time.time()
if shutil.which("arecord"):
    rec_proc = subprocess.Popen(["arecord", "-f", "cd"], stdout=open(".lyd.wav", "w"), stderr=open("/dev/null"))
elif shutil.which("sox"):
    rec_proc = subprocess.Popen(["sox", "-e", "u-law", "-d", ".lyd.wav"], stdout=open("/dev/null"), stderr=open("/dev/null"))
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
print(i_to_c(len(zones))+":   Ikke spill av likevel")
zones.append(dummy_zone())
zone = zones[c_to_i(input("\nSkriv bokstaven til ønsket sone: "))]
old_vol = zone.volume
zone.volume = 70
zone.play_uri("http://"+ip+":8318/.lyd.wav")

# Wait some seconds and terminate webserver
time.sleep(recording_length+2)
zone.volume = old_vol
server_proc.terminate()
os.remove(".lyd.wav")
