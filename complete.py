from picamera import PiCamera       # Handles setting up the camera object
from gpiozero import Button         # Easily lets us use buttons
from datetime import datetime       # For time and timezones
from pytz import timezone           # For time and timezones
import time                         # This allows the sleep function so everything times correct
import threading                    # Allows backgrounding of the video recording process, which allows
                                    # # # us to have accurate door closing times
import subprocess                   # Enable threading of data offloading

button = Button(4)
camera = PiCamera()

device_name = 'freezer_one'         #Define a friendly device name to easily identify video
record_time = 5                     #Define the number of seconds we want to record
camera.resolution = (1920, 1080)    #Define the resolution we want the video to be at

upload_server = '192.168.43.147'
upload_user = 'root'
privkey_location = '/home/pi/Desktop/id_rsa'
upload_destination = '/root/video'

def record_video(record_time):
    print("Recording video at " + current_time)
    camera.start_preview()
    file_name = '/home/pi/Desktop/' + device_name + current_time + '.h264'
    camera.start_recording(file_name)
    time.sleep(record_time)
    camera.stop_recording()
    camera.stop_preview()
    scp_command = "scp -i " + privkey_location + " " + file_name + " " + upload_user + "@" + upload_server + ":" + upload_destination
    print(scp_command)
    subprocess.call([scp_command])
    return;

def upload_video(file_name):
    print file_name

while True:
    current_time = datetime.now(timezone('US/Eastern')).strftime('%Y-%m-%d_%H-%M-%S')
    if button.is_pressed:
        print("The door was opened at " + current_time)
        #record_time = 5
        print("Recording video for " + str(record_time) + " seconds")
        background_thread = threading.Thread(target=record_video, args=[record_time])
        background_thread.start()
        time.sleep(1) # Do this so release message doesn't get jumbled
        print("Waiting for door to close...")
        button.wait_for_release()

    else:
        print("The door was closed at " + current_time)
        button.wait_for_press()
