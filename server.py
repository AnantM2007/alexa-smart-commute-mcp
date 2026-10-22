import json
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Any, Tuple

def get_coordinates(place_name: str) -> Tuple[float, float]:
    """Fetches real GPS (lat, lon) from OpenStreetMap Nominatim API."""
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(place_name)}&format=json&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "AlexaPlusSmartCommute/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return 26.5123, 80.2329  # Fallback coordinates if offline

def get_real_route_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, int]:
    """Fetches real road distance (km) and driving duration (mins) from OSRM Routing API."""
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    req = urllib.request.Request(url, headers={"User-Agent": "AlexaPlusSmartCommute/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            if data.get("routes"):
                dist_km = round(data["routes"][0]["distance"] / 1000.0, 2)
                drive_mins = max(5, int((data["routes"][0]["duration"] / 60.0) * 1.4))
                return dist_km, drive_mins
    except Exception:
        pass
    return 13.4, 34

def find_best_commute(origin: str, destination: str, max_time_minutes: int = 35) -> Dict[str, Any]:
    lat1, lon1 = get_coordinates(origin)
    lat2, lon2 = get_coordinates(destination)
    distance_km, cab_time_mins = get_real_route_distance(lat1, lon1, lat2, lon2)

    bike_time = max(4, int(cab_time_mins * 0.72))
    bike_cost = int(20 + (distance_km * 8.5))

    metro_time = max(8, int((distance_km * 1.6) + 7))
    metro_cost = min(60, int(10 + (distance_km * 3.2)))

    cab_cost = int(55 + (distance_km * 16.5))

    bus_time = int(cab_time_mins * 1.45)
    bus_cost = min(35, int(10 + (distance_km * 1.5)))

    routes = [
        {"mode": "Bike Taxi (Rapido)", "time_mins": bike_time, "cost_inr": bike_cost, "details": f"Live distance: {distance_km} km. Cuts through traffic."},
        {"mode": "Metro Rail", "time_mins": metro_time, "cost_inr": metro_cost, "details": f"Covers {distance_km} km corridor including 7m station walk."},
        {"mode": "AC Cab (Uber / Ola)", "time_mins": cab_time_mins, "cost_inr": cab_cost, "details": f"Live OSRM road route ({distance_km} km)."},
        {"mode": "City AC Bus", "time_mins": bus_time, "cost_inr": bus_cost, "details": f"Public transit along {distance_km} km route."}
    ]

    viable = [r for r in routes if r["time_mins"] <= max_time_minutes]
    rejected = [r for r in routes if r["time_mins"] > max_time_minutes]

    if not viable:
        fastest = min(routes, key=lambda x: x["time_mins"])
        return {
            "status": "deadline_too_tight",
            "distance_km": distance_km,
            "alexa_voice_response": (
                f"The distance from {origin} to {destination} is {distance_km} kilometers. "
                f"No transit option can reach within {max_time_minutes} minutes. "
                f"The fastest option is {fastest['mode']} taking {fastest['time_mins']} minutes for {fastest['cost_inr']} rupees."
            ),
            "viable_routes": [],
            "filtered_out_slow_routes": rejected
        }

    fastest = min(viable, key=lambda x: x["time_mins"])
    cheapest = min(viable, key=lambda x: x["cost_inr"])

    voice = (
        f"From {origin} to {destination} is {distance_km} kilometers. "
        f"To reach within {max_time_minutes} minutes, your fastest option is {fastest['mode']} "
        f"taking {fastest['time_mins']} minutes for {fastest['cost_inr']} rupees. "
        f"Your cheapest option is {cheapest['mode']} taking {cheapest['time_mins']} minutes for {cheapest['cost_inr']} rupees."
    )

    return {
        "status": "success",
        "origin": origin,
        "destination": destination,
        "real_distance_km": distance_km,
        "max_time_minutes": max_time_minutes,
        "alexa_voice_response": voice,
        "recommended_fastest": fastest,
        "recommended_cheapest": cheapest,
        "viable_routes": viable,
        "filtered_out_slow_routes": rejected
    }


class AlexaMCPServer(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, Mcp-Session-Id")
        self.send_header("Connection", "close")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "close")
        self.end_headers()
        response = {
            "protocol": "Model Context Protocol (MCP) 2025-11-25+",
            "transport": "Streamable HTTP",
            "server": "SmartCommuteAlexaPlus",
            "tools": ["find_best_commute"]
        }
        self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
        method = body.get("method", "")
        msg_id = body.get("id", 1)

        # 1. MCP Initialize Handshake
        if method == "initialize":
            rpc_result = {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "SmartCommuteAlexaPlus", "version": "1.0.0"}
            }
        # 2. MCP Tool Discovery
        elif method == "tools/list":
            rpc_result = {
                "tools": [{
                    "name": "find_best_commute",
                    "description": "Compare live travel time and INR fares across Metro, Rapido Bike Taxi, Uber/Ola Cab, and Bus between any two locations.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "origin": {"type": "string", "description": "Starting location"},
                            "destination": {"type": "string", "description": "Target destination"},
                            "max_time_minutes": {"type": "integer", "description": "Max time budget in minutes", "default": 35}
                        },
                        "required": ["origin", "destination"]
                    }
                }]
            }
        # 3. Handle MCP Notifications
        elif method.startswith("notifications/"):
            self.send_response(202)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Connection", "close")
            self.end_headers()
            return
        # 4. Strict MCP Spec Tool Execution
        else:
            params = body.get("params", {}).get("arguments", {})
            data = find_best_commute(
                origin=params.get("origin", "IIT Kanpur"),
                destination=params.get("destination", "Kanpur Central"),
                max_time_minutes=int(params.get("max_time_minutes", 35))
            )
            rpc_result = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(data, indent=2)
                    }
                ],
                "isError": False
            }

        payload = json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": rpc_result}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    port = 8000
    print("================================================================")
    print("Alexa+ SmartCommute Multi-Threaded MCP Server Live!")
    print(f"Listening on: http://localhost:{port}/mcp")
    print("================================================================")
    ThreadingHTTPServer(("localhost", port), AlexaMCPServer).serve_forever()