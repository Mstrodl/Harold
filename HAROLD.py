import os
import time
import csh_ldap
import requests
import pygame
import RPi.GPIO as GPIO
import config

sudoPassword = config.SUDO_PASSWORD

os.system('echo %s|sudo modprobe wire timeout=1 slave_ttl=5' % (sudoPassword))
os.system('echo %s|sudo modprobe w1-gpio' % (sudoPassword))
os.system('echo %s|sudo modprobe w1-smem' % (sudoPassword))
os.system('echo %s|sudo chmod a+w /sys/devices/w1_bus_master1/w1_master_slaves' % (sudoPassword))
os.system('echo %s|sudo chmod a+w /sys/devices/w1_bus_master1/w1_master_remove' % (sudoPassword))
os.system('echo %s|sudo chmod a+w /sys/devices/w1_bus_master1/w1_master_search' % (sudoPassword))
base_dir = '/sys/devices/w1_bus_master1/w1_master_slaves'
delete_dir = '/sys/devices/w1_bus_master1/w1_master_remove'

instance = csh_ldap.CSHLDAP("uid=nfatkhiyev,cn=users,cn=accounts,dc=csh,dc=rit,dc=edu", config.PASSWORD)

HAROLD_AUTH = config.harold_auth

pygame.mixer.init()

def main():
    ID = " "
    songsPlayed = 0
    while True:
        while True:
            time.sleep(0.5)
            f = open(base_dir, "r")
            ID = f.readline()
            time.sleep(0.1)
            f.close()
            if ID != 'not found.\n':
                print(ID)
                pygame.mixer.music.load("scanComplete")
                pygame.mixer.music.play()
                time.sleep(3)
                while True:
                    f2 = open(base_dir, "r")
                    test = f2.readline()
                    f2.close()
                    if test != 'not found.\n':
                        d = open(delete_dir, "w")
                        d.write(test)
                        continue
                    else:
                        print("iButton read file is clean")
                        break
                break
            else:
                print("Waiting")

        ID = "*" + ID[3:].strip() + "01"
        gets3Link(getAudiophiler(getUID(ID)))
        try:
            pygame.mixer.music.load("music")
            pygame.mixer.music.play()

            while True:
                if pygame.mixer.music.get_busy() == False or pygame.mixer.music.get_pos()/1000 > 30:
                    break
            pygame.mixer.music.stop()
            deleteMusic()
        except:
            os.system('vlc --stop-time 30 music --sout-al vlc://quit')

        ID =""
        print("FINISHED")

def getUID(iButtonCode):
    user = instance.get_member_ibutton(iButtonCode)
    UID = user.uid
    return UID

def getAudiophiler(UID):
    getHaroldURL = "https://audiophiler.csh.rit.edu/get_harold/" + UID
    params = {
        'auth_key':HAROLD_AUTH
    }
    try:
        s3Link = requests.post(url = getHaroldURL, json = params)
        print(s3Link.text)
        return s3Link.text
    except:
        print(e)
        getDefaultURL = "https://audiophiler.csh.rit.edu/get_harold/nfatkhiyev"
        paramsD = {
            'auth_key':HAROLD_AUTH
        }
        defaultLink = requests.post(url = getDefaultURL, json = paramsD)
        return defaultLink.text

def gets3Link(link):
    try:
        music = requests.get(link, allow_redirects=True)
        open('music', 'wb').write(music.content)
    except:
        music = requests.get(getAudiophiler("nfatkhiyev"), allow_redirects=True)
        open('music', 'wb').write(music.content)

def deleteMusic():
    os.remove("music")

if __name__ == '__main__':
    main()