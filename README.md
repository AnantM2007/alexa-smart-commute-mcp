# 🚖 SmartCommute: Live Multimodal Travel & Fare Optimizer (Alexa+ MCP Server)

![MCP Spec](https://img.shields.io/badge/MCP_Spec-2025--11--25+-blue)
![Python](https://img.shields.io/badge/Python-3.8+-yellow)
![License](https://img.shields.io/badge/License-MIT-green)
![Track](https://img.shields.io/badge/Amazon_Hackathon-Alexa%2B_Track-orange)

**SmartCommute** is a real-time **Model Context Protocol (MCP) Server** and interactive **Alexa+ Smart Display Simulator** built for the **Build, Ship, Shape: Amazon Developer Hackathon (Alexa+ Track)**.

---

## 🎥 Video Demo
🔗 **Watch the Full Demo Video Here:** [PASTE YOUR YOUTUBE OR LOOM VIDEO LINK HERE]

---

## 💡 The Problem
Every day, commuters waste time switching between 3 to 4 separate apps—Google Maps for traffic, Uber/Ola for cab fares, Rapido for bike taxis, and Metro apps for train timings—just to answer one simple question:
> *"How do I reach my destination before my deadline without overspending?"*

## 🚀 The Solution
With **SmartCommute**, a user asks a single natural-language question to Alexa+ or any MCP-enabled AI agent:
> *"Alexa, I need to reach Z Square Mall from IIT Kanpur in 35 minutes. What is my fastest and cheapest option?"*

The AI agent invokes the `find_best_commute` tool on our live HTTP MCP server, which executes a 4-stage pipeline in real time:
1. **Live GPS Geocoding:** Converts any real-world origin and destination into exact latitude/longitude coordinates via the **OpenStreetMap Nominatim API**.
2. **Real Road Routing:** Fetches the actual road network distance (in km) and live driving duration via the **OSRM (Open Source Routing Machine) API**.
3. **Multimodal Fare & Time Engine:** Computes travel times and dynamic INR (`₹`) fares across four Indian transit modes:
   - 🛵 **Bike Taxi (Rapido):** Cuts through urban traffic congestion directly.
   - 🚇 **Metro Rail:** High-speed transit corridor calculation with station walk buffer.
   - 🚕 **AC Cab (Uber / Ola):** Full road distance with city traffic multiplier.
   - 🚌 **City AC Bus:** Economical public transit factoring in scheduled stop delays.
4. **Deadline Filtering & Voice Synthesis:** Filters out transit modes that will make the user late, returning both a structured JSON payload for visual cards and a conversational voice response for Alexa+.

---

## 🏛️ System Architecture

| Component | Technology Used | Role in Architecture |
| :--- | :--- | :--- |
| **MCP Client** | VS Code Copilot / Alexa+ Simulator | Sends JSON-RPC 2.0 `initialize`, `tools/list`, and `tools/call` requests over HTTP. |
| **MCP Server (`server.py`)** | Python `ThreadingHTTPServer` | Multi-threaded Streamable HTTP server listening on `http://localhost:8000/mcp`. |
| **Geocoding Layer** | OpenStreetMap Nominatim API | Resolves natural-language place names into live `(lat, lon)` GPS coordinates. |
| **Routing Engine** | Project OSRM Driving API | Computes real-world road distance (km) and base driving time (minutes). |
| **Multimodal UI (`index.html`)** | HTML5 / JS + Web Speech API | Renders visual route comparison cards and speaks the Alexa+ response aloud. |

### Protocol Flow:
1. **Client Request** $\rightarrow$ `POST http://localhost:8000/mcp` (`method: "tools/call"`, `name: "find_best_commute"`)
2. **MCP Server** $\rightarrow$ Queries `nominatim.openstreetmap.org` & `router.project-osrm.org`
3. **Decision Engine** $\rightarrow$ Evaluates `Bike Taxi`, `Metro Rail`, `AC Cab`, and `City AC Bus` against `max_time_minutes`
4. **Strict MCP Response** $\rightarrow$ Returns JSON-RPC 2.0 `result.content` back to the AI Agent & Smart Display UI

---

## 📂 Repository Structure

* **`server.py`** — Multi-threaded, zero-dependency Python MCP Server implementing MCP Spec `2025-11-25+` (`initialize`, `tools/list`, `tools/call`).
* **`index.html`** — Interactive Alexa+ Smart Display web simulator with live voice synthesis (`window.speechSynthesis`).
* **`mcp.json`** — Configuration file for connecting the HTTP MCP server directly to VS Code Copilot / MCP clients.
* **`requirements.txt`** — Environment documentation (runs natively on Python 3.8+ standard library with zero external C++ build dependencies).
* **`LICENSE`** — MIT Open Source License.

---

## ⚙️ How to Run Locally (Quick Start)

### Step 1: Clone the Repository & Start the MCP Server
No `pip install` is required! `server.py` uses Python's standard library for instant cross-platform execution:

    git clone [https://github.com/AnantM2007/alexa-smart-commute-mcp.git](https://github.com/AnantM2007/alexa-smart-commute-mcp.git)
    cd alexa-smart-commute-mcp
    python server.py

The server will start at: `http://localhost:8000/mcp`

### Step 2: Test with an AI Agent (VS Code MCP Client)
Move `mcp.json` into a `.vscode/mcp.json` folder in your workspace and ask Copilot Chat in Agent Mode:
> *"Using my MCP server, tell me the cheapest mode of transport from IIT Kanpur to Z Square Mall Kanpur."*

### Step 3: Launch the Alexa+ Smart Display Simulator
Open **`index.html`** in any modern browser, enter any two real-world locations and your deadline in minutes, and click **Ask Alexa+**.
