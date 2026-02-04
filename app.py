from flask import Flask, request, jsonify, render_template_string
from twilio.rest import Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)


# ---------------- CONFIG ----------------
TWILIO_SID = "ACb053c150e0efb5890ad3ff32c4686df8"
TWILIO_AUTH = "18c80cbe5108877d636e1e3d2c8e4b23"
TWILIO_NUMBER = "+18457738393"   # Your Twilio number

EMAIL_ADDRESS = "nexus.srmist@gmail.com"
EMAIL_PASSWORD = "bnon rrkt rndh ahid"

client = Client(TWILIO_SID, TWILIO_AUTH)

live_location = {}

# ---------------- UI ----------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ProtectHer</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link rel="manifest" href="/manifest.json">

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>

<style>
/* ---------------- GLOBAL ---------------- */
*{box-sizing:border-box}
body{
  margin:0;
  font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;
  background:linear-gradient(135deg,#0f172a,#020617);
  color:white;
}

/* ---------------- LAYOUT ---------------- */
.container{
  max-width:420px;
  margin:auto;
  padding:18px;
}

.title{
  text-align:center;
  font-weight:800;
  font-size:26px;
  margin:12px 0 18px;
  letter-spacing:.5px;
}

/* ---------------- CARDS ---------------- */
.card{
  background:rgba(30,41,59,.7);
  backdrop-filter:blur(14px);
  border-radius:20px;
  padding:18px;
  margin-bottom:18px;
  box-shadow:0 10px 30px rgba(0,0,0,.4);
  transition:.25s;
}

.card:hover{
  transform:translateY(-2px);
}

/* ---------------- INPUTS ---------------- */
input{
  width:100%;
  padding:12px 14px;
  margin:8px 0;
  border-radius:12px;
  border:none;
  background:#0b1220;
  color:white;
  font-size:14px;
}

/* ---------------- BUTTONS ---------------- */
button{
  width:100%;
  padding:13px;
  border-radius:14px;
  border:none;
  font-weight:700;
  font-size:16px;
  cursor:pointer;
}

/* Save */
.btn-save{
  background:#1e293b;
  color:white;
}

/* SOS */
.btn-sos{
  background:linear-gradient(135deg,#ef4444,#f97316);
  font-size:22px;
  padding:20px;
  animation:pulse 1.6s infinite;
}

/* Pulse animation for panic effect */
@keyframes pulse{
  0%{box-shadow:0 0 0 0 rgba(239,68,68,.6)}
  70%{box-shadow:0 0 0 20px rgba(239,68,68,0)}
  100%{box-shadow:0 0 0 0 rgba(239,68,68,0)}
}

/* ---------------- MAP ---------------- */
#map{
  height:260px;
  border-radius:14px;
  overflow:hidden;
}

/* ---------------- TOAST ---------------- */
.toast{
  position:fixed;
  bottom:20px;
  left:50%;
  transform:translateX(-50%);
  background:#111827;
  padding:10px 18px;
  border-radius:10px;
  display:none;
  font-size:14px;
}

/* small text */
.small{
  font-size:12px;
  opacity:.6;
  margin-top:6px;
  text-align:center;
}
</style>
<script>
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/static/sw.js");
}
</script>

</head>

<body>

<div class="container">

  <div class="title">ProtectHer</div>

  <!-- USER CARD -->
  <div class="card">
    <h3>Welcome <span id="username">User</span></h3>

    <input id="name" placeholder="Your Name">
    <input id="phone" placeholder="Parent Phone (+91...)">
    <input id="email" placeholder="Parent Email">

    <button class="btn-save" onclick="save()">Save Details</button>
  </div>

  <!-- SOS CARD -->
  <div class="card">
    <button class="btn-sos" onclick="sendSOS()">🚨 SEND SOS</button>
    <div class="small">Instant SMS + Email with live location</div>
  </div>

  <!-- MAP CARD -->
  <div class="card">
    <h3>Live Location</h3>
    <div id="map"></div>
  </div>

</div>

<div id="toast" class="toast"></div>

<script>
/* ---------------- MAP ---------------- */
let map = L.map('map').setView([20.5937,78.9629], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
let marker = L.marker([0,0]).addTo(map);

/* ---------------- TOAST ---------------- */
function toast(msg){
  const t=document.getElementById("toast");
  t.innerText=msg;
  t.style.display="block";
  setTimeout(()=>t.style.display="none",2500);
}

/* ---------------- SAVE ---------------- */
function save(){
  document.cookie="username="+document.getElementById("name").value+"; path=/";
  document.getElementById("username").innerText=getCookie("username");
  toast("Saved ✓");
}

function getCookie(name){
 let v=document.cookie.match('(^|;) ?'+name+'=([^;]*)(;|$)');
 return v ? v[2] : null;
}

document.getElementById("username").innerText=getCookie("username")||"User";


/* ---------------- LOCATION ---------------- */
navigator.geolocation.watchPosition(pos=>{
 fetch('/update_location',{
  method:"POST",
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({
   lat:pos.coords.latitude,
   lng:pos.coords.longitude
  })
 });

 marker.setLatLng([pos.coords.latitude,pos.coords.longitude]);
 map.setView([pos.coords.latitude,pos.coords.longitude],15);

},()=>toast("Enable GPS for tracking"),{enableHighAccuracy:true});


/* ---------------- SOS ---------------- */
function sendSOS(){
 fetch('/sos',{
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({
   name:document.getElementById("name").value,
   phone:document.getElementById("phone").value,
   email:document.getElementById("email").value
  })
 }).then(r=>r.json()).then(d=>toast(d.status));
}


/* 🎤 VOICE + AUTO CALL + AUTO SOS (NEW FEATURE) */

const keywords = ["help","save me","stop","danger"];

function autoCall(){
  const phone = document.getElementById("phone").value;
  if(phone){
    window.location.href = "tel:"+phone;   // opens dialer
  }
}

function triggerAutoSOS(){
  toast("🚨 Voice detected! Sending SOS...");
  sendSOS();
  autoCall();
}

/* Speech Recognition */
function startVoiceMonitoring(){

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if(!SpeechRecognition){
    toast("Voice detection not supported in this browser");
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.lang = "en-US";
  recognition.interimResults = false;

  recognition.onresult = function(event){
    let text = event.results[event.results.length-1][0].transcript.toLowerCase();
    console.log("Heard:", text);

    for(let k of keywords){
      if(text.includes(k)){
        triggerAutoSOS();
        break;
      }
    }
  };

  recognition.onerror = ()=>{};
  recognition.onend = ()=> recognition.start();

  recognition.start();
  toast("Voice monitoring ON");
}


/* Start automatically after page loads */
setTimeout(startVoiceMonitoring, 2000);

</script>

</body>
</html>
"""


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.json
    live_location["lat"] = data["lat"]
    live_location["lng"] = data["lng"]
    return jsonify({"status":"updated"})

@app.route("/sos", methods=["POST"])
def sos():
    try:
        data = request.json

        lat = live_location.get("lat")
        lng = live_location.get("lng")

        if not lat or not lng:
            return jsonify({"status": "Location not available yet. Please allow GPS."})

        map_url = f"https://www.google.com/maps?q={lat},{lng}"
        msg = f"🚨 SOS ALERT!\nUser: {data['name']}\nLive Location: {map_url}"

        # --- SMS ---
        sms = client.messages.create(
            body=msg,
            from_=TWILIO_NUMBER,
            to=data["phone"]
        )

        # --- Email ---
        email = MIMEMultipart()
        email['From'] = EMAIL_ADDRESS
        email['To'] = data["email"]
        email['Subject'] = "🚨 SOS Alert - Live Location"
        email.attach(MIMEText(msg, 'plain'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(email)
        server.quit()

        return jsonify({"status": "✅ SOS sent successfully!"})

    except Exception as e:
        return jsonify({"status": f"❌ ERROR: {str(e)}"})


@app.route("/manifest.json")
def manifest():
    return jsonify({
        "name":"SafeGuard AI",
        "short_name":"SafeGuard",
        "start_url":"/",
        "display":"standalone",
        "background_color":"#0f172a",
        "theme_color":"#dc2626",

        "icons": [
  {
    "src": "/icon-192.png",
    "sizes": "192x192",
    "type": "image/png"
  },
  {
    "src": "/icon-512.png",
    "sizes": "512x512",
    "type": "image/png"
  }
]

    })

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(debug=True)