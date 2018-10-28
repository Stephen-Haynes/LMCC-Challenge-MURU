from network import LoRa
import socket
import time
import binascii
import pycom
import ustruct
from machine import ADC
import time
from machine import Pin, Timer
import utime

debug = False

pin = Pin(Pin.exp_board.G11, mode=Pin.IN, pull=Pin.PULL_UP)
p_out = Pin(Pin.exp_board.G24, mode=Pin.OUT)
p_out.value(0)

echo = Pin(Pin.exp_board.G7, mode=Pin.IN)
trigger = Pin(Pin.exp_board.G8, mode=Pin.OUT)
trigger(0)

def distance_measure():
    trigger(0)
    time.sleep_us(2)
    trigger(1)
    time.sleep_us(10)
    trigger(0)

    while echo() == 0:
        pass

    start = utime.ticks_us()

    while echo() == 1 and utime.ticks_diff(start, utime.ticks_us()) < 15000:
        pass

    finish = utime.ticks_us()
    time.sleep_ms(20)

    #if utime.ticks_diff(start, finish) < 100:
    #    return 1
    #else:
    distance = (utime.ticks_diff(start, finish))

    return distance


def adc_position():

    # initialise adc hardware
    #adc = ADC(0)
    #create an object to sample ADC on pin 16 with attenuation of 11db (config 3)
    #adc_c = adc.channel(attn=3, pin='P20')
    # initialise the list
    adc_samples = []
    # take 10 samples and append them into the list
    for count in range(10):
        adc_samples.append(int(distance_measure()))
    # sort the list
    adc_samples = sorted(adc_samples)
    # take the center list row value (median average)
    adc_median = adc_samples[int(len(adc_samples)/2)]
    # apply the function to scale to volts
    if debug == True:
        print(adc_samples)

    return int(adc_median)


def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = int(value - leftMin) / int(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

# disable LED heartbeat (so we can control the LED)
pycom.heartbeat(False)
# set LED to red
pycom.rgbled(0x640000)

# lora config
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AS923)
# access info
app_eui = binascii.unhexlify('70B3D57ED0012758')
app_key = binascii.unhexlify('E43834D8D7F0D47A7E27B60D125D106A')

def connect():
    reconnect_timeout = 5000
    # set LED to red
    pycom.rgbled(0x640000)
    # attempt join - continues attempts in background
    lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=100000)
    reconnect_start = utime.ticks_ms()
    while not lora.has_joined() and utime.ticks_diff(reconnect_start, utime.ticks_us()) < reconnect_timeout:
        pass

    pycom.rgbled(0x006400)
    if debug == True:
        print('Network joined!')
    time.sleep(1)
    pycom.rgbled(000000) # turn off after blinking green

    test = 0
    testpack = ustruct.pack('f',test)
    s.send(testpack)
    if debug == True:
        print('Sending 0')
    time.sleep(10)

# setup the socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
s.setblocking(False)
s.bind(1)

while True:
    while lora.has_joined():
         # check for a downlink payload, up to 64 bytes
        rx_pkt = s.recv(2)

        # is received packet of two bytes, 'resets' device and connection
        if len(rx_pkt) > 0:
            if debug == True:
                print("Downlink data on port 200:", rx_pkt)
            #initialise global variables
            position_last = 0
            cal_distance = adc_position()
            count = 0
            run_time = 30000 # 1 hour is 3.6e+6 in ms
            current_time = 0
            gap_time_start = utime.ticks_ms()

        #print("Switch Reads: ",pin())
        if pin() == 1: # switch away from usb
            tick = 0 #count for changed readings
            position = 100-translate(adc_position(), 1000, 5000, 0, 100) # translates reading to 1-100
            if debug == True:
                print("Position:  ", position)
                print("Last Position: ", position_last)
            if abs(position - position_last) > 10: # if change is greater than 10%
                for count in range(3): # check readings three times
                    if abs(position-position_last) > 10:
                        tick = tick + 1
                        if debug == True:
                            print("Positive change iterations: ", tick)
                            print("Position change greater than 10%")
                            print("Check back in 1 minute(s)")
                        time.sleep(10)    #1 minute sleep
                        position = 100-translate(adc_position(), 1000, 5000, 0, 100)
            if tick > 2: #if three readings in a row detected change
                position_last = position #update position
                if debug == True:
                    print("Position Updated, sending packet")
                    print("Position:  ", position)
                # encode the packet, so that it's in BYTES (TTN friendly)
                # could be extended like this struct.pack('f',lipo_voltage) + struct.pack('c',"example text")
                packet = ustruct.pack('h', int(position))

                # send the prepared packet via LoRa
                s.send(packet)

                # example of unpacking a payload - unpack returns a sequence of
                #immutable objects (a list) and in this case the first object is the only object
                if debug == True:
                    print ("Unpacked value is:", ustruct.unpack('h',packet)[0])
                pycom.rgbled(0x006400)
                time.sleep(0.5)
                pycom.rgbled(000000) # turn off after blinking green
            time.sleep(30) #30 minutes
        else:
            #position =
            if (cal_distance - distance_measure()) > 500:
                sonic_count = 0
                while (cal_distance - distance_measure()) > 500:
                    if debug == True:
                        print(cal_distance - distance_measure())
                    sonic_count = sonic_count + 1
                    pass

                    #position = adc_position()
                if sonic_count > 1:
                    if utime.ticks_diff(gap_time_start, utime.ticks_ms()) < 500:
                        pass
                    else:
                        count = count + 1
                        gap_time_start = utime.ticks_ms()
            #print("Count: ", count)
            #print (time.ticks_ms())
            #print (current_time)
            if time.ticks_ms() - current_time > run_time:
                packet = ustruct.pack('h', count)
                s.send(packet)
                if debug == True:
                    print ("Sent Packet:", ustruct.unpack('h',packet)[0])
                current_time = time.ticks_ms()
                pycom.rgbled(0x006400)
                time.sleep(0.5)
                pycom.rgbled(000000) # turn off after blinking green
                time.sleep(1) #Wait after sending
    #initialise global variables
    position_last = 0
    cal_distance = adc_position()
    count = 0
    run_time = 30000 # 1 hour is 3.6e+6 in ms
    current_time = 0
    gap_time_start = utime.ticks_ms()
    #if LoRa connection is lost, connect
    connect()
