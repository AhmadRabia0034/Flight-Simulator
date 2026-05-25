import math
import random
import socket
import struct
import threading
import time
from typing import Dict

from flask import Flask, render_template
from flask_socketio import SocketIO

from dis_pdu import EntityStatePDU, EntityID, Vec3f, Vec3d, Orientation

app = Flask(__name__)
app.config["SECRET_KEY"] = "dis-sa"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

HOST_IP = "127.0.0.1"
HOST_PORT = 50000

MAGIC = b"DIST"
HDR_FMT = ">4sB3xIQQB"
HDR_SIZE = struct.calcsize(HDR_FMT)

MSG_DIS = 1
MSG_PTP_SYNC = 2

MARKA_LAT = 31.9727
MARKA_LON = 35.9916

NODES = {
    "jor_flight": {"cluster": "jordan", "port": 51001, "virtual": True,  "lat": MARKA_LAT, "lon": MARKA_LON},
       "jor_amman_1": {"cluster": "jordan", "port": 51002, "virtual": False, "lat": 31.70, "lon": 35.80},
    "jor_amman_2": {"cluster": "jordan", "port": 51003, "virtual": False, "lat": 32.10, "lon": 36.10},
    "jor_aqaba":   {"cluster": "jordan", "port": 51004, "virtual": False, "lat": 29.53, "lon": 35.00},
    "jor_irbid":   {"cluster": "jordan", "port": 51005, "virtual": False, "lat": 32.55, "lon": 35.85},
    "jor_mafraq":  {"cluster": "jordan", "port": 51006, "virtual": False, "lat": 32.33, "lon": 36.20},
    "jor_zarqa":   {"cluster": "jordan", "port": 51007, "virtual": False, "lat": 32.08, "lon": 36.08},

    "ksa_riyadh1": {"cluster": "ksa", "port": 51301, "virtual": False, "lat": 24.95, "lon": 46.70},
    "ksa_riyadh2": {"cluster": "ksa", "port": 51302, "virtual": False, "lat": 24.50, "lon": 46.50},
    "ksa_jeddah":  {"cluster": "ksa", "port": 51303, "virtual": False, "lat": 21.65, "lon": 39.15},
    "ksa_dammam":  {"cluster": "ksa", "port": 51304, "virtual": False, "lat": 26.47, "lon": 49.79},
    "ksa_tabuk":   {"cluster": "ksa", "port": 51305, "virtual": False, "lat": 28.36, "lon": 36.60},
    "ksa_neom":    {"cluster": "ksa", "port": 51306, "virtual": False, "lat": 28.08, "lon": 34.71},

    "egy_cairo1":  {"cluster": "egypt", "port": 51201, "virtual": False, "lat": 30.12, "lon": 31.40},
    "egy_cairo2":  {"cluster": "egypt", "port": 51202, "virtual": False, "lat": 29.90, "lon": 31.20},
    "egy_alex":    {"cluster": "egypt", "port": 51203, "virtual": False, "lat": 30.93, "lon": 29.54},
    "egy_sharm":   {"cluster": "egypt", "port": 51204, "virtual": False, "lat": 27.97, "lon": 34.39},
    "egy_luxor":   {"cluster": "egypt", "port": 51205, "virtual": False, "lat": 25.67, "lon": 32.70},

    "irq_bgd1":    {"cluster": "iraq", "port": 51101, "virtual": False, "lat": 33.26, "lon": 44.23},
    "irq_bgd2":    {"cluster": "iraq", "port": 51102, "virtual": False, "lat": 33.50, "lon": 44.50},
    "irq_erbil":   {"cluster": "iraq", "port": 51103, "virtual": False, "lat": 36.23, "lon": 43.96},
    "irq_basra":   {"cluster": "iraq", "port": 51104, "virtual": False, "lat": 30.55, "lon": 47.76},

    "uae_dxb1":    {"cluster": "uae", "port": 51401, "virtual": False, "lat": 25.25, "lon": 55.36},
    "uae_dxb2":    {"cluster": "uae", "port": 51402, "virtual": False, "lat": 25.00, "lon": 55.00},
    "uae_auh":     {"cluster": "uae", "port": 51403, "virtual": False, "lat": 24.43, "lon": 54.65},
    "uae_sharjah": {"cluster": "uae", "port": 51404, "virtual": False, "lat": 25.32, "lon": 55.51},

    "tur_ist1":    {"cluster": "turkey", "port": 51501, "virtual": False, "lat": 41.27, "lon": 28.72},
    "tur_ist2":    {"cluster": "turkey", "port": 51502, "virtual": False, "lat": 40.90, "lon": 29.31},
    "tur_ankara":  {"cluster": "turkey", "port": 51503, "virtual": False, "lat": 40.12, "lon": 32.99},
    "tur_antalya": {"cluster": "turkey", "port": 51504, "virtual": False, "lat": 36.90, "lon": 30.79},

    "de_frankfurt":{"cluster": "germany", "port": 51601, "virtual": False, "lat": 50.03, "lon": 8.57},
    "de_munich":   {"cluster": "germany", "port": 51602, "virtual": False, "lat": 48.35, "lon": 11.78},
    "de_berlin":   {"cluster": "germany", "port": 51603, "virtual": False, "lat": 52.36, "lon": 13.50},
    "uk_lhr1":     {"cluster": "uk", "port": 51701, "virtual": False, "lat": 51.47, "lon": -0.45},
    "uk_lhr2":     {"cluster": "uk", "port": 51702, "virtual": False, "lat": 51.50, "lon": -0.10},
    "uk_man":      {"cluster": "uk", "port": 51703, "virtual": False, "lat": 53.35, "lon": -2.27},

    "us_jfk1":     {"cluster": "usa", "port": 51801, "virtual": False, "lat": 40.64, "lon": -73.77},
    "us_jfk2":     {"cluster": "usa", "port": 51802, "virtual": False, "lat": 40.80, "lon": -74.00},
    "us_lax1":     {"cluster": "usa", "port": 51803, "virtual": False, "lat": 33.94, "lon": -118.40},
    "us_lax2":     {"cluster": "usa", "port": 51804, "virtual": False, "lat": 34.10, "lon": -118.20},
    "us_ord":      {"cluster": "usa", "port": 51805, "virtual": False, "lat": 41.97, "lon": -87.90},
    "us_mia":      {"cluster": "usa", "port": 51806, "virtual": False, "lat": 25.79, "lon": -80.28},
    "us_dfw":      {"cluster": "usa", "port": 51807, "virtual": False, "lat": 32.89, "lon": -97.04},

    "ind_delhi1":  {"cluster": "india", "port": 51901, "virtual": False, "lat": 28.55, "lon": 77.10},
    "ind_delhi2":  {"cluster": "india", "port": 51902, "virtual": False, "lat": 28.70, "lon": 77.30},
    "ind_mumbai":  {"cluster": "india", "port": 51903, "virtual": False, "lat": 19.09, "lon": 72.86},
    "jpn_tokyo1":  {"cluster": "japan", "port": 52001, "virtual": False, "lat": 35.54, "lon": 139.77},
    "jpn_tokyo2":  {"cluster": "japan", "port": 52002, "virtual": False, "lat": 35.76, "lon": 140.39},
    "jpn_osaka":   {"cluster": "japan", "port": 52003, "virtual": False, "lat": 34.43, "lon": 135.24},

    "aus_syd":     {"cluster": "australia", "port": 52101, "virtual": False, "lat": -33.94, "lon": 151.17},
    "aus_mel":     {"cluster": "australia", "port": 52102, "virtual": False, "lat": -37.66, "lon": 144.84},
    "bra_gru":     {"cluster": "brazil", "port": 52201, "virtual": False, "lat": -23.43, "lon": -46.47},
    "bra_gig":     {"cluster": "brazil", "port": 52202, "virtual": False, "lat": -22.81, "lon": -43.24},
}

REGION_PATHS = {
    "jordan": {"wan_ms": 15,  "wan_jitter_ms": 5,  "drop": 0.01},
    "iraq":   {"wan_ms": 25,  "wan_jitter_ms": 8,  "drop": 0.02},
    "egypt":  {"wan_ms": 35,  "wan_jitter_ms": 10, "drop": 0.02},
    "ksa":    {"wan_ms": 10,  "wan_jitter_ms": 4,  "drop": 0.01},
    "uae":    {"wan_ms": 20,  "wan_jitter_ms": 6,  "drop": 0.01},
    "turkey": {"wan_ms": 40,  "wan_jitter_ms": 12, "drop": 0.02},
    "germany":{"wan_ms": 60,  "wan_jitter_ms": 15, "drop": 0.03},
    "uk":     {"wan_ms": 70,  "wan_jitter_ms": 18, "drop": 0.03},
    "usa":    {"wan_ms": 120, "wan_jitter_ms": 25, "drop": 0.04},
    "india":  {"wan_ms": 80,  "wan_jitter_ms": 20, "drop": 0.03},
    "japan":  {"wan_ms": 130, "wan_jitter_ms": 30, "drop": 0.04},
    "australia": {"wan_ms": 170, "wan_jitter_ms": 35, "drop": 0.05},
    "brazil": {"wan_ms": 190, "wan_jitter_ms": 40, "drop": 0.05},
}

entities: Dict[str, dict] = {}
node_last_seen: Dict[str, float] = {}
node_status: Dict[str, str] = {name: "disconnected" for name in NODES}

ptp_state: Dict[str, dict] = {}
for name in NODES:
    ptp_state[name] = {
        "clock_offset_ms": 0.0,
        "ptp_sync_error_ms": 0.0,
        "last_sync_time": None,
        "one_way_latency_ms": 0.0,
    }

state_lock = threading.Lock()

A = 6378137.0
E2 = 6.69437999014e-3

def llh_to_ecef(lat_deg: float, lon_deg: float, alt_m: float):
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)
    N = A / math.sqrt(1 - E2 * sin_lat * sin_lat)
    x = (N + alt_m) * cos_lat * cos_lon
    y = (N + alt_m) * cos_lat * sin_lon
    z = (N * (1 - E2) + alt_m) * sin_lat
    return x, y, z

def ecef_to_llh(x: float, y: float, z: float):
    lon = math.atan2(y, x)
    p = math.sqrt(x * x + y * y)
    lat = math.atan2(z, p * (1 - E2))
    for _ in range(5):
        sin_lat = math.sin(lat)
        N = A / math.sqrt(1 - E2 * sin_lat * sin_lat)
        lat = math.atan2(z + E2 * N * sin_lat, p)
    sin_lat = math.sin(lat)
    N = A / math.sqrt(1 - E2 * sin_lat * sin_lat)
    alt = p / math.cos(lat) - N
    return math.degrees(lat), math.degrees(lon), alt

def pack_message(msg_type: int, seq: int, tx_ns: int, playout_ns: int, src: str, payload: bytes) -> bytes:
    src_b = src.encode("utf-8")
    return (
        struct.pack(HDR_FMT, MAGIC, msg_type, seq, tx_ns, playout_ns, len(src_b))
        + src_b
        + struct.pack(">I", len(payload))
        + payload
    )

def unpack_message(data: bytes):
    magic, msg_type, seq, tx_ns, playout_ns, src_len = struct.unpack(HDR_FMT, data[:HDR_SIZE])
    if magic != MAGIC:
        raise ValueError("Bad magic")
    offset = HDR_SIZE
    src = data[offset:offset + src_len].decode("utf-8")
    offset += src_len
    (payload_len,) = struct.unpack(">I", data[offset:offset + 4])
    offset += 4
    payload = data[offset:offset + payload_len]
    return msg_type, seq, tx_ns, playout_ns, src, payload

class SimClock:
    def __init__(self, offset_ms=0.0, drift_ppm=0.0):
        self.base_offset_ns = int(offset_ms * 1e6)
        self.drift = drift_ppm / 1_000_000.0
        self.start_real_ns = time.time_ns()
        self.correction_ns = 0
        self.last_error_ns = 0

    def now_ns(self):
        real_elapsed = time.time_ns() - self.start_real_ns
        drifted = int(real_elapsed * (1.0 + self.drift))
        return self.start_real_ns + drifted + self.base_offset_ns + self.correction_ns

    def apply_ptp_sample(self, master_time_ns: int):
        local_before = self.now_ns()
        error_ns = master_time_ns - local_before
        self.last_error_ns = error_ns
        self.correction_ns += int(error_ns * 0.5)
        local_after = self.now_ns()
        residual_ns = master_time_ns - local_after
        return error_ns, residual_ns

def process_and_emit(src, cluster, tx_ns, pdu):
    try:
        lat, lon, alt = ecef_to_llh(pdu.location.x, pdu.location.y, pdu.location.z)
        latency_ms = (time.time_ns() - tx_ns) / 1e6
        marking_str = pdu.marking.strip("\x00")

        with state_lock:
            ptp_state[src]["one_way_latency_ms"] = latency_ms

            entity = {
                "name": src,
                "cluster": cluster,
                "lat": lat,
                "lon": lon,
                "alt": alt,
                "latency_ms": latency_ms,
                "roll": pdu.orientation.phi,
                "pitch": pdu.orientation.theta,
                "yaw": pdu.orientation.psi,
                "virtual": NODES[src]["virtual"],
                "timestamp": time.time(),
                "clock_offset_ms": ptp_state[src]["clock_offset_ms"],
                "ptp_sync_error_ms": ptp_state[src]["ptp_sync_error_ms"],
                "marking": marking_str
            }

            entities[src] = entity
            node_last_seen[src] = time.time()
            node_status[src] = "connected"

        socketio.emit("entity_update", entity)
        socketio.emit("node_status", {"name": src, "status": "connected"})
        socketio.emit("packet_event", {"src": src, "status": "ok"})
        socketio.emit("ptp_update", {
            "node": src,
            "clock_offset_ms": ptp_state[src]["clock_offset_ms"],
            "ptp_sync_error_ms": ptp_state[src]["ptp_sync_error_ms"],
            "one_way_latency_ms": ptp_state[src]["one_way_latency_ms"],
        })
    except Exception as e:
        print(f"[PROCESS ERROR] {e}")

def host_receiver_loop():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST_IP, HOST_PORT))
    print(f"[HOST] Running on {HOST_IP}:{HOST_PORT} with {len(NODES)} ACTIVE NODES!")

    while True:
        data, _addr = sock.recvfrom(4096)
        try:
            msg_type, seq, tx_ns, playout_ns, src, payload = unpack_message(data)
        except Exception:
            continue

        if src not in NODES:
            continue

        cluster = NODES[src]["cluster"]
        path = REGION_PATHS[cluster]

        if random.random() < path["drop"]:
            socketio.emit("packet_event", {"src": src, "status": "drop"})
            continue

        if msg_type == MSG_DIS:
            try:
                pdu = EntityStatePDU.unpack(payload)
            except Exception:
                continue

            if src == "jor_flight":
                process_and_emit(src, cluster, tx_ns, pdu)
            else:
                extra_delay_ms = path["wan_ms"] + random.uniform(0, path["wan_jitter_ms"])
                threading.Timer(extra_delay_ms / 1000.0, process_and_emit, args=(src, cluster, tx_ns, pdu)).start()

def connection_monitor_loop():
    timeout_sec = 5.0
    while True:
        now = time.time()
        changed = []

        with state_lock:
            for name in NODES:
                last = node_last_seen.get(name)
                current = node_status.get(name, "disconnected")

                if last is None or (now - last) > timeout_sec:
                    if current != "disconnected":
                        node_status[name] = "disconnected"
                        changed.append((name, "disconnected"))
                else:
                    if current != "connected":
                        node_status[name] = "connected"
                        changed.append((name, "connected"))

        for name, status in changed:
            socketio.emit("node_status", {"name": name, "status": status})

        time.sleep(1.0)

def host_ptp_broadcast_loop():
    while True:
        master_time_ns = time.time_ns()
        with state_lock:
            names = list(NODES.keys())
        for name in names:
            socketio.emit("ptp_sync", {
                "node": name,
                "master_time_ns": master_time_ns
            })
        time.sleep(1.0)

def node_publisher_loop(name: str):
    cfg = NODES[name]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clock = SimClock(offset_ms=random.uniform(-8, 8), drift_ppm=random.uniform(-15, 15))
    seq = 1
    t0 = time.time()
    last_ptp_sync = time.time()

    fg_sock = None
    lat = cfg["lat"]
    lon = cfg["lon"]
    alt = 0.0
    roll = 0.0
    pitch = 0.0
    yaw = 0.0
    marking = name[:11].upper()

    if name == "jor_flight":
        fg_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        fg_sock.bind(("127.0.0.1", 49000))
        fg_sock.settimeout(0.05) 
        print("[FG_NODE] Listening to FlightGear on port 49000...")

    while True:
        if time.time() - last_ptp_sync >= 1.0:
            master_time_ns = time.time_ns()
            error_ns, residual_ns = clock.apply_ptp_sample(master_time_ns)

            with state_lock:
                ptp_state[name]["clock_offset_ms"] = error_ns / 1e6
                ptp_state[name]["ptp_sync_error_ms"] = residual_ns / 1e6
                ptp_state[name]["last_sync_time"] = time.time()

            socketio.emit("ptp_update", {
                "node": name,
                "clock_offset_ms": error_ns / 1e6,
                "ptp_sync_error_ms": residual_ns / 1e6,
                "last_sync_time": time.time(),
                "one_way_latency_ms": ptp_state[name]["one_way_latency_ms"],
            })
            last_ptp_sync = time.time()

        t = time.time() - t0

        if name == "jor_flight":
            try:
                data, _ = fg_sock.recvfrom(1024)
                parts = data.decode('utf-8').strip().split(',')
                if len(parts) >= 6:
                    lat = float(parts[0])
                    lon = float(parts[1])
                    alt = float(parts[2]) * 0.3048 
                    roll = math.radians(float(parts[3]))
                    pitch = math.radians(float(parts[4]))
                    yaw = math.radians(float(parts[5]))
                    marking = "C172_LIVE"
            except socket.timeout:
                marking = "C172_PARKED"
            except Exception as e:
                pass
        else:
            lat = cfg["lat"] + 0.1 * math.sin(0.02 * t + (hash(name) % 5))
            lon = cfg["lon"] + 0.1 * math.cos(0.02 * t + (hash(name) % 7))
            alt = 3000.0  
            roll = 0.0
            pitch = 0.0
            yaw = 0.02 * t
            marking = name[:11].upper()

        x, y, z = llh_to_ecef(lat, lon, alt)
        pdu = EntityStatePDU(
            entity_id=EntityID(site=1, application=1, entity=100 + list(NODES.keys()).index(name)),
            linear_velocity=Vec3f(0.0, 0.0, 0.0),
            location=Vec3d(x, y, z),
            orientation=Orientation(psi=yaw, theta=pitch, phi=roll),
            marking=marking
        )

        tx_ns = clock.now_ns()
        pkt = pack_message(MSG_DIS, seq, tx_ns, 0, name, pdu.pack())

        sock.sendto(pkt, (HOST_IP, HOST_PORT))
        sock.sendto(pdu.pack(), ("127.0.0.1", 3000))

        seq += 1
        
        if name == "jor_flight":
            time.sleep(1.0 / 20.0) 
        else:
            time.sleep(1.0 / 1.0) 

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def on_connect():
    with state_lock:
        snapshot_entities = list(entities.values())
        snapshot_status = [{"name": n, "status": node_status.get(n, "disconnected")} for n in NODES]
        ptp_snapshot = [
            {
                "node": n,
                "clock_offset_ms": ptp_state[n]["clock_offset_ms"],
                "ptp_sync_error_ms": ptp_state[n]["ptp_sync_error_ms"],
                "one_way_latency_ms": ptp_state[n]["one_way_latency_ms"],
            }
            for n in NODES
        ]

    for ent in snapshot_entities:
        socketio.emit("entity_update", ent)
    for st in snapshot_status:
        socketio.emit("node_status", st)
    for p in ptp_snapshot:
        socketio.emit("ptp_update", p)

def start_background_threads():
    threading.Thread(target=host_receiver_loop, daemon=True).start()
    threading.Thread(target=connection_monitor_loop, daemon=True).start()
    threading.Thread(target=host_ptp_broadcast_loop, daemon=True).start()

    for name in NODES:
        threading.Thread(target=node_publisher_loop, args=(name,), daemon=True).start()

if __name__ == "__main__":
    start_background_threads()
    socketio.run(
        app,
        host="127.0.0.1",
        port=8080,
        debug=False,
        allow_unsafe_werkzeug=True
    )