#main imports
import os
import time
import csh_ldap
import requests
import pygame
import vlc
import serial
import LIGHT_BAR
import AUDIO_PROCESSING
from pygame import mixer
import RPi.GPIO as GPIO

#import the config file
import config

#set config password
sudoPassword = config.SUDO_PASSWORD

#setup Serial Coms
ser = serial.Serial('/dev/ttyACM0',9600)
ser_light = serial.Serial('/dev/ttyACM1',9600)

#create an instance
instance = csh_ldap.CSHLDAP(config.LDAP_BIND_DN, config.PASSWORD)

#authentication config file
HAROLD_AUTH = config.harold_auth

pygame.mixer.init()

time_now = time.localtime()

max_counter = 0

LIGHT_BAR.setup_light_bar_gpio()

global beat_array
beat_array = []

global harold_analyzed
harold_analyzed = False

#main function
def main():
    LIGHT_BAR.reset()

    ID = ""

    #keep the whole program running so it doesn't play one song and stop
    while True:
        #while loop per song
        while True:
            if 23 >= time_now.tm_hour >= 7:
                os.system("amixer set Master 73%")
            else:
                os.system("amixer set Master 20%")
            
            #if I-Button is found play scanComplete
            if ser.in_waiting > 6:
                ID = ser.readline().decode('ascii')
                ser.flushInput()
                if ID is None or 'ready' in ID:
                    print("Waiting")
                    continue
                print(ID)
                #Strip the read id of the family code and replaces it with star
                ID = "*" + ID[2:].strip()
                UID = get_uid(ID)
                if UID == "mom":
                    play_music_pygame("aaa", 22, False, False, UID)
                    break
                play_music_pygame("scanComplete", 10, False, False, UID)
                break
            else:
                print("Waiting")
                continue
        #try to play music with pygame and if you can't play the music then quit the vlc process
        try:
            #play the music file with pygame for max of 30 seconds and also flush serial
            play_music_pygame("music", 30, True, True, UID)
        #if music is unplayable in pygame, use vlc
        except Exception as e:
            print(e)

            os.system("ffmpeg -i music music.wav")
            play_music_pygame("music.wav", 30, True, True, UID)

        finally:
            delete_music()

        #reset variables
        ID = ""
        print("FINISHED")

#getUID with the I-Button as an arg
def get_uid(iButtonCode):
    user = instance.get_member_ibutton(iButtonCode)
    UID = user.uid
    return UID

#getAudiophiler with UID as an arg
def get_audiophiler(UID):
    get_harold_url = "https://audiophiler.csh.rit.edu/get_harold/" + UID
    params = {
        'auth_key':HAROLD_AUTH
    }
    try:
        s3_link = requests.post(url = get_harold_url, json = params)
        print(s3_link.text)
        return s3_link.text
    except Exception as e:
        print(e)
        return "getAudiophiler ERROR"

#gets3Link with the Link as an arg
def get_s3_link(link):
    try:
        music = requests.get(link, allow_redirects=True)
        open('music', 'wb').write(music.content)
    except Exception as e:
        print(e)
        return "gets3Link ERROR"

#plays music till done or limit t has been reached
#last parameter dictates wheter or not the serial line is flushed at the end of the song
def play_music_pygame(music, t, flush_serial, light, UID):
    global harold_analyzed

    pygame.mixer.music.load(music)
    pygame.mixer.music.play()

    if not harold_analyzed:
        #Download te song from the s3_link
        get_s3_link(get_audiophiler(UID))
        beat_array = AUDIO_PROCESSING.get_beat_times()
        harold_analyzed = True
        
    elif harold_analyzed:
        harold_analyzed = False

    i = 0

    while True:
        if light:
            time1 = pygame.mixer.music.get_pos() / 1000
            if i < len(beat_array) and time1 > beat_array[i]:
                print(beat_array[i])
                i+=1
                print("beat")
                LIGHT_BAR.set_light_bar(LIGHT_BAR.get_random_gpio_state(), LIGHT_BAR.get_random_gpio_state(), LIGHT_BAR.get_random_gpio_state())
                msg = ser_light.write(b'7')
                print(msg)
                time.sleep(0.01)
                
            #LIGHT_BAR.set_light_bar(LIGHT_BAR.get_random_gpio_state(), LIGHT_BAR.get_random_gpio_state(), LIGHT_BAR.get_random_gpio_state())
            
        if pygame.mixer.music.get_busy() == False or pygame.mixer.music.get_pos()/1000 > t:
            break
    if flush_serial:
        ser.flushInput()
    pygame.mixer.music.stop()
    LIGHT_BAR.reset()

#remove the music file from the directory
def delete_music():
    os.remove("music")
    try:
        os.remove("music.wav")
    except:
        print("no music.wav")
#run main
if __name__ == '__main__':
    main()
