#!/usr/bin/env python3
import soco, os, sys, subprocess, socket, http, time, lib

# Record voice
os.chdir(sys.path[0])
lib.clear()
rec_proc = subprocess.Popen(["arecord", "-f", "cd"], stdout=open("lyd.wav", "w"), stderr=open("/dev/null"))
input("Press RETURN when you are done recording")
rec_proc.terminate()
print("Done!")

# Start webserver
server_proc = subprocess.Popen(["python3", "-m", "http.server", "8316"], stdout=open("/dev/null"))

# Get local IP of machine
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip = s.getsockname()[0]
s.close()

# Play on Sonos zone selected by user
lib.clear()
print("Hvilken sone vil du spille lyden på?\n")
zones = []
for i, zone in enumerate(soco.discover()):
    zones.append(zone)
    print(lib.i_to_c(i)+":  ", zone.player_name)
zone = zones[lib.c_to_i(input("\nSkriv bokstaven til ønsket sone: "))]
zone.play_uri("http://"+ip+":8316/lyd.wav")

# Wait some seconds and terminate webserver
time.sleep(2)
server_proc.terminate()
