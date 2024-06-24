from machine import Pin, SoftI2C
import bluetooth
from BLE import BLEUART
from MPU6050 import MPU6050
from time import sleep

uart = None
led = Pin(2, Pin.OUT)
mpu = None


def on_rx():
    global uart

    rx_data = uart.read().decode().strip()
    uart.write("Esp32 says: " + str(rx_data) + "\n")
    print("Esp32 says: " + str(rx_data))

    if rx_data == "!B507":
        led.on()
    elif rx_data == "!B606":
        led.off()


def loop():
    global mpu

    while True:
        gyro = mpu.read_gyro_data()
        accel = mpu.read_accel_data()
        temp = mpu.read_temperature()

        print(gyro, accel, temp)

        sleep(0.1)


def main():
    global uart
    global led
    global mpu

    name = "esp32"
    led.off()

    ble = bluetooth.BLE()
    uart = BLEUART(ble, name)
    uart.irq(handler=on_rx)

    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu = MPU6050(i2c)
    mpu.wake()

    loop()


if __name__ == "__main__":
    main()
