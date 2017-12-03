#!/usr/bin/env python3
import soco, os, sys, subprocess, socket, http, time, shutil

def clear():
    os.system("clear")

chars = ["A", "B", "C", "D"]
s_chars = ["a", "b", "c", "d"]
def i_to_c(i):
    return chars[i]
def c_to_i(c):
    return (c in chars and chars.index(c)) or (c in s_chars and s_chars.index(c)) or 0

# Record voice
clear()
start = time.time()
if shutil.which("arecord"):
    rec_proc = subprocess.Popen(["arecord", "-f", "cd"], stdout=open(".lyd.wav", "w"), stderr=open("/dev/null"))
elif shutil.which("sox"):
    rec_proc = subprocess.Popen(["sox", "-d", ".lyd.wav"], stdout=open("/dev/null"), stderr=open("/dev/null"))
else:
    print("You need to install either arecord or sox to use this program.")
    quit()
input("Press RETURN when you are done recording")
recording_length = time.time() - start
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
clear()
print("Hvilken sone vil du spille lyden på?\n")
zones = []
for i, zone in enumerate(soco.discover()):
    zones.append(zone)
    print(i_to_c(i)+":  ", zone.player_name)
zone = zones[c_to_i(input("\nSkriv bokstaven til ønsket sone: "))]
zone.play_uri("http://"+ip+":8316/.lyd.wav")

# Wait some seconds and terminate webserver
time.sleep(recording_length+2)
server_proc.terminate()
os.remove(".lyd.wav")
