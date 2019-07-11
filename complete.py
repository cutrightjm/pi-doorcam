from picamera import PiCamera       # Handles setting up the camera object
from gpiozero import Button         # Easily lets us use buttons
from datetime import datetime       # For time and timezones
from pytz import timezone           # For time and timezones
import time                         # This allows the sleep function so everything times correct
import subprocess                   # Enable threading of data offloading

button = Button(4)
camera = PiCamera()

device_name = 'freezer_one'         #Define a friendly device name to easily identify video
record_time = 5                     #Define the number of seconds we want to record
camera.resolution = (1920, 1080)    #Define the resolution we want the video to be at

isRecording = 0                     # Maintains state of recording operation
close_length = 5                    # Record for <n> seconds after closing door

upload_server = '192.168.43.147'                                # Define the server to upload to
upload_user = 'root'                                                    # Define a non-root user to log in as
privkey_location = '/home/pi/Desktop/id_rsa'    # Add full path to private key for passwordless logon
upload_destination = '/root/video'                              # Add upload destination on remote server
upload_path = upload_user + '@' + upload_server + ':' + upload_destination

def record_video():
    global file_name
    print("... Recording video at " + current_time)
    camera.start_preview()
    file_name = '/tmp/' + device_name + current_time + '.h264'
    print("... The file_name is set to " + file_name)
    camera.start_recording(file_name)
    return;

while True:
    current_time = datetime.now(timezone('US/Eastern')).strftime('%Y-%m-%d_%H-%M-%S')
    if button.is_pressed:
        if isRecording == 0:
            print("The door was opened at " + current_time)
            print("... Begin video recording")
            record_video()
            isRecording = 1
            print("... Waiting for door to close")
        else:
            pass

    else:
        button.wait_for_release()
        if isRecording == 1:
            print("The door was closed at " + current_time)
            isRecording = 0
            time.sleep(close_length) # Record specified number of seconds after door closing
            camera.stop_recording()
            camera.stop_preview()
            print("... Recording for an additional " + str(record_time) + " seconds")
            time.sleep(record_time)
            scp_command = ['scp', '-i', privkey_location, file_name, upload_path]
            print("... Beginning data upload to " + upload_server)
            subprocess.call(scp_command)
            delete_command = ['rm', file_name]
            print("... Deleting file " + file_name)
            subprocess.call(delete_command)

        else:
            print("... Waiting for door to open")
            button.wait_for_press()
