import network
import config
import json
import socket
from time import sleep

socket_server = None
clients = []


def connect_sta():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)

    print("WIFI scan results:")

    authmodes = ['Open', 'WEP', 'WPA-PSK' 'WPA2-PSK4', 'WPA/WPA2-PSK']

    for (ssid, bssid, channel, RSSI, authmode, hidden) in sta_if.scan():
        try:
            print("* {:s}".format(ssid))
            print(
                "   - Auth: {} {}".format(authmodes[authmode], '(hidden)' if hidden else ''))
            print("   - Channel: {}".format(channel))
            print("   - RSSI: {}".format(RSSI))
            print(
                "   - BSSID: {:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}".format(*bssid))
            print()
        except:
            pass

    print("Connecting to " + config.WIFI_SSID)
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


def create_server(ap_if=True):
    """Initializes esp32 server.

    Args:
        ap_if (bool, optional): Whether to connect to access point (True) or station (False). Defaults to True.
    """

    global socket_server

    if ap_if:
        connect_ap()
    else:
        connect_sta()

    socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_server.bind((config.HOST_IP, config.HOST_PORT))
    socket_server.listen(5)


def http_server(client, mpu):
    request = client[0].recv(1024).decode("utf-8")
    request_lines = request.split('\r\n')
    method, path, protocol = request_lines[0].split(' ')

    print(f"method = {method} path = {path} protocol = {protocol}")

    if method == "GET":
        if path == "/":
            page = open("/pages/index.html", "r")
            html = page.read()
            # client[0].sendall(f"HTTP/1.1 200 OK {html}".encode("utf-8"))
            # client[0].sendall(f"HTTP/1.1 200 OK {open("/pages/style.css").read()}".encode("utf-8"))
            # page.close()
            # client[0].close()
            # page.close()
            # client[0].send(b"HTTP/1.1 200 OK")
            # client[0].send(b"Content-Type: text/html")
            # client[0].send(open("/pages/index.html").read().encode("utf-8"))

            client[0].sendall(
                f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n{html}".encode("utf-8"))

            # client[0].send(b"Content-Type: text/css")
            # client[0].send(open("/pages/style.css").read().encode("utf-8"))
            client[0].close()
            page.close()
        elif path == "/stream":
            if not client in clients:
                clients.append(client)
        if path == "/gyro":
            client[0].sendall(json.dumps(mpu.read_gyro_data()).encode("utf-8"))
            client[0].close()
        elif path == "/accel":
            client[0].sendall(json.dumps(
                mpu.read_accel_data()).encode("utf-8"))
            client[0].close()
        elif path == "/temp":
            client[0].sendall(json.dumps(
                mpu.read_temperature()).encode("utf-8"))
            client[0].close()
        else:
            client[0].sendall(b"HTTP/1.1 404 NOT FOUND")
            client[0].close()


def socket_accept(mpu):
    while True:
        client = socket_server.accept()
        print("Client connected: {}\n".format(client[1]))

        try:
            http_server(client, mpu)
        except OSError:
            print("Error with request")


def send_stream(data):
    for client in clients:
        try:
            client[0].sendall(json.dumps(data).encode("utf-8"))
        except OSError:
            print("Client disconnected: {}\n".format(client[1]))
            client[0].close()
            clients.remove(client)
