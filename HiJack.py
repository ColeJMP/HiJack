# pyinstaller --onefile --noconsole --add-data "lizard-button.mp3;." HiJack.py
import os
import sys
import threading
import time
from pynput import keyboard, mouse
import pygame
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from pynput.keyboard import Controller, Key

keyboard_controller = Controller()

def hold_volume_up():
    while True:
        # Press and release the volume up key
        keyboard_controller.press(Key.media_volume_up)
        keyboard_controller.release(Key.media_volume_up)
        time.sleep(1)  # Press once every second

# Start the hold_volume_up thread
volume_up_thread = threading.Thread(target=hold_volume_up, daemon=True)
volume_up_thread.start()


# Get the directory where the script or EXE is located
def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)

MP3_PATH = resource_path("lizard-button.mp3")

# Initialize pygame mixer
pygame.mixer.init()
sound = pygame.mixer.Sound(MP3_PATH)

# Volume control setup
def force_max_volume():
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterScalarVolume(1.0, None)
        volume.SetMute(False, None)
    except Exception as e:
        print("Failed to set volume:", e)

def play_sound():
    def play_in_thread():
        sound.set_volume(1.0)
        sound.play()
    threading.Thread(target=play_in_thread, daemon=True).start()

# Keep track of pressed keys and mouse buttons
pressed_keys = set()
pressed_buttons = set()
input_lock = threading.Lock()

def on_key_press(key):
    with input_lock:
        pressed_keys.add(key)
    
    # Don't play sound for volume up key
    if key != Key.media_volume_up:
        play_sound()

def on_key_release(key):
    with input_lock:
        pressed_keys.discard(key)

def on_click(x, y, button, pressed):
    with input_lock:
        if pressed:
            pressed_buttons.add(button)
            play_sound()
        else:
            pressed_buttons.discard(button)

def volume_monitor():
    while True:
        with input_lock:
            if not pressed_keys and not pressed_buttons:
                # No keys or buttons pressed: force volume
                force_max_volume()
        time.sleep(0.2)

# Start volume monitor thread
volume_thread = threading.Thread(target=volume_monitor, daemon=True)
volume_thread.start()

# Start listeners
keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
mouse_listener = mouse.Listener(on_click=on_click)

keyboard_listener.start()
mouse_listener.start()

# Force volume at start
force_max_volume()

keyboard_listener.join()
mouse_listener.join()
