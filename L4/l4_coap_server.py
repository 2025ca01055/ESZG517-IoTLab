"""
=============================================================================
ESZG517 — Internet of Things: Design and Development
Lab Session L4 — Edge Intelligence and Protocol Comparison
Project 2: Smart Home Automation

l4_coap_server.py — CoAP Server: Smart Home State

WHAT THIS FILE DOES:
--------------------
This script runs a CoAP server on your local machine.
It exposes three smart home rooms as CoAP resources.

Each room is accessible at:
   coap://localhost/smarthome/<room_name>

GET  → returns current room state (light on/off)
PUT  → updates the light state for that room

This is a LOCAL server — it does not connect to HiveMQ.
Run this in Terminal 1 BEFORE running l4_coap_client.py.

HOW TO RUN:
-----------
Terminal 1:  python3 l4_coap_server.py
Terminal 2:  python3 l4_coap_client.py  (in a separate terminal)
=============================================================================
"""

import asyncio
import json
import datetime
import aiocoap
import aiocoap.resource as resource


# =============================================================================
# IN-MEMORY STATE STORE
# =============================================================================

room_states = {
    "bedroom1":    {"light_on": False, "last_motion": None},
    "bedroom2":    {"light_on": False, "last_motion": None},
    "living_room": {"light_on": False, "last_motion": None},
}


# =============================================================================
# ROOM RESOURCE
# =============================================================================

class RoomResource(resource.Resource):

    def __init__(self, room_name):
        super().__init__()
        self.room_name = room_name

    async def render_get(self, request):
        state = room_states[self.room_name]
        payload = json.dumps({
            "room":        self.room_name,
            "light_on":    state["light_on"],
            "last_motion": state["last_motion"] or "never"
        })
        print(f"[GET]  /smarthome/{self.room_name} → {payload}")
        return aiocoap.Message(code=aiocoap.CONTENT, payload=payload.encode("utf-8"))

    async def render_put(self, request):
        try:
            data = json.loads(request.payload.decode("utf-8"))
            room_states[self.room_name]["light_on"] = data["light_on"]
            room_states[self.room_name]["last_motion"] = datetime.datetime.now().isoformat()
            print(f"[PUT]  /smarthome/{self.room_name} → light_on={data['light_on']}")
            return aiocoap.Message(code=aiocoap.CHANGED)
        except Exception as e:
            print(f"[ERROR] Bad request: {e}")
            return aiocoap.Message(code=aiocoap.BAD_REQUEST)


# =============================================================================
# MAIN
# =============================================================================

async def main():
    site = resource.Site()

    for room_name in room_states:
        site.add_resource(["smarthome", room_name], RoomResource(room_name))
        print(f"[RESOURCE] coap://localhost/smarthome/{room_name}")

    await aiocoap.Context.create_server_context(site, bind=("127.0.0.1", 5683))

    print("\n[SERVER RUNNING] CoAP server is ready.")
    print("Open Terminal 2 and run: python3 l4_coap_client.py\n")

    await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
