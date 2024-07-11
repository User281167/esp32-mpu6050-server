import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import socket
import json

socket_client = socket.socket(family=socket.AF_INET)
socket_client.connect(("192.168.4.1", 80))
socket_client.sendall("GET /stream HTTPS".encode())

plt.style.use('fast')

index = 0
x = [0] * 100
gyro_x = [0] * 100
gyro_y = [0] * 100
gyro_z = [0] * 100

accel_x = [0] * 100
accel_y = [0] * 100
accel_z = [0] * 100

temp = [0] * 100

# fig, ax = plt.subplots(3, 3)
fig, ax = plt.subplot_mosaic("ABC;DEF;GGG")

gx = ax['A'].plot(x, gyro_x)[0]
gy = ax['B'].plot(x, gyro_y)[0]
gz = ax['C'].plot(x, gyro_z)[0]
ax["A"].set_title("Gyro X")
ax["B"].set_title("Gyro Y")
ax["C"].set_title("Gyro Z")

acx = ax["D"].plot(x, accel_x)[0]
acy = ax["E"].plot(x, accel_y)[0]
acz = ax["F"].plot(x, accel_z)[0]
ax["D"].set_title("Accel X")
ax["E"].set_title("Accel Y")
ax["F"].set_title("Accel Z")

ax["G"].set_title("Temp")
t_plot = ax["G"].plot(x, temp)[0]

for i in ["A", "B", "C", "D", "E", "F", "G"]:
    ax[i].grid()


def animate(i):
    global index

    try:
        data = socket_client.recv(1024)
        data = json.loads(data)
        print(data, end="\r")

        x[index] = index
        gyro_x[index] = data["gyro"][0]
        gyro_y[index] = data["gyro"][1]
        gyro_z[index] = data["gyro"][2]

        accel_x[index] = data["accel"][0]
        accel_y[index] = data["accel"][1]
        accel_z[index] = data["accel"][2]

        temp[index] = data["temp"]

        index = (index + 1) % 100
    except:
        pass
    finally:
        gx.set_xdata(x)
        gx.set_ydata(gyro_x)
        ax["A"].set(ylim=[np.min(gyro_x), np.max(gyro_x)], xlim=[0, 100])

        gy.set_xdata(x)
        gy.set_ydata(gyro_y)
        ax["B"].set(ylim=[np.min(gyro_y), np.max(gyro_y)], xlim=[0, 100])

        gz.set_xdata(x)
        gz.set_ydata(gyro_z)
        ax["C"].set(ylim=[np.min(gyro_z), np.max(gyro_z)], xlim=[0, 100])

        acx.set_xdata(x)
        acx.set_ydata(accel_x)
        ax["D"].set(ylim=[np.min(accel_x), np.max(accel_x)], xlim=[0, 100])

        acy.set_xdata(x)
        acy.set_ydata(accel_y)
        ax["E"].set(ylim=[np.min(accel_y), np.max(accel_y)], xlim=[0, 100])

        acz.set_xdata(x)
        acz.set_ydata(accel_z)
        ax["F"].set(ylim=[np.min(accel_z), np.max(accel_z)], xlim=[0, 100])

        t_plot.set_xdata(x)
        t_plot.set_ydata(temp)
        ax["G"].set(ylim=[np.min(temp), np.max(temp)], xlim=[0, 100])


ani = FuncAnimation(fig=fig, func=animate, interval=1)
plt.tight_layout()
plt.show()
