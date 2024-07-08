"""
A lightweight MicroPython implementation for interfacing with an MPU-6050 via I2C. 
Author: Tim Hanewich - https://github.com/TimHanewich
Version: 1.0
Get updates to this code file here: https://github.com/TimHanewich/MicroPython-Collection/blob/master/MPU6050/MPU6050.py

License: MIT License
Copyright 2023 Tim Hanewich
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import machine
from time import sleep

ACCEL_RANGE_2G = 2
ACCEL_RANGE_4G = 4
ACCEL_RANGE_8G = 8
ACCEL_RANGE_16G = 16

GYRO_RANGE_250DPS = 250
GYRO_RANGE_500DPS = 500
GYRO_RANGE_1000DPS = 1000
GYRO_RANGE_2000DPS = 2000

LPF_RANGE_5HZ = 5
LPF_RANGE_10HZ = 10
LPF_RANGE_21HZ = 21
LPF_RANGE_44HZ = 44
LPF_RANGE_94HZ = 94
LPF_RANGE_184HZ = 184
LPF_RANGE_260HZ = 260

ACCEL_RANGES_TO_HEX = {
    2: 0x00,
    4: 0x08,
    8: 0x10,
    16: 0x18
}

GYRO_RANGES_TO_HEX = {
    250: 0x00,
    500: 0x08,
    1000: 0x10,
    2000: 0x18
}

LPF_RANGES_TO_HEX = {
    5: 0x00,
    10: 0x01,
    21: 0x02,
    44: 0x03,
    94: 0x04,
    184: 0x05,
    260: 0x06
}

ACCEL_RANGES_TO_VALUE = {v: k for k, v in ACCEL_RANGES_TO_HEX.items()}
GYRO_RANGES_TO_VALUE = {v: k for k, v in GYRO_RANGES_TO_HEX.items()}
LPF_RANGES_TO_VALUE = {v: k for k, v in LPF_RANGES_TO_HEX.items()}


class MPU6050:
    """Class for reading gyro rates and acceleration data from an MPU-6050 module via I2C."""

    def __init__(self, i2c: machine.I2C, address: int = 0x68):
        """
        Creates a new MPU6050 class for reading gyro rates and acceleration data.
        :param i2c: A setup I2C module of the machine module.
        :param address: The I2C address of the MPU-6050 you are using (0x68 is the default).
        """
        self.address = address
        self.i2c = i2c

        self.accel_offset = (0, 0, 0)
        self.gyro_offset = (0, 0, 0)

    def wake(self) -> None:
        """Wake up the MPU-6050."""
        self.i2c.writeto_mem(self.address, 0x6B, bytes([0x01]))

    def sleep(self) -> None:
        """Places MPU-6050 in sleep mode (low power consumption). Stops the internal reading of new data. Any calls to get gyro or accel data while in sleep mode will remain unchanged - the data is not being updated internally within the MPU-6050!"""
        self.i2c.writeto_mem(self.address, 0x6B, bytes([0x40]))

    def who_am_i(self) -> int:
        """Returns the address of the MPU-6050 (ensure it is working)."""
        return self.i2c.readfrom_mem(self.address, 0x75, 1)[0]

    def read_temperature(self) -> float:
        """Reads the temperature, in celsius, of the onboard temperature sensor of the MPU-6050."""
        data = self.i2c.readfrom_mem(self.address, 0x41, 2)
        raw_temp: float = self._translate_pair(data[0], data[1])
        temp: float = (raw_temp / 340.0) + 36.53
        return temp

    def read_gyro_range(self) -> int:
        """Reads the gyroscope range setting."""
        value = (self.i2c.readfrom_mem(self.address, 0x1B, 1)[0])
        return GYRO_RANGES_TO_VALUE[value]

    def write_gyro_range(self, range: int) -> None:
        """Sets the gyroscope range setting."""
        self.i2c.writeto_mem(self.address, 0x1B, bytes(
            [GYRO_RANGES_TO_HEX[range]]))

    def read_gyro_data(self) -> tuple[float, float, float]:
        """Read the gyroscope data, in a (x, y, z) tuple."""

        # set the modified based on the gyro range (need to divide to calculate)
        gr: int = self.read_gyro_range()
        modifier: float = None

        if gr == 250:
            modifier = 131.0
        elif gr == 500:
            modifier = 65.5
        elif gr == 1000:
            modifier = 32.8
        elif gr == 2000:
            modifier = 16.4

        # read data
        # read 6 bytes (gyro data)
        data = self.i2c.readfrom_mem(self.address, 0x43, 6)
        x: float = (self._translate_pair(data[0], data[1])) / modifier
        y: float = (self._translate_pair(data[2], data[3])) / modifier
        z: float = (self._translate_pair(data[4], data[5])) / modifier

        x -= self.gyro_offset[0]
        y -= self.gyro_offset[1]
        z -= self.gyro_offset[2]

        return (x, y, z)

    def read_accel_range(self) -> int:
        """Reads the accelerometer range setting."""
        value = self.i2c.readfrom_mem(self.address, 0x1C, 1)[0]
        return ACCEL_RANGES_TO_VALUE[value]

    def write_accel_range(self, range: int) -> None:
        """Sets the gyro accelerometer setting."""
        value = ACCEL_RANGES_TO_HEX[range]
        self.i2c.writeto_mem(self.address, 0x1C, bytes([value]))

    def read_accel_data(self) -> tuple[float, float, float]:
        """Read the accelerometer data, in a (x, y, z) tuple."""

        # set the modified based on the gyro range (need to divide to calculate)
        ar: int = self.read_accel_range()
        modifier: float = None

        if ar == 2:
            modifier = 16384.0
        elif ar == 4:
            modifier = 8192.0
        elif ar == 8:
            modifier = 4096.0
        elif ar == 16:
            modifier = 2048.0

        # read data
        # read 6 bytes (accel data)
        data = self.i2c.readfrom_mem(self.address, 0x3B, 6)
        x: float = (self._translate_pair(data[0], data[1])) / modifier
        y: float = (self._translate_pair(data[2], data[3])) / modifier
        z: float = (self._translate_pair(data[4], data[5])) / modifier

        x -= self.accel_offset[0]
        y -= self.accel_offset[1]
        z -= self.accel_offset[2]

        return (x, y, z)

    def read_lpf_range(self) -> int:
        value = self.i2c.readfrom_mem(self.address, 0x1A, 1)[0]
        return LPF_RANGES_TO_VALUE[value]

    def write_lpf_range(self, range: int) -> None:
        """
        Sets low pass filter range.
        """

        value = LPF_RANGES_TO_HEX[range]
        self.i2c.writeto_mem(self.address, 0x1A, bytes([value]))

    def _translate_pair(self, high: int, low: int) -> int:
        """Converts a byte pair to a usable value. Borrowed from https://github.com/m-rtijn/mpu6050/blob/0626053a5e1182f4951b78b8326691a9223a5f7d/mpu6050/mpu6050.py#L76C39-L76C39."""
        value = (high << 8) + low
        if value >= 0x8000:
            value = -((65535 - value) + 1)
        return value

    def print_ranges(self) -> None:
        """Prints the gyroscope and accelerometer ranges."""

        print()
        print("============= MPU6050 =============")
        print("Gyro range : {} degrees/sec".format(self.read_gyro_range()))
        print("Accel range: {} G".format(self.read_accel_range()))
        print("LPF range  : {} Hz".format(self.read_lpf_range()))
        print("Gyro offset: {}".format(self.gyro_offset))
        print("Accel offset: {}".format(self.accel_offset))
        print("===================================")
        print()

    def calibrate(self, total_samples: int = 100, delay_ms: int = 100, az_0: bool = True) -> None:
        """
        Calibrates the gyroscope and accelerometer.

        Args:
            total_samples (int, optional): Number of samples to take. Defaults to 100.
            delay (int, optional): Delay between samples in milliseconds. Defaults to 100.
            az_0 (bool, optional): Whether to set the accelerometer z-axis offset to zero. The default value is True.
        """

        self.gyro_offset = (0, 0, 0)
        self.accel_offset = (0, 0, 0)

        gx, gy, gz = 0, 0, 0
        ax, ay, az = 0, 0, 0

        for _ in range(total_samples):
            gyro = self.read_gyro_data()
            accel = self.read_accel_data()

            gx, gy, gz = gx + gyro[0], gy + gyro[1], gz + gyro[2]
            ax, ay, az = ax + accel[0], ay + accel[1], az + accel[2]

            sleep(delay_ms / 1000)

        self.gyro_offset = (
            gx / total_samples,
            gy / total_samples,
            gz / total_samples,
        )

        az /= total_samples

        if not az_0:
            az -= 1

        self.accel_offset = (
            ax / total_samples,
            ay / total_samples,
            az,
        )
