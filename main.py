import uos
from machine import UART, Pin,ADC
import utime
import time
led = Pin(25,Pin.OUT)
recv_buf="" # receive buffer global variable
sensor_temp = ADC(4) # Connect to the internal temperature sensor
conversion_factor = 3.3 / (65535)
try:
    from secrets import secrets
except ImportError:
    print("All secret keys are kept in secrets.py, please add them there!")
    raise
ssid = secrets["ssid" ]
password_wifi = secrets["password"]
print()
print("Machine: \t" + uos.uname()[4])
print("MicroPython: \t" + uos.uname()[3])
rx_pin = Pin(17)
tx_pin = Pin(16)
temp_in_pin = Pin(0)
temp_out_pin = Pin(1)

#uart = UART(id=0, rx=rx_pin, tx=tx_pin, baudrate=115200)
uart0 = UART(0, rx=rx_pin, tx=tx_pin, baudrate=115200)
#uart0 = UART(0, baudrate=115200)
print(uart0)


def Rx_ESP_Data():
    recv=bytes()
    while uart0.any()>0:
        recv+=uart0.read(1)
    res=recv.decode('utf-8')
    return res

def Connect_WiFi(cmd, uart=uart0, timeout=3000):
    print("CMD: " + cmd)
    uart.write(cmd)
    utime.sleep(7.0)
    Wait_ESP_Rsp(uart, timeout)
    print()

def Send_AT_Cmd(cmd, uart=uart0, timeout=3000):
    print("CMD: " + cmd)
    uart.write(cmd)
    Wait_ESP_Rsp(uart, timeout)
    print()
    
def Wait_ESP_Rsp(uart=uart0, timeout=3000):
    prvMills = utime.ticks_ms()
    resp = b""
    while (utime.ticks_ms()-prvMills)<timeout:
        if uart.any():
            resp = b"".join([resp, uart.read(1)])
    print("resp:")
    try:
        print(resp.decode())
    except UnicodeError:
        print(resp)
    
Send_AT_Cmd('AT\r\n')          #Test AT startup
Send_AT_Cmd('AT+GMR\r\n')      #Check version information
Send_AT_Cmd('AT+CIPSERVER=0\r\n')      #Check version information
Send_AT_Cmd('AT+RST\r\n')      #Check version information
Send_AT_Cmd('AT+RESTORE\r\n')  #Restore Factory Default Settings
Send_AT_Cmd('AT+CWMODE?\r\n')  #Query the WiFi mode
Send_AT_Cmd('AT+CWMODE=1\r\n') #Set the WiFi mode = Station mode
Send_AT_Cmd('AT+CWMODE?\r\n')  #Query the WiFi mode again
#Send_AT_Cmd('AT+CWLAP\r\n', timeout=10000) #List available APs
Connect_WiFi('AT+CWJAP="' + ssid +'","' + password_wifi +'"\r\n', timeout=5000) #Connect to AP
Send_AT_Cmd('AT+CIFSR\r\n')    #Obtain the Local IP Address
time.sleep_ms(10)
Send_AT_Cmd('AT+CIPMUX=1\r\n')    #Obtain the Local IP Address
time.sleep_ms(100)
Send_AT_Cmd('AT+CIPSERVER=1,80\r\n')    #Obtain the Local IP Address
time.sleep_ms(100)
print ('Starting connection to ESP8266...')
while True:
    led.value(1)
    time.sleep_ms(100)
    led.value(0)
    res =""
    res=Rx_ESP_Data()
    if '+IPD' in res: # if the buffer contains IPD(a connection), then respond with HTML handshake
        id_index = res.find('+IPD')
        #reading temperature
        reading = sensor_temp.read_u16() * conversion_factor
        temperature = 27 - (reading - 0.706)/0.001721
        
        print(str(round(temperature, 0)))
        msg = '<center><h2>Temperature: ' + str(round(temperature, 0)) + 'C. </h2></center>'
        print("resp:")
        print(res)
        connection_id =  res[id_index+5]
        print("connectionId:" + connection_id)
        print ('! Incoming connection - sending webpage')
        uart0.write('AT+CIPSEND='+connection_id+',200'+'\r\n')
        #Send a HTTP response then a webpage as bytes the 108 is the amount of bytes you are sending, change this if you change the data sent below
        time.sleep_ms(5)
        uart0.write('HTTP/1.1 200 OK'+'\r\n')
        uart0.write('Content-Type: text/html'+'\r\n')
        uart0.write('Connection: close'+'\r\n')
        uart0.write(''+'\r\n')
        uart0.write('<!DOCTYPE HTML>'+'\r\n')
        uart0.write('<html>'+'\r\n')
        uart0.write('<body><center><h1>Raspberry Pi Pico Web Server</h1></center>'+'\r\n')
        uart0.write(msg +'\r\n')
        uart0.write('</body></html>'+'\r\n')
        utime.sleep_ms(10)
        Send_AT_Cmd('AT+CIPCLOSE='+ connection_id+'\r\n') # once file sent, close connection
        utime.sleep_ms(10)
        recv_buf="" #reset buffer6
        print ('Waiting For connection...')      