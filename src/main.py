from machine import Pin, SoftI2C
from time import sleep
from MPU6050 import *


uart = None
led = Pin(2, Pin.OUT)
mpu = None


def on_rx():
    rx_data = uart.read().decode().strip()
    uart.write("Esp32 says: " + str(rx_data) + "\n")
    print("Esp32 says: " + str(rx_data))

    # bluefruit connect app
    if rx_data == "!B507":
        led.on()
    elif rx_data == "!B606":
        led.off()


def loop():
    from server import send_stream

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
        send_stream(data)

        sleep(0.1)


def main():
    from _thread import start_new_thread
    import bluetooth
    from BLE import BLEUART
    from server import create_server, socket_accept

    global uart
    global mpu

    name = "esp32"
    led.off()

    create_server(ap_if=True)

    ble = bluetooth.BLE()
    uart = BLEUART(ble, name)
    uart.irq(handler=on_rx)

    i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
    mpu = MPU6050(i2c)
    mpu.wake()

    mpu.write_gyro_range(GYRO_RANGE_250DPS)
    mpu.write_accel_range(ACCEL_RANGE_2G)
    mpu.write_lpf_range(LPF_RANGE_44HZ)

    # print("Calibrating...")
    # mpu.calibrate(az_0=False)

    # mpu.print_ranges()

    # start_new_thread(socket_accept, ([mpu]))
    # loop()
    socket_accept(mpu=mpu)


if __name__ == "__main__":
    main()
