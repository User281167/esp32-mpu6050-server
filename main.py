from machine import Pin, SoftI2C
import bluetooth
from BLE import BLEUART
from MPU6050 import *
from time import sleep
import network
import config
import socket
import json
from _thread import start_new_thread

uart = None
led = Pin(2, Pin.OUT)
mpu = None

socket_server = None
clients = []


def on_rx():
    global uart

    rx_data = uart.read().decode().strip()
    uart.write("Esp32 says: " + str(rx_data) + "\n")
    print("Esp32 says: " + str(rx_data))

    # bluefruit connect app
    if rx_data == "!B507":
        led.on()
    elif rx_data == "!B606":
        led.off()


def connect_sta():
    print("\nConnecting to " + config.WIFI_SSID)

    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWD)

    while not sta_if.isconnected():
        print("Waiting for connection...", end="\r")
        sleep(0.25)

    print("Connected!")
    print(sta_if.ifconfig())
    print("======================\n")


def connect_ap():
    print("\nConnecting to " + config.WIFI_SSID_AP)

    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    ap_if.config(essid=config.WIFI_SSID_AP, password=config.WIFI_PASSWD_AP)

    while not ap_if.active():
        print("Waiting for connection...", end="\r")
        sleep(0.25)

    print("Connected!")
    print(ap_if.ifconfig())
    print("======================\n")


def socket_accept():
    global clients
    global socket_server

    while True:
        client = socket_server.accept()
        print("Client connected: {}\n".format(client[1]))

        clients.append(client)


def loop():
    global mpu
    global socket_server

    start_new_thread(socket_accept, ())

    while True:
        gyro = mpu.read_gyro_data()
        accel = mpu.read_accel_data()
        temp = mpu.read_temperature()

        data = {
            "gyro": gyro,
            "accel": accel,
            "temp": temp,
        }

        print(data, end="\r")

        for client in clients:
            try:
                client[0].sendall(json.dumps(data).encode("utf-8"))
            except OSError:
                print("Client disconnected: {}\n".format(client[1]))
                client[0].close()
                clients.remove(client)

        sleep(0.1)


def main():
    global uart
    global led
    global mpu
    global socket_server

    name = "esp32"
    led.off()

    connect_ap()
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_server.bind((config.HOST_IP, config.HOST_PORT))
    socket_server.listen(5)

    ble = bluetooth.BLE()
    uart = BLEUART(ble, name)
    uart.irq(handler=on_rx)

    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu = MPU6050(i2c)
    mpu.wake()

    mpu.write_gyro_range(GYRO_RANGE_250DPS)
    mpu.write_accel_range(ACCEL_RANGE_2G)
    mpu.write_lpf_range(LPF_RANGE_44HZ)

    print("Calibrating...")
    mpu.calibrate(az_0=False)

    mpu.print_ranges()
    sleep(5)

    loop()


if __name__ == "__main__":
    main()
