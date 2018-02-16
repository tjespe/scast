#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, subprocess, socket, http, time, shutil, string
from shutil import copy2 as copy

def param_present(x):
    return "-"+x in sys.argv

def get_param_val(x, fallback=None):
    return fallback if not "-"+x in sys.argv or len(sys.argv) <= sys.argv.index("-"+x) + 1 else sys.argv[sys.argv.index("-"+x) + 1]

# Try to import SoCo and offer auto installation if it is unavailable
try:
    import soco
except ModuleNotFoundError:
    if input("You need the SoCo module to run this script. Do you want to attempt automatic installation?  [y/N]: ").lower() == "y":
        if shutil.which("pip3"):
            os.system("sudo pip3 install soco")
            import soco
        else:
            from platform import system
            if system() == "Darwin":
                if shutil.which("brew"):
                    os.system("brew install python3")
                else:
                    os.system('/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"')
                    os.system("brew install python3")
                    os.system("sudo pip3 install soco")
                    import soco
            elif shutil.which("apt"):
                os.system("apt install python3-pip")
            else:
                print("\n\nSorry, no automatic installation is configured for your system. Please try to install pip3 and then type `sudo pip3 install soco`")
                quit()
    else:
        quit()

# Try to update automatically
newest_update, root_required = "", False
try:
    if not param_present("-no-update"): # Command line flag --no-update can be used to prevent auto update
        def update_script():
            global newest_update, root_required
            from urllib import request
            with request.urlopen('https://raw.githubusercontent.com/tjespe/scast/master/scast.py?time='+str(int(time.time()))) as response:
               newest_update = response.read().decode("utf-8")
            if open(__file__, "r").read() != newest_update:
                try:
                    open(__file__, "w").write(newest_update)
                except PermissionError:
                    root_required = True
        import threading
        update_thread = threading.Thread(target=update_script)
        update_thread.start()
except:
    pass # Fail silently

def i_to_c(i):
    return string.ascii_uppercase[i]
def c_to_i(c):
    return (c in string.ascii_uppercase and string.ascii_uppercase.index(c)) or (c in string.ascii_lowercase and string.ascii_lowercase.index(c)) or 0

if get_param_val("f"): # Audio file is specified as command line option
    if get_param_val("l"):
        recording_length = int(get_param_val("l"))
    else:
        print("Since you did not specify length on the command line (using -l option) the file will be played for 10 seconds")
        recording_length = 10
    if get_param_val("f").endswith(".wav"):
        copy(get_param_val("f"), ".lyd.wav")
    else:
        if shutil.which("ffmpeg"):
            if param_present("-debug"):
                print("Converting file...")
            conv_proc = subprocess.run(["ffmpeg", "-i", get_param_val("f"), ".lyd.wav"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if param_present("-debug"):
                print(conv_proc.stdout.decode(), conv_proc.stderr.decode())
                print("Playing file...")
        else:
            print("The file you specified was not a .wav file and this script did not find ffmpeg installed. Either use a .wav file or install ffmpeg.")
            quit(1)
    volume = int(get_param_val("v")) if get_param_val("v") else 60
else:
    # Start clock
    start = time.time()
    # Record voice
    if shutil.which("arecord"):
        rec_proc = subprocess.Popen(["arecord", "-f", "cd"], stdout=open(".lyd.wav", "w"), stderr=open("/dev/null"))
        volume = 35
    elif shutil.which("sox"):
        rec_proc = subprocess.Popen(["sox", "-e", "u-law", "-d", ".lyd.wav"], stdout=open("/dev/null"), stderr=open("/dev/null"))
        volume = 70
    else:
        if input("\n\nYou need to install either arecord or sox to use this program interactively. Do you want to attempt automatic installation? [y/N]: ").lower() == "y":
            from platform import system
            if system() == "Darwin":
                if shutil.which("brew"):
                    os.system("brew install sox")
                else:
                    os.system('/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"')
                    os.system("brew install sox")
                rec_proc = subprocess.Popen(["sox", "-e", "u-law", "-d", ".lyd.wav"], stdout=open("/dev/null"), stderr=open("/dev/null"))
                volume = 70
            else:
                print("\n\nNo automatic installation is configured for your system. If you are on Linux and have apt installed you can try to type `sudo apt install arecord`")
                quit()
        else:
            quit()
    input("Press the ENTER key when you are done recording")
    recording_length = time.time() - start
    rec_proc.terminate()

# Start webserver
server_proc = subprocess.Popen(["python3", "-m", "http.server", "8318"], stdout=open("/dev/null"), stderr=open("/dev/null"))

# Get local IP of machine
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip = s.getsockname()[0]
s.close()

# Play on Sonos zone(s) selected by user
target_zones = []
zones_data = []
if not get_param_val("z"):
    print("\n\nIn which zone do you wish to play the recording?\n")
    zones = []
    for i, zone in enumerate(soco.discover()):
        zones.append(zone)
        print(i_to_c(i)+":  ", zone.player_name)
    print(i_to_c(len(zones))+":   Don't play it")
    i = c_to_i(input("\nWrite the letter of the zone: "))
    if len(zones) > i: # Make sure user did not change their mind
        target_zones.append(zones[i])
        zones_data.append({})
else:
    for i, zone in enumerate(soco.discover()):
        if get_param_val("z") == "all" or zone.player_name == get_param_val("z"):
            target_zones.append(zone)
            zones_data.append({})

# Loop through target zones, save state and play sound
for i, zone in enumerate(target_zones):
    zones_data[i]["vol"] = zone.volume
    zones_data[i]["track_info"] = zone.group.coordinator.get_current_track_info()
    zones_data[i]["queue_index"] = int(zones_data[i]["track_info"]["playlist_position"]) - 1
    zones_data[i]["pos"] = zones_data[i]["track_info"]["position"]
    zones_data[i]["uri"] = zones_data[i]["track_info"]["uri"]
    zones_data[i]["was_playing"] = zone.group.coordinator.get_current_transport_info()['current_transport_state'] == "PLAYING"
    zone.group.coordinator.play_uri("http://"+ip+":8318/.lyd.wav")
    zone.volume = volume

# Wait the appropriate amount of seconds
if len(target_zones):
    time.sleep(recording_length)

# Revert each zone back to previous state
for i, zone in enumerate(target_zones):
    zone.volume = zones_data[i]["vol"]
    try:
        # zone.group.coordinator.play_from_queue(queue_index)
        zone.group.coordinator.play_from_queue(zones_data[i]["queue_index"])
        zone.group.coordinator.seek(zones_data[i]["pos"])
    except soco.exceptions.SoCoUPnPException:
        try:
            zone.group.coordinator.play_uri(zones_data[i]["uri"])
        except soco.exceptions.SoCoUPnPException:
            pass
    if not zones_data[i]["was_playing"]:
        try:
            zone.group.coordinator.pause()
        except soco.exceptions.SoCoUPnPException:
            pass

# Stop server and delete sound file
server_proc.terminate()
os.remove(".lyd.wav")

# Prompt for password to update this script if necessary
if root_required:
    try:
        from pipes import quote
        from getpass import getpass
        password = getpass("\nAn update of this script is available. Since administrator priviliges are required to modify this script, please enter your password: ")
        command = "echo "+quote(newest_update.rstrip())+" |sudo tee "+quote(__file__)+" > /dev/null"
        os.system("echo %s|sudo -S %s" % (password, command))
    except Exception as e:
        if param_present("-debug"):
            print(e)
