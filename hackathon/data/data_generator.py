import random
import json
from datetime import datetime, timedelta
from uuid import uuid4
from faker import Faker

fake = Faker()

REASONS = {
    "voice": [
        "call drop", "cannot make calls", "poor call quality", "no signal",
        "call not connecting", "distorted voice", "echo on call", "delayed voice",
        "mute/unmute problem", "number unreachable", "cross connection", "noise/static in call",
        "international call issue", "roaming call issue", "blocked outgoing calls",
        "caller ID not working", "missed call alerts not working", "conference call issue",
        "call forwarding not working", "repeated call disconnection"
    ],
    "internet": [
        "slow internet", "no internet", "intermittent connectivity", "mobile data not working",
        "router not working", "5G not available", "DNS issues", "IP address conflict",
        "Wi-Fi authentication error", "network congestion", "speed lower than plan",
        "data usage not updating", "unable to connect to VPN", "LAN port failure", "ISP outage",
        "fiber line cut", "internet LED blinking", "parental controls not working",
        "streaming buffering", "online gaming lag"
    ],
    "billing": [
        "billing dispute", "refund request", "double charge", "late fee dispute",
        "promo not applied", "overcharged for usage", "incorrect bill amount", "missed payment fee",
        "advance rental charge", "taxes unclear", "roaming charges incorrect", "payment not reflected",
        "auto-debit issue", "wrong add-on billed", "partial refund", "plan downgrade fee",
        "bill not received", "billing cycle clarification", "discount not applied", "duplicate invoice"
    ],
    "sim": [
        "SIM activation issue", "lost SIM replacement", "block SIM", "SIM not detected",
        "porting request delay", "eSIM activation", "SIM delivery delayed", "SIM swap security check",
        "PUK code needed", "SIM not connecting to network", "damaged SIM", "wrong SIM issued",
        "multi-SIM configuration", "eSIM profile delete", "roaming SIM inactive"
    ],
    "plans": [
        "change plan", "upgrade package", "plan downgrade", "family plan setup", "plan cancellation",
        "plan not reflecting", "add-on not activated", "data pack expired", "combo plan inquiry",
        "unlimited plan limit", "plan not compatible", "voice pack activation", "plan auto-renewal failed",
        "plan duration mismatch", "change billing frequency"
    ],
    "account": [
        "update contact info", "email not verified", "account locked", "change password",
        "unable to login", "account suspended", "KYC update required", "app login error",
        "wrong account linked", "account merge request"
    ]
}

CATEGORY_WEIGHTS = {
    "billing": 0.25,
    "internet": 0.25,
    "voice": 0.20,
    "sim": 0.15,
    "plans": 0.10,
    "account": 0.05
}


def pick_reason():
    categories = list(REASONS.keys())
    weights = [CATEGORY_WEIGHTS[cat] for cat in categories]
    category = random.choices(categories, weights=weights, k=1)[0]
    reason = random.choice(REASONS[category])
    return reason, category


def generate_event_sequence(start_time, end_time, reason):
    events = []
    t = start_time
    steps = ["ringing", "answered", "greeting", "interaction", "resolution", "ended"]
    
    for step in steps:
        t += timedelta(seconds=random.randint(5, 60))
        event = {"event_type": step, "timestamp": t.isoformat() + "Z"}
        
        if step == "greeting":
            event["details"] = {
                "agent_greeting": f"Hello, thank you for calling TelecomX, "
                f"my name is {fake.first_name()}, how can I help you today?"
            }
        elif step == "interaction":
            event["details"] = {"customer_request": f"I need help with {reason}."}
        elif step == "resolution":
            event["details"] = {"solution": f"{reason} addressed"}
        
        events.append(event)
    
    return events


def generate_record(call_id):
    start_time = fake.date_time_between(start_date='-6M', end_date='now')
    duration = random.randint(180, 1800)  # 3 to 30 min
    end_time = start_time + timedelta(seconds=duration)
    reason, category = pick_reason()
    disposition = random.choices(
        ["resolved", "unresolved", "escalated"],
        weights=[0.7, 0.2, 0.1]
    )[0]

    return {
        "call_id": str(call_id),
        "start_time": start_time.isoformat() + "Z",
        "end_time": end_time.isoformat() + "Z",
        "duration": duration,
        "customer": {
            "customer_id": f"C{random.randint(1000, 9999)}",
            "phone_number": fake.phone_number(),
            "name": fake.name(),
            "email": fake.email()
        },
        "agent": {
            "agent_id": f"A{random.randint(100, 999)}",
            "name": fake.name(),
            "extension": str(random.randint(100, 999))
        },
        "queue_name": "Support Queue",
        "call_type": random.choice(["inbound", "outbound"]),
        "disposition": disposition,
        "reason": reason,
        "category": category,
        "notes": f"Customer called regarding {reason}. Issue was {disposition}.",
        "events": generate_event_sequence(start_time, end_time, reason),
        "recording_url": f"https://example.com/recordings/{call_id}.wav"
    }


def generate_data(n_records=100000, output_file="telecom_calls.jsonl"):
    with open(output_file, "w") as f:
        for i in range(n_records):
            record = generate_record(i)
            f.write(json.dumps(record) + "\n")
    print(f"{n_records} records saved to {output_file}")


if __name__ == "__main__":
    generate_data(n_records=100000)