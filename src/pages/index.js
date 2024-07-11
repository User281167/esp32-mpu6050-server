const ax = document.getElementById("ax");
const ay = document.getElementById("ay");
const az = document.getElementById("az");

const gx = document.getElementById("gx");
const gy = document.getElementById("gy");
const gz = document.getElementById("gz");

const temp = document.getElementById("temp");

const mpuSettingsDialog = document.getElementById("mpu-settings-dialog");
const cancelBtn = document.getElementById("cancel-btn");
const confirmBtn = document.getElementById("confirm-btn");
const settingsBtn = document.getElementById("settings-btn");

// const gateway = `${window.location.host}/stream`;
const gateway = `ws://${window.location.host}:80/stream`;
let webSocket;

function initWebSocket() {
  webSocket = new WebSocket(gateway);
  webSocket.onopen = onOpen;
  webSocket.onclose = onClose;
  webSocket.onmessage = onMessage;

  alert(window.location.host);
}

function onOpen() {
  console.log("Connection open");
  webSocket.send("GET /stream HTTP/1.1");
}

function onClose() {
  console.log("Connection closed");
}

function onMessage(event) {
  const data = JSON.parse(event.data);

  // for (const [key, value] of Object.entries(data)) {
  //   mpuData[key].textContent = parseFloat(value).toFixed(2);
  // }

  mpuData = data;

  ax.textContent = parseFloat(data.acceleration.x).toFixed(2);
  ay.textContent = parseFloat(data.acceleration.y).toFixed(2);
  az.textContent = parseFloat(data.acceleration.z).toFixed(2);

  gx.textContent = parseFloat(data.gyro.x).toFixed(2);
  gy.textContent = parseFloat(data.gyro.y).toFixed(2);
  gz.textContent = parseFloat(data.gyro.z).toFixed(2);

  temp.textContent = parseFloat(data.temperature).toFixed(2);
}

settingsBtn.addEventListener("click", () => {
  mpuSettingsDialog.showModal();
});

cancelBtn.addEventListener("click", () => {
  mpuSettingsDialog.close();
});

confirmBtn.addEventListener("click", () => {
  const accelerometerRange = document.getElementById(
    "accelerometer-range"
  ).value;

  const gyroscopeRange = document.getElementById("gyroscope-range").value;
  const filterBand = document.getElementById("filter-band").value;
  const delay = document.getElementById("delay").value;

  if (webSocket.readyState === WebSocket.OPEN) {
    webSocket.send(
      JSON.stringify({
        accelerometerRange: accelerometerRange,
        gyroRange: gyroscopeRange,
        filterBand: filterBand,
        delay: delay,
      })
    );
  }

  mpuSettingsDialog.close();
});

window.addEventListener("load", initWebSocket);
