"""
AAFPA 2.0 — Interactive Web Studio
Standalone Web GUI for natural-language floor plan design and editing.
Zero third-party pip dependencies required (built using standard library http.server).
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any, List

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

from aafpa import (
    InteractiveFloorPlanStudioSession,
    get_studio_session,
    ArchitecturalOntology
)

SESSION = get_studio_session()

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AAFPA 2.0 — AI Agentic Floor Plan Architect Studio</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #0B0F19;
            --bg-card: #131B2E;
            --bg-card-hover: #1A243B;
            --border-subtle: #23314E;
            --primary: #38BDF8;
            --primary-glow: rgba(56, 189, 248, 0.25);
            --accent: #818CF8;
            --accent-green: #34D399;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --text-dim: #64748B;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Top Navbar */
        header {
            background: rgba(19, 27, 46, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-subtle);
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-logo {
            font-size: 24px;
        }

        .brand-title {
            font-size: 18px;
            font-weight: 700;
            background: linear-gradient(135deg, #38BDF8, #818CF8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-subtitle {
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(52, 211, 153, 0.12);
            border: 1px solid rgba(52, 211, 153, 0.3);
            color: var(--accent-green);
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--accent-green);
        }

        /* Main Workspace */
        .workspace {
            display: grid;
            grid-template-columns: 420px 1fr;
            flex: 1;
            overflow: hidden;
        }

        /* Left Chat Sidebar */
        .chat-sidebar {
            background: #0E1424;
            border-right: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            height: calc(100vh - 61px);
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            display: flex;
            flex-direction: column;
            gap: 6px;
            max-width: 90%;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            align-self: flex-end;
        }

        .message.system {
            align-self: flex-start;
        }

        .message-bubble {
            padding: 12px 16px;
            border-radius: 14px;
            font-size: 13.5px;
            line-height: 1.5;
        }

        .message.user .message-bubble {
            background: linear-gradient(135deg, #0284C7, #2563EB);
            color: #FFFFFF;
            border-bottom-right-radius: 4px;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
        }

        .message.system .message-bubble {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            color: var(--text-main);
            border-bottom-left-radius: 4px;
        }

        .message-meta {
            font-size: 11px;
            color: var(--text-dim);
            padding: 0 4px;
        }

        .chips-container {
            padding: 10px 16px;
            display: flex;
            gap: 8px;
            overflow-x: auto;
            background: rgba(19, 27, 46, 0.4);
            border-top: 1px solid var(--border-subtle);
        }

        .chip {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            color: var(--text-muted);
            padding: 6px 12px;
            border-radius: 999px;
            font-size: 11.5px;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.2s;
        }

        .chip:hover {
            background: var(--bg-card-hover);
            color: var(--primary);
            border-color: var(--primary);
        }

        /* Chat Input Box */
        .chat-input-area {
            padding: 16px;
            background: var(--bg-card);
            border-top: 1px solid var(--border-subtle);
            display: flex;
            gap: 10px;
        }

        .chat-input {
            flex: 1;
            background: #0B0F19;
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 12px 16px;
            color: var(--text-main);
            font-family: inherit;
            font-size: 13.5px;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px var(--primary-glow);
        }

        .btn-send {
            background: linear-gradient(135deg, #38BDF8, #2563EB);
            border: none;
            color: #FFFFFF;
            padding: 0 20px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-send:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        /* Right Canvas Area */
        .canvas-area {
            display: flex;
            flex-direction: column;
            background: radial-gradient(circle at 50% 50%, #111827 0%, #070B14 100%);
            padding: 24px;
            overflow-y: auto;
            position: relative;
        }

        .canvas-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .canvas-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-main);
        }

        .toolbar-btns {
            display: flex;
            gap: 8px;
        }

        .tool-btn {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            color: var(--text-muted);
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .tool-btn:hover {
            background: var(--bg-card-hover);
            color: var(--text-main);
            border-color: var(--primary);
        }

        /* Floor Plan Card / Viewport */
        .plan-viewport {
            background: #FFFFFF;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 520px;
        }

        /* 4 Layout Candidate Grid */
        .candidate-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            width: 100%;
        }

        .candidate-card {
            background: #FFFFFF;
            border-radius: 14px;
            padding: 16px;
            border: 2px solid #E2E8F0;
            cursor: pointer;
            transition: all 0.25s;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .candidate-card:hover {
            transform: translateY(-3px);
            border-color: #0284C7;
            box-shadow: 0 12px 24px rgba(2, 132, 199, 0.18);
        }

        .candidate-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .candidate-badge {
            background: #0284C7;
            color: #FFFFFF;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
        }

        .candidate-title {
            font-size: 13px;
            font-weight: 600;
            color: #0F172A;
        }

        /* Room Inspector Panel */
        .room-inspector {
            margin-top: 20px;
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 16px 20px;
        }

        .inspector-title {
            font-size: 13px;
            font-weight: 600;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 12px;
        }

        .room-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .room-tag {
            background: #0B0F19;
            border: 1px solid var(--border-subtle);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12px;
            display: flex;
            gap: 8px;
        }

        .room-tag-name {
            font-weight: 600;
            color: var(--text-main);
        }

        .room-tag-dim {
            color: var(--primary);
            font-family: 'JetBrains Mono', monospace;
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <span class="brand-logo">🏛️</span>
            <div>
                <div class="brand-title">AAFPA 2.0 Studio</div>
                <div class="brand-subtitle">AI Agentic Floor Plan Architect</div>
            </div>
        </div>
        <div class="status-badge">
            <div class="status-dot"></div>
            <span>NBC 2016 Compliant &bull; Active</span>
        </div>
    </header>

    <div class="workspace">
        <!-- Left: Conversational Console -->
        <div class="chat-sidebar">
            <div class="chat-messages" id="chatMessages">
                <div class="message system">
                    <div class="message-bubble">
                        👋 Welcome to <strong>AAFPA 2.0</strong>! Describe your housing requirements in plain language (e.g. <em>"3BHK on a 1500 sqft plot with large living room, modular kitchen, 3 bedrooms and 2 bathrooms"</em>).
                    </div>
                    <div class="message-meta">AI Architectural Assistant</div>
                </div>
            </div>

            <!-- Suggestion Chips -->
            <div class="chips-container">
                <div class="chip" onclick="sendQuickPrompt('3BHK on a 1500 sqft plot with modular kitchen, 3 bedrooms, 2 bathrooms')">✨ Generate 3BHK</div>
                <div class="chip" onclick="sendQuickPrompt('Make master bedroom bigger')">📐 Enlarge Master Bed</div>
                <div class="chip" onclick="sendQuickPrompt('Actually make it wider instead of longer')">↔️ Make it wider</div>
                <div class="chip" onclick="sendQuickPrompt('Take 20 sqft from dining for kitchen')">🔄 Transfer Area</div>
                <div class="chip" onclick="sendQuickPrompt('Remove balcony')">🗑️ Remove Balcony</div>
                <div class="chip" onclick="sendQuickPrompt('Can you make the house feel more spacious?')">🌟 Spacious Open-Plan</div>
            </div>

            <!-- Input bar -->
            <div class="chat-input-area">
                <input type="text" class="chat-input" id="userInput" placeholder="Type an architectural instruction..." onkeydown="if(event.key==='Enter') sendMessage()">
                <button class="btn-send" onclick="sendMessage()">Send</button>
            </div>
        </div>

        <!-- Right: CAD Floor Plan Visualizer -->
        <div class="canvas-area">
            <div class="canvas-toolbar">
                <div class="canvas-title" id="viewportTitle">Interactive Architectural Canvas</div>
                <div class="toolbar-btns">
                    <button class="tool-btn" onclick="sendQuickPrompt('Undo that.')">↩️ Undo</button>
                    <button class="tool-btn" onclick="sendQuickPrompt('Finalize plan.')">🔒 Finalize Plan</button>
                </div>
            </div>

            <div class="plan-viewport" id="planViewport">
                <div style="color: #64748B; font-size: 14px; text-align: center;">
                    📐 No floor plan generated yet.<br>Type your requirements in the chat to generate 4 distinct layout concepts!
                </div>
            </div>

            <!-- Live Room Program Table -->
            <div class="room-inspector" id="roomInspector" style="display: none;">
                <div class="inspector-title">Active Room Program & Dimensions</div>
                <div class="room-chips" id="roomTags"></div>
            </div>
        </div>
    </div>

    <script>
        let currentPlanData = null;

        function addMessage(text, isUser = false) {
            const container = document.getElementById('chatMessages');
            const msg = document.createElement('div');
            msg.className = 'message ' + (isUser ? 'user' : 'system');
            msg.innerHTML = `
                <div class="message-bubble">${text}</div>
                <div class="message-meta">${isUser ? 'You' : 'AI Architect'}</div>
            `;
            container.appendChild(msg);
            container.scrollTop = container.scrollHeight;
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;

            addMessage(text, true);
            input.value = '';

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: text })
                });
                const data = await res.json();
                handleServerResponse(data);
            } catch (err) {
                addMessage('❌ Error communicating with AAFPA server: ' + err.message);
            }
        }

        function sendQuickPrompt(text) {
            document.getElementById('userInput').value = text;
            sendMessage();
        }

        function handleServerResponse(data) {
            if (data.explanation) {
                addMessage(data.explanation);
            }

            // If 4 candidate layouts returned
            if (data.candidates && data.candidates.length > 0) {
                renderCandidateGrid(data.candidates);
                document.getElementById('viewportTitle').innerText = '4 Layout Candidate Concepts (Click one to select)';
            } else if (data.plan) {
                renderSinglePlan(data.plan);
                document.getElementById('viewportTitle').innerText = 'Active Working Floor Plan (v' + (data.version || 1) + ')';
            }
        }

        function renderCandidateGrid(candidates) {
            const viewport = document.getElementById('planViewport');
            let html = '<div class="candidate-grid">';
            candidates.forEach((c, idx) => {
                html += `
                    <div class="candidate-card" onclick="selectLayout(${idx + 1})">
                        <div class="candidate-header">
                            <span class="candidate-badge">LAYOUT ${idx + 1}</span>
                            <span class="candidate-title">${c.title}</span>
                        </div>
                        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px; min-height: 180px; display: flex; align-items: center; justify-content: center;">
                            ${generatePlanSVG(c.plan, 280, 200)}
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            viewport.innerHTML = html;
        }

        async function selectLayout(idx) {
            addMessage('Select Layout ' + idx, true);
            try {
                const res = await fetch('/api/select', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ option: idx })
                });
                const data = await res.json();
                handleServerResponse(data);
            } catch (err) {
                addMessage('❌ Error selecting layout: ' + err.message);
            }
        }

        function renderSinglePlan(plan) {
            currentPlanData = plan;
            const viewport = document.getElementById('planViewport');
            viewport.innerHTML = generatePlanSVG(plan, 580, 480, true);

            // Update room inspector tags
            const inspector = document.getElementById('roomInspector');
            const tags = document.getElementById('roomTags');
            if (plan.rooms && plan.rooms.length > 0) {
                inspector.style.display = 'block';
                tags.innerHTML = plan.rooms.map(r => `
                    <div class="room-tag">
                        <span class="room-tag-name">${r.type.replace('_',' ').toUpperCase()}</span>
                        <span class="room-tag-dim">${r.width.toFixed(1)}' x ${r.length.toFixed(1)}' (${r.area.toFixed(0)} sqft)</span>
                    </div>
                `).join('');
            }
        }

        function generatePlanSVG(plan, svgW, svgH, detailed = false) {
            const W = (plan.plot && plan.plot.width_ft) || 32.0;
            const L = (plan.plot && plan.plot.length_ft) || 31.25;

            const scale = Math.min((svgW - 40) / W, (svgH - 40) / L);
            const ox = (svgW - W * scale) / 2;
            const oy = (svgH - L * scale) / 2;

            const roomColors = {
                "living_room": "#E0E7FF",
                "master_bedroom": "#E2E8F0",
                "bedroom": "#F1F5F9",
                "kitchen": "#FEF08A",
                "dining": "#FEF3C7",
                "bathroom": "#BAE6FD",
                "balcony": "#D1FAE5",
                "study": "#EDE9FE",
                "pooja_room": "#FFEDD5",
                "corridor": "#F8FAFC"
            };

            let svg = `<svg width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}" style="font-family: 'Outfit', sans-serif;">`;
            // Outer plot
            svg += `<rect x="${ox}" y="${oy}" width="${W * scale}" height="${L * scale}" fill="#FFFFFF" stroke="#0F172A" stroke-width="3"/>`;

            // Rooms
            (plan.rooms || []).forEach(r => {
                const rx = ox + r.x * scale;
                const ry = oy + r.y * scale;
                const rw = r.width * scale;
                const rl = r.length * scale;
                const col = roomColors[r.type] || "#F1F5F9";

                svg += `<rect x="${rx}" y="${ry}" width="${rw}" height="${rl}" fill="${col}" stroke="#475569" stroke-width="1.5"/>`;
                
                const cx = rx + rw / 2;
                const cy = ry + rl / 2;
                const label = r.type.replace('_',' ').toUpperCase();
                const fontSz = detailed ? Math.max(9, Math.min(13, rw * 0.18)) : 9;

                svg += `<text x="${cx}" y="${cy - (detailed ? 4 : 0)}" font-size="${fontSz}" font-weight="bold" fill="#0F172A" text-anchor="middle">${label}</text>`;
                if (detailed) {
                    svg += `<text x="${cx}" y="${cy + 12}" font-size="${fontSz - 2}" fill="#475569" text-anchor="middle">${r.width.toFixed(1)}' x ${r.length.toFixed(1)}'</text>`;
                }
            });

            svg += `</svg>`;
            return svg;
        }
    </script>
</body>
</html>
"""

class AAFPAStudioHTTPHandler(BaseHTTPRequestHandler):
    """Serves the Interactive Web Studio frontend and handles REST API requests."""

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if self.path == "/api/chat":
            prompt = req_data.get("prompt", "")
            res = SESSION.handle_message(prompt)
            self._send_json(self._serialize_response(res))

        elif self.path == "/api/select":
            opt = int(req_data.get("option", 1))
            res = SESSION.select_layout(opt)
            self._send_json(self._serialize_response(res))

        else:
            self.send_response(404)
            self.end_headers()

    def _send_json(self, data: Dict[str, Any]):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _serialize_response(self, res: Dict[str, Any]) -> Dict[str, Any]:
        """Serializes plans into JSON-safe dictionaries."""
        out = {
            "status": res.get("status", "success"),
            "explanation": res.get("explanation", ""),
            "version": res.get("version", 1)
        }
        if "candidates" in res and res["candidates"]:
            out["candidates"] = []
            for c in res["candidates"]:
                out["candidates"].append({
                    "title": c.get("title", ""),
                    "topology": c.get("topology", ""),
                    "plan": self._serialize_plan(c.get("plan"))
                })
        elif "plan" in res and res["plan"]:
            out["plan"] = self._serialize_plan(res["plan"])
        return out

    def _serialize_plan(self, plan: Any) -> Optional[Dict[str, Any]]:
        if not plan:
            return None
        rooms = []
        for r in getattr(plan, 'rooms', []):
            rooms.append({
                "id": getattr(r, 'id', ''),
                "type": getattr(r, 'type', ''),
                "x": float(getattr(r, 'x', 0)),
                "y": float(getattr(r, 'y', 0)),
                "width": float(getattr(r, 'width', 0)),
                "length": float(getattr(r, 'length', 0)),
                "area": float(getattr(r, 'area', 0))
            })
        plot = getattr(plan, 'plot', None)
        return {
            "version": getattr(plan, 'version', 1),
            "topology": getattr(plan, 'topology', 'open_plan'),
            "plot": {
                "width_ft": float(getattr(plot, 'width_ft', 32.0)) if plot else 32.0,
                "length_ft": float(getattr(plot, 'length_ft', 31.25)) if plot else 31.25,
                "area_sqft": float(getattr(plot, 'area_sqft', 1000.0)) if plot else 1000.0
            },
            "rooms": rooms
        }

def launch_web_studio(port: int = 8000):
    server = HTTPServer(("127.0.0.1", port), AAFPAStudioHTTPHandler)
    print("=" * 80)
    print(f"🏛️  AAFPA 2.0 INTERACTIVE WEB STUDIO IS LIVE!")
    print(f"👉 Open your browser at: http://localhost:{port}")
    print("Press Ctrl+C to stop the studio server.")
    print("=" * 80)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStudio server stopped.")

if __name__ == "__main__":
    launch_web_studio()
