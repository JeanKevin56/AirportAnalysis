import os, random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

SEED = 23
np.random.seed(SEED)
random.seed(SEED)

os.makedirs("data", exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# 1.  ACCESS POINTS
# ══════════════════════════════════════════════════════════════════════════════
# x / y are pixel-like coordinates on a schematic airport map (0-100 scale).
# threshold = max recommended simultaneous devices before a warning fires.

AP_DATA = [
    # ── Departures side ──────────────────────────────────────────────────────
    {"ap_id": "AP-CHECKIN-01",  "name": "Check-in Hall A",      "zone": "Check-in",   "x":  8, "y": 55, "threshold":  80},
    {"ap_id": "AP-CHECKIN-02",  "name": "Check-in Hall B",      "zone": "Check-in",   "x": 18, "y": 55, "threshold":  80},
    {"ap_id": "AP-SECURITY-01", "name": "Security Lane 1",      "zone": "Security",   "x": 33, "y": 60, "threshold":  50},
    {"ap_id": "AP-SECURITY-02", "name": "Security Lane 2",      "zone": "Security",   "x": 33, "y": 45, "threshold":  50},
    {"ap_id": "AP-FOOD-01",     "name": "Food Court – Main",    "zone": "Food Court", "x": 50, "y": 68, "threshold": 110},
    {"ap_id": "AP-FOOD-02",     "name": "Food Court – Annex",   "zone": "Food Court", "x": 58, "y": 68, "threshold":  75},
    {"ap_id": "AP-LOUNGE-01",   "name": "Business Lounge",      "zone": "Lounge",     "x": 52, "y": 38, "threshold":  35},
    # ── Gates A (far end) ────────────────────────────────────────────────────
    {"ap_id": "AP-GATE-A1",     "name": "Gate A1",              "zone": "Gates A",    "x": 72, "y": 80, "threshold": 130},
    {"ap_id": "AP-GATE-A2",     "name": "Gate A2",              "zone": "Gates A",    "x": 80, "y": 80, "threshold": 130},
    {"ap_id": "AP-GATE-A3",     "name": "Gate A3",              "zone": "Gates A",    "x": 88, "y": 80, "threshold": 130},
    # ── Gates B ──────────────────────────────────────────────────────────────
    {"ap_id": "AP-GATE-B1",     "name": "Gate B1",              "zone": "Gates B",    "x": 72, "y": 42, "threshold": 110},
    {"ap_id": "AP-GATE-B2",     "name": "Gate B2",              "zone": "Gates B",    "x": 80, "y": 42, "threshold": 110},
    # ── Arrivals side ────────────────────────────────────────────────────────
    {"ap_id": "AP-ARRIVALS-01", "name": "Arrivals Hall",        "zone": "Arrivals",   "x": 15, "y": 22, "threshold":  90},
    {"ap_id": "AP-BAGGAGE-01",  "name": "Baggage Claim 1",      "zone": "Arrivals",   "x": 22, "y": 14, "threshold":  80},
    {"ap_id": "AP-BAGGAGE-02",  "name": "Baggage Claim 2",      "zone": "Arrivals",   "x": 30, "y": 14, "threshold":  80},
]

ap_df = pd.DataFrame(AP_DATA)
ap_df.to_csv("data/access_points.csv", index=False)
print(f"[✓] access_points.csv  →  {len(ap_df)} access points")


# ══════════════════════════════════════════════════════════════════════════════
# 2.  FLIGHT SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════
BASE_DATE = datetime(2025, 6, 12)

def t(h, m=0):
    """Return a datetime for the simulation day at hh:mm."""
    return BASE_DATE + timedelta(hours=h, minutes=m)

DEPARTING_FLIGHTS = [
    {"flight": "QR801", "gate": "AP-GATE-A1", "departs": t(8, 30),  "pax": 120, "business_ratio": 0.15},
    {"flight": "QR101", "gate": "AP-GATE-A2", "departs": t(10,  0), "pax":  95, "business_ratio": 0.10},
    {"flight": "QR915", "gate": "AP-GATE-B1", "departs": t(9, 15),  "pax": 105, "business_ratio": 0.20},
    {"flight": "QR201", "gate": "AP-GATE-A3", "departs": t(12,  0), "pax": 140, "business_ratio": 0.08},
    {"flight": "QR220", "gate": "AP-GATE-A1", "departs": t(12, 20),  "pax": 120, "business_ratio": 0.15},
    {"flight": "QR301", "gate": "AP-GATE-A2", "departs": t(13,  0), "pax":  95, "business_ratio": 0.10},
    {"flight": "QR315", "gate": "AP-GATE-B1", "departs": t(13, 15),  "pax": 105, "business_ratio": 0.20},
    {"flight": "QR401", "gate": "AP-GATE-A3", "departs": t(14,  0), "pax": 140, "business_ratio": 0.08},
    {"flight": "QR430", "gate": "AP-GATE-B2", "departs": t(14, 30), "pax": 150, "business_ratio": 0.4}
]

ARRIVING_FLIGHTS = [
    {"flight": "QR102", "baggage": "AP-BAGGAGE-01", "arrives": t(7, 0),  "pax":  90},
    {"flight": "QR204", "baggage": "AP-BAGGAGE-02", "arrives": t(7, 30),  "pax": 115},
    {"flight": "QR308", "baggage": "AP-BAGGAGE-01", "arrives": t(8,  0), "pax": 100},
    {"flight": "QR102", "baggage": "AP-BAGGAGE-02", "arrives": t(8, 45),  "pax":  90},
    {"flight": "QR204", "baggage": "AP-BAGGAGE-01", "arrives": t(9, 30),  "pax": 115},
    {"flight": "QR308", "baggage": "AP-BAGGAGE-02", "arrives": t(10,  0), "pax": 100},
    {"flight": "QR102", "baggage": "AP-BAGGAGE-01", "arrives": t(11, 45),  "pax":  90},
    {"flight": "QR204", "baggage": "AP-BAGGAGE-02", "arrives": t(11, 30),  "pax": 115},
    {"flight": "QR308", "baggage": "AP-BAGGAGE-01", "arrives": t(12,  0), "pax": 100},
    {"flight": "QR102", "baggage": "AP-BAGGAGE-02", "arrives": t(12, 45),  "pax":  90},
    {"flight": "QR204", "baggage": "AP-BAGGAGE-01", "arrives": t(13, 30),  "pax": 130},
    {"flight": "QR308", "baggage": "AP-BAGGAGE-02", "arrives": t(14,  0), "pax": 100},
]


# ══════════════════════════════════════════════════════════════════════════════
# 3.  HELPER UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

FIRST_NAMES = ["Alice","Bob","Carlos","Diana","Eric","Fatima","George","Hana",
               "Ivan","Julia","Karim","Layla","Marco","Nina","Omar","Petra",
               "Quentin","Rosa","Sam","Talia","Ugo","Vera","Will","Xena",
               "Yann","Zahra","Adrien","Beatrice","Cyrus","Dina"]
LAST_NAMES  = ["Martin","Dupont","Smith","Kowalski","Al-Rashid","Chen","Müller",
               "Rossi","Patel","Nguyen","Johansson","Garcia","Kim","Okafor",
               "Svensson","Brown","Leroy","Costa","Ivanov","Yamamoto"]
EMAIL_DOMAINS = ["gmail.com","yahoo.com","outlook.com","icloud.com","hotmail.com"]

_used_emails: set = set()

def random_email():
    while True:
        fn = random.choice(FIRST_NAMES).lower()
        ln = random.choice(LAST_NAMES).lower()
        suffix = random.randint(1, 999)
        dom = random.choice(EMAIL_DOMAINS)
        email = f"{fn}.{ln}{suffix}@{dom}"
        if email not in _used_emails:
            _used_emails.add(email)
            return email

_mac_counter = 0
def random_mac():
    global _mac_counter
    _mac_counter += 1
    # OUI prefix distinguishes personal devices from machine accounts
    return "F4:5C:{:02X}:{:02X}:{:02X}:{:02X}".format(
        (_mac_counter >> 24) & 0xFF,
        (_mac_counter >> 16) & 0xFF,
        (_mac_counter >>  8) & 0xFF,
         _mac_counter        & 0xFF,
    )

def jitter(seconds: int) -> timedelta:
    """Return a random timedelta ± seconds."""
    return timedelta(seconds=random.uniform(-seconds, seconds))

def log_entries(mac, identity, ap_id, start: datetime, dwell_minutes: float):
    """
    Simulate several WiFi association events during dwell_minutes at an AP.
    A device typically associates once, possibly re-associates if it sleeps.
    """
    events = []
    end = start + timedelta(minutes=dwell_minutes)
    ts = start + jitter(30)
    while ts < end:
        events.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "ap_id":     ap_id,
            "mac":       mac,
            "identity":  identity,
            "rssi":      random.randint(-75, -35),     # dBm signal strength
        })
        # re-associate after 3-8 minutes (DHCP lease, power-save wakeup, etc.)
        ts += timedelta(minutes=random.uniform(3, 8)) + jitter(60)
    return events


# ══════════════════════════════════════════════════════════════════════════════
# 4.  MACHINE ACCOUNTS  (anchored to one AP, never move)
# ══════════════════════════════════════════════════════════════════════════════
MACHINES = [
    {"mac": "AA:BB:00:00:00:01", "identity": "svc-kiosk-01@airport-systems.com", "ap_id": "AP-CHECKIN-01"},
    {"mac": "AA:BB:00:00:00:02", "identity": "svc-kiosk-02@airport-systems.com", "ap_id": "AP-CHECKIN-02"},
    {"mac": "AA:BB:00:00:00:03", "identity": "PRINTER-SECURITY-01",              "ap_id": "AP-SECURITY-01"},
    {"mac": "AA:BB:00:00:00:04", "identity": "svc-scanner@airport-systems.com",  "ap_id": "AP-SECURITY-02"},
    {"mac": "AA:BB:00:00:00:05", "identity": "DISPLAY-FOOD-COURT-01",            "ap_id": "AP-FOOD-01"},
    {"mac": "AA:BB:00:00:00:06", "identity": "CAMERA-GATE-A1",                   "ap_id": "AP-GATE-A1"},
    {"mac": "AA:BB:00:00:00:07", "identity": "CAMERA-GATE-B1",                   "ap_id": "AP-GATE-B1"},
    {"mac": "AA:BB:00:00:00:08", "identity": "svc-baggage@airport-systems.com",  "ap_id": "AP-BAGGAGE-01"},
    {"mac": "AA:BB:00:00:00:09", "identity": "PRINTER-LOUNGE-01",                "ap_id": "AP-LOUNGE-01"},
    {"mac": "AA:BB:00:00:00:10", "identity": "svc-infodesk@airport-systems.com", "ap_id": "AP-ARRIVALS-01"},
]

all_logs = []

# Machines are active from 05:30 to 23:30 → ~1080 minutes
for m in MACHINES:
    all_logs += log_entries(m["mac"], m["identity"], m["ap_id"],
                            start=t(5, 30), dwell_minutes=1080)


# ══════════════════════════════════════════════════════════════════════════════
# 5.  DEPARTING PASSENGERS
# ══════════════════════════════════════════════════════════════════════════════
# Typical path  →  check-in  →  security  →  [food/lounge]  →  gate
# Dwell times are in minutes (normally distributed around the mean).

def dwell(mean, std, mn=1):
    return max(mn, np.random.normal(mean, std))

for flight in DEPARTING_FLIGHTS:
    departure  = flight["departs"]
    gate_ap    = flight["gate"]
    n_pax      = flight["pax"]
    biz_ratio  = flight["business_ratio"]

    for i in range(n_pax):
        is_business = random.random() < biz_ratio
        email = random_email()
        mac   = random_mac()

        # ── Check-in: 90–30 min before departure ──────────────────────────
        checkin_ap  = random.choice(["AP-CHECKIN-01", "AP-CHECKIN-02"])
        checkin_offset = random.uniform(30, 90)        # minutes before dep
        checkin_start  = departure - timedelta(minutes=checkin_offset)
        checkin_dwell  = dwell(12, 4, mn=3)            # ~12 min at check-in

        all_logs += log_entries(mac, email, checkin_ap, checkin_start, checkin_dwell)

        # ── Security: right after check-in ────────────────────────────────
        sec_ap    = random.choice(["AP-SECURITY-01", "AP-SECURITY-02"])
        sec_start = checkin_start + timedelta(minutes=checkin_dwell) + timedelta(minutes=random.uniform(2, 6))
        sec_dwell = dwell(15, 6, mn=5)                 # queue + screening

        all_logs += log_entries(mac, email, sec_ap, sec_start, sec_dwell)

        # ── Food court / lounge (most passengers stop here) ───────────────
        after_sec = sec_start + timedelta(minutes=sec_dwell)

        if is_business:
            # Business → lounge
            if random.random() < 0.85:
                lounge_dwell = dwell(40, 15, mn=10)
                all_logs += log_entries(mac, email, "AP-LOUNGE-01", after_sec, lounge_dwell)
                after_sec += timedelta(minutes=lounge_dwell)
        else:
            # Economy → food court (70% chance), or straight to gate
            if random.random() < 0.70:
                food_ap    = random.choice(["AP-FOOD-01", "AP-FOOD-02"])
                food_dwell = dwell(25, 10, mn=5)
                all_logs += log_entries(mac, email, food_ap, after_sec, food_dwell)
                after_sec += timedelta(minutes=food_dwell)

        # ── Gate: arrive ~25 min before departure, until boarding ─────────
        gate_start = departure - timedelta(minutes=random.uniform(5, 35))
        gate_start = max(gate_start, after_sec + timedelta(minutes=2))
        gate_dwell = (departure - gate_start).total_seconds() / 60 + 5
        gate_dwell = max(gate_dwell, 5)

        all_logs += log_entries(mac, email, gate_ap, gate_start, gate_dwell)


# ══════════════════════════════════════════════════════════════════════════════
# 6.  ARRIVING PASSENGERS
# ══════════════════════════════════════════════════════════════════════════════
# Path  →  arrivals hall  →  baggage claim  →  (exit / disappear)

for flight in ARRIVING_FLIGHTS:
    arrival     = flight["arrives"]
    baggage_ap  = flight["baggage"]
    n_pax       = flight["pax"]

    for i in range(n_pax):
        email = random_email()
        mac   = random_mac()

        # Walk from gate bridge to arrivals hall: 5–15 min after landing
        arr_start = arrival + timedelta(minutes=random.uniform(5, 15))
        arr_dwell = dwell(10, 4, mn=2)

        all_logs += log_entries(mac, email, "AP-ARRIVALS-01", arr_start, arr_dwell)

        # Baggage claim
        bag_start = arr_start + timedelta(minutes=arr_dwell) + timedelta(minutes=random.uniform(1, 4))
        bag_dwell = dwell(18, 7, mn=5)

        all_logs += log_entries(mac, email, baggage_ap, bag_start, bag_dwell)
        # Passenger exits the building → no more WiFi events


# ══════════════════════════════════════════════════════════════════════════════
# 7.  EXPORT
# ══════════════════════════════════════════════════════════════════════════════

log_df = pd.DataFrame(all_logs)
log_df["timestamp"] = pd.to_datetime(log_df["timestamp"])
log_df = log_df.sort_values("timestamp").reset_index(drop=True)
log_df["timestamp"] = log_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

log_df.to_csv("data/wifi_logs.csv", index=False)

n_unique_macs   = log_df["mac"].nunique()
n_machine_macs  = len(MACHINES)
n_human_macs    = n_unique_macs - n_machine_macs

print(f"[✓] wifi_logs.csv      →  {len(log_df):,} log entries")
print(f"    ├─ Unique devices   : {n_unique_macs:,}")
print(f"    ├─ Machine accounts : {n_machine_macs}")
print(f"    └─ Human passengers : {n_human_macs:,}")
print("\nDataset generation complete. Run airport_analysis.py next.")
