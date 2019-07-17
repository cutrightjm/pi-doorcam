from picamera import PiCamera       # Handles setting up the camera object
from gpiozero import Button         # Easily lets us use buttons
from datetime import datetime       # For time and timezones
from pytz import timezone           # For time and timezones
import time                         # This allows the sleep function so everything times correct
import subprocess                   # Enable threading of data offloading
import paramiko
import sys
import glob

button = Button(4)
camera = PiCamera()

device_name = 'freezer_one'         #Define a friendly device name to easily identify video
record_time = 5                     #Define the number of seconds we want to record
camera.resolution = (1920, 1080)    #Define the resolution we want the video to be at
log_file = '/home/pi/Desktop/' + device_name + '.log'

isRecording = 0                     # Maintains state of recording operation

upload_server = '10.0.0.14'                # Define the server to upload to
upload_user = 'administrator'                            # Define a non-root user to log in as
privkey_location = '/home/pi/Desktop/id_rsa2'    # Add full path to private key for passwordless logon
upload_destination = '/home/administrator/Videos/Door_Alarm_Videos/' + device_name + '/'           # Add upload destination on remote server

beep_server = '10.0.0.14'
beep_user = 'ubuntu'

opening_beep = 'play -n synth 0.2 sin 440 && play -n synth 0.2 sin 880'
open_beep = 'while true; do `play -n synth 0.2 sin 440 && play -n synth 0.2 sin 440`; sleep 2; done'
closing_beep = 'play -n synth 0.2 sin 880 && play -n synth 0.2 sin 440'

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(log_file, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass

sys.stdout = Logger()

ssh_beep = paramiko.SSHClient()
ssh_upload = paramiko.SSHClient()
key = paramiko.RSAKey.from_private_key_file(privkey_location)
ssh_beep.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_upload.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try: # Attempt to establish first SSH session
    print("Attempting to connect with SSH...")
    ssh_beep.connect(beep_server, username = beep_user, pkey = key)
    print("Beeper connection successful")
except paramiko.SSHException:
    print("Connection failed! Attempt to troubleshoot SSH.")

try: # Attempt to establish data upload connection
    ssh_upload.connect(upload_server, username = upload_user, pkey = key)
    print("Data upload connection successful")
except paramiko.SSHException:
    print("Connection failed! Attempt to troubleshoot SSH.")

def record_video():
    global file_name
    global video_name
    print("... Recording video at " + current_time)
    camera.start_preview()
    video_name = device_name + current_time + '.h264'
    file_name = '/tmp/' + video_name
    print("... The file_name is set to " + file_name)
    camera.start_recording(file_name)
    return;

def upload_old():
    files = glob.glob('/tmp/*.h264')
    print(files)
    #sftp_client.put(files.pop[0], upload_destination)

    return;

while True:
    current_time = datetime.now(timezone('US/Eastern')).strftime('%Y-%m-%d_%H-%M-%S')
    if button.is_pressed:
        if isRecording == 0:
            print("The door was opened at " + current_time)
            stdin,stdout,stderr=ssh_beep.exec_command(opening_beep)
            print("... Begin video recording")
            record_video()
            isRecording = 1
            print("... Waiting for door to close")
        else:
            pass

    else:
        button.wait_for_release()
        if isRecording == 1:
            isRecording = 0
            print("The door was closed at " + current_time)
            stdin,stdout,stderr=ssh_beep.exec_command(closing_beep)
            print("... Recording for an additional " + str(record_time) + " seconds")
            time.sleep(record_time)
            camera.stop_recording()
            camera.stop_preview()
            print("... Beginning data upload to " + upload_server)
            try:
                final_destination = upload_destination + video_name
                sftp_client = ssh_upload.open_sftp()
                sftp_client.put(file_name, final_destination)
                print("... Data upload successful.")
                delete_command = ['rm', file_name]
                print("... Deleting file " + file_name)
                subprocess.call(delete_command)

                upload_old()

                ssh_beep.close()
                ssh_upload.close()
            except Exception as error:
                print("... Error: " + str(error))
                print("... Unable to upload file! Quitting upload; not deleting file")
                print("... Upload of " + file_name + " will be attempted next time.")
                pass

            try: # Re-establish an SSH connection in case last one failed.
                ssh_beep.connect(beep_server, username = beep_user, pkey = key)
            except paramiko.SSHException:
                print("Connection failed! Attempt to troubleshoot SSH.")

            try:
                ssh_upload.connect(upload_server, username = upload_user, pkey = key)
            except paramiko.SSHException:
                print("Connection failed! Attempt to troubleshoot SSH.")

        else:
            print("\nWaiting for door to open")
            button.wait_for_press()
