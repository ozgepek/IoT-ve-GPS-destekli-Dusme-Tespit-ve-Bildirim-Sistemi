from PiicoDev_MPU6050 import PiicoDev_MPU6050
from PiicoDev_Unified import sleep_ms
import time
import network
import urequests
from machine import Pin, UART
import utime
from math import sqrt


motion = PiicoDev_MPU6050()
fall = False
trigger1 = False
trigger2 = False
trigger3 = False
trigger1count = 0
trigger2count = 0
trigger3count = 0
angleChange = 0
statusGPS = True

gpsModule = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))



TIMEOUT = False
FIX_STATUS = False
counterGPS = 0




wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("wifi ad","wifi sifre")
time.sleep(5)
print(wlan.isconnected())

url = "https://www.google.com/maps/search/?api=1&query=" 
def mesaj_gonder():
    
    gps_readings = {'value1':url}

    request_headers = {'Content-Type': 'application/json'}
    request = urequests.post(
    'https://maker.ifttt.com/trigger/EVENT NAME/with/key/API KEY',
    json=gps_readings,
    headers=request_headers)
    print("mesaj gönderildi")



def getGPS(gpsModule):
    global statusGPS, counterGPS
    
    timeout = utime.time() + 8
    start_time = utime.time()
    
    while counterGPS <=  20:   
        
        counterGPS = counterGPS + 1 
        
        if gpsModule.any():
            line = gpsModule.readline()
            parts = line.split(b',')
            
            statusGPS = False
            
            if len(parts) == 15 and parts[0] == b'$GPGGA':
                fix = parts[6]
                if fix == b'0':
                    continue
                
                latitude = convertToDegree(parts[2], parts[3])
                longitude = convertToDegree(parts[4], parts[5])
                satellites = parts[7].decode()
                GPStime = parts[1][0:2].decode() + ":" + parts[1][2:4].decode() + ":" + parts[1][4:6].decode()
                
                x = [latitude,longitude] 
                print(x)
                return x

        
        if utime.time() - start_time > 1:
            start_time = utime.time()
            gpsModule.write(b"$PMTK220,100*2F\r\n")  # Set update rate to 10Hz
        
        utime.sleep_ms(100)
        
        if counterGPS >= 21:
            counterGPS = 0
                

def convertToDegree(raw_degrees, direction):
    raw_float = float(raw_degrees)
    degrees = int(raw_float / 100)
    minutes = (raw_float % 100) / 60.0
    converted = degrees + minutes
    
    if direction == b'S' or direction == b'W':
        converted = -converted
    
    converted = "{0:.6f}".format(converted)
    return converted


    
while True:
    
   
    accel = motion.read_accel_data() # [ms^-2]
    aX = accel["x"]
    aY = accel["y"]
    aZ = accel["z"]
    
    gyro = motion.read_gyro_data()   # [deg/s]
    gX = gyro["x"]
    gY = gyro["y"]
    gZ = gyro["z"]

    Amp=motion.read_accel_abs(False)
    print(Amp)
    if Amp <= 4 and not trigger2:
        trigger1 = True
        print("TRIGGER 1 AKTİF")

    if trigger1:
        trigger1count += 1
        if Amp >= 12:
            trigger2 = True
            trigger1 = False
            trigger1count = 0
            print("TRIGGER 2 AKTİF")

    if trigger2:
        trigger2count += 1
        ozge = motion.read_gyro_data()
        angleChange=sqrt(ozge['x']**2+ozge['y']**2+ozge['z']**2)
        if 30 <= angleChange <= 400:
            trigger3 = True
            trigger2 = False
            trigger2count = 0
            print(angleChange)
            print("TRIGGER 3 AKTİF")

    if trigger3:
        trigger3count += 1
        if trigger3count >= 10:
            ozge = motion.read_gyro_data()
            angleChange=sqrt(ozge['x']**2+ozge['y']**2+ozge['z']**2)
         
            print(angleChange)
            if 0 <= angleChange <= 11:
                fall = True
                trigger3 = False
                trigger3count = 0
                print(angleChange)
            else:
                trigger3 = False
                trigger3count = 0
                print("TRIGGER 3 KAPATILDI")

    if fall:
        print("DUSME GERCEKLESTI")
        fall = False
        
        fallGPS = getGPS(gpsModule)
        print(fallGPS)
        url = "https://www.google.com/maps/search/?api=1&query=" + str(fallGPS[0]) + '+' + str(fallGPS[1])
        mesaj_gonder()
        statusGPS = True

    if trigger2count >= 6:
        trigger2 = False
        trigger2count = 0
        

    if trigger1count >= 6:
        trigger1 = False
        trigger1count = 0
        
    
    sleep_ms(100)
