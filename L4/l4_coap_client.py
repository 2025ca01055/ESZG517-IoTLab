"""
=============================================================================
ESZG517 — Internet of Things: Design and Development
Lab Session L4 — Edge Intelligence and Protocol Comparison
Project 2: Smart Home Automation

l4_coap_client.py — CoAP Client: Smart Home Queries and Commands

WHAT THIS FILE DOES:
--------------------
This script connects to the CoAP server running on your local machine.
It performs the following in sequence:

1. GET the state of all three rooms
2. PUT light_on=True for bedroom1 (turn light ON)
3. GET bedroom1 again to confirm the change
4. PUT light_on=False for bedroom1 (turn light OFF)
5. GET bedroom1 again to confirm the change
6. Measure round-trip latency for 20 GET requests

HOW TO RUN:
-----------
Make sure l4_coap_server.py is already running in Terminal 1.
Then in Terminal 2: python3 l4_coap_client.py
=============================================================================
"""

import asyncio
import json
import time
import aiocoap

SERVER_URI = "coap://127.0.0.1/smarthome"


async def get_room_state(context, room):
    uri      = f"{SERVER_URI}/{room}"
    request  = aiocoap.Message(code=aiocoap.GET, uri=uri)
    response = await context.request(request).response
    payload  = json.loads(response.payload.decode("utf-8"))
    print(f"  [GET]  {room} → light_on={payload['light_on']}, last_motion={payload['last_motion']}")
    return payload


async def set_room_light(context, room, light_on):
    uri      = f"{SERVER_URI}/{room}"
    payload  = json.dumps({"light_on": light_on}).encode("utf-8")
    request  = aiocoap.Message(code=aiocoap.PUT, uri=uri, payload=payload)
    response = await context.request(request).response
    status   = "OK" if response.code == aiocoap.CHANGED else "FAILED"
    print(f"  [PUT]  {room} light_on={light_on} → {status}")
    return response.code == aiocoap.CHANGED


async def measure_latency(context, room, num_requests=20):
    latencies = []
    print(f"\n  Measuring latency for {num_requests} GET requests to {room}...")
    for i in range(num_requests):
        uri      = f"{SERVER_URI}/{room}"
        request  = aiocoap.Message(code=aiocoap.GET, uri=uri)
        start    = time.time()
        await context.request(request).response
        end      = time.time()
        latencies.append((end - start) * 1000)

    print(f"\n  ── CoAP GET Latency Results ({num_requests} requests) ──")
    print(f"  Min:     {min(latencies):.2f} ms")
    print(f"  Max:     {max(latencies):.2f} ms")
    print(f"  Average: {sum(latencies)/len(latencies):.2f} ms")
    print(f"  ──────────────────────────────────────")


async def main():
    print("=" * 60)
    print("ESZG517 L4 — CoAP Client")
    print("=" * 60)

    context = await aiocoap.Context.create_client_context()

    print("\n[STEP 1] Current state of all rooms:")
    for room in ["bedroom1", "bedroom2", "living_room"]:
        await get_room_state(context, room)

    print("\n[STEP 2] Turning bedroom1 light ON:")
    await set_room_light(context, "bedroom1", True)

    print("\n[STEP 3] Confirming bedroom1 state after PUT:")
    await get_room_state(context, "bedroom1")

    print("\n[STEP 4] Turning bedroom1 light OFF:")
    await set_room_light(context, "bedroom1", False)

    print("\n[STEP 5] Confirming bedroom1 state after PUT:")
    await get_room_state(context, "bedroom1")

    print("\n[STEP 6] Latency measurement:")
    await measure_latency(context, "bedroom1", num_requests=20)

    print("\n[DONE] CoAP client finished. Take a screenshot of this terminal.")


if __name__ == "__main__":
    asyncio.run(main())
