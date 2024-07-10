import network
import config
import json
import socket
from time import sleep
from _thread import start_new_thread

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
    ap_if.config(essid=config.WIFI_SSID_AP,
                 authmode=network.AUTH_WPA2_PSK, password=config.WIFI_PASSWD_AP)

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


def get_html(client, html_file) -> str:
    res = ""

    with open(html_file, "r") as page:
        html = page.read()
        res = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n{html}"

    return res


def http_server(client, mpu):
    request = client[0].recv(1024).decode("utf-8")
    request_lines = request.split('\r\n')
    method, path, protocol = request_lines[0].split(' ')

    print(f"method = {method} path = {path} protocol = {protocol}")

    file_path = "/pages" + path
    file_type = path.split('.')[-1]
    print(file_path)

    if method == "GET":
        if path == "/":
            res = get_html(client[0], "pages/index.html")
        elif path == "/aviator":
            res = get_html(client[0], "pages/aviator.html")
        elif file_type == "css":
            with open(file_path, "r") as file:
                css = file.read()
                res = f"HTTP/1.1 200 OK\r\nContent-Type: text/css\r\n{css}"
        elif file_type == "js":
            with open(file_path, "r") as file:
                js = file.read()
                res = f"HTTP/1.1 200 OK\r\nContent-Type: text/javascript\r\n{js}"
        elif path == "/stream":
            # send continuous stream of data
            if not client in clients:
                clients.append(client)
        elif path == "/gyro":
            res = json.dumps(mpu.read_gyro_data())
        elif path == "/accel":
            res = json.dumps(mpu.read_accel_data())
        elif path == "/temp":
            res = json.dumps(mpu.read_temperature())
        else:
            res = "HTTP/1.1 404 NOT FOUND"

        client[0].sendall(res.encode("utf-8"))

        if path != "/stream":
            client[0].close()

        print("END HTTP")


def socket_accept(mpu):
    while True:
        client = socket_server.accept()
        print("Client connected: {}\n".format(client[1]))

        try:
            http_server(client, mpu)
        except OSError as e:
            print("Error with request")
            print(e)


def send_stream(data):
    for client in clients:
        try:
            client[0].send(json.dumps(data).encode("utf-8"))
        except OSError:
            print("Client disconnected: {}\n".format(client[1]))
            client[0].close()
            clients.remove(client)
