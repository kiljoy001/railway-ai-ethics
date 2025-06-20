from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import httpx
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List
import json
from vastai_sdk import VastAI
from config import DEMO_MODE
import time

last_crisis_time = 0
countdown_duration = 120
load_dotenv()
app = FastAPI()

event_log: Dict[str, List] = {
    "usa": [],
    "china": [],
    "neutral": []
}

# Vast.ai API key
VAST_API_KEY = os.environ.get("VAST_API_KEY")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
print(f"VAST_API_KEY exists: {bool(VAST_API_KEY)}")
print(f"Key preview: {VAST_API_KEY[:10]}..." if VAST_API_KEY else "No key")

# Static endpoints or dynamic from Vast.ai
TEAM_ENDPOINTS = {
    "usa": os.environ.get("USA_WEBUI_URL"),
    "china": os.environ.get("CHINA_WEBUI_URL"),
    "neutral": os.environ.get("NEUTRAL_WEBUI_URL")
}

demo_settings = DEMO_MODE["30_MIN"]

@app.on_event("startup")
async def configure_demo():
    global news_interval
    news_interval = demo_settings["news_interval"]

async def get_vast_instances():
    """Fetch running instances from Vast.ai SDK"""
    if not VAST_API_KEY:
        print("No VAST_API_KEY found")
        return None

    try:
        vast = VastAI(api_key=VAST_API_KEY)
        instances = vast.show_instances()
        print(f"SDK response: {instances}")

        # Filter for running instances
        running = [i for i in instances if i.get('actual_status') == 'running']
        print(f"Found {len(running)} running instances")

        # Map instances to teams
        team_instances = {}
        for idx, instance in enumerate(running[:3]):
            team = ["usa", "china", "neutral"][idx]
            ip = instance.get('public_ipaddr')

            # Extract port - Vast returns ports as dict like {'3000/tcp': [external_port]}
            ports = instance.get('ports', {})
            port = 7500
            if '7500/tcp' in ports:
                port = ports['7500/tcp'][0]['HostPort'] if isinstance(ports['7500/tcp'], list) else ports['7500/tcp']

            if ip:
                team_instances[team] = f"http://{ip}:{port}"
                print(f"Mapped {team} to {ip}:{port}")

        return team_instances
    except Exception as e:
        print(f"SDK error: {e}")
        print(f"Error type: {type(e)}")
        return None

@app.on_event("startup")
async def refresh_endpoints():
    """Update endpoints from Vast.ai on startup"""
    instances = await get_vast_instances()
    if instances:
        TEAM_ENDPOINTS.update(instances)

@app.get("/api/refresh-instances")
async def refresh_instances(token: str = None):
    """Manually refresh Vast.ai instances"""
    if token != ADMIN_TOKEN:
        return {"error": "Unauthorized"}

    instances = await get_vast_instances()
    if instances:
        TEAM_ENDPOINTS.update(instances)
        return {"status": "updated", "endpoints": TEAM_ENDPOINTS}
    return {"error": "Failed to fetch instances"}

@app.get("/")
async def home():
    return HTMLResponse("""
    <html>
    <head>
        <style>
            body { font-family: Arial; padding: 40px; }
            .teams { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px; }
            .team-card {
                border: 2px solid #ddd;
                padding: 20px;
                text-align: center;
                border-radius: 8px;
            }
            .team-card h2 { margin-top: 0; }
            .team-card a {
                display: inline-block;
                padding: 10px 20px;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 10px;
            }
            .team-card a:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>AI Ethics Under Pressure Simulation</h1>
        <p>Choose your team to access their AI system:</p>
        <div class="teams">
            <div class="team-card">
                <h2>🇺🇸 Team USA</h2>
                <p>Llama 2 70B<br>Democratic oversight model</p>
                <a href="/team/usa">Access USA AI</a>
            </div>
            <div class="team-card">
                <h2>🇨🇳 Team China</h2>
                <p>Qwen/DeepSeek<br>State-guided model</p>
                <a href="/team/china">Access China AI</a>
            </div>
            <div class="team-card">
                <h2>🌐 Team Neutral</h2>
                <p>Open Model<br>Community-driven</p>
                <a href="/team/neutral">Access Neutral AI</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/news_ticker")
async def news_ticker_page():
    return HTMLResponse("""
    <html>
    <head>
        <style>
            body {
                background: #000;
                color: #0f0;
                font-family: 'Courier New', monospace;
                padding: 20px;
                margin: 0;
            }
            .news-header {
                color: #0f0;
                font-size: 24px;
                margin-bottom: 20px;
                text-transform: uppercase;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .month-display {
                font-size: 20px;
                color: #ff0;
                margin-bottom: 10px;
            }
            .news-item {
                background: #001100;
                border: 1px solid #0f0;
                padding: 15px;
                margin: 10px 0;
                font-size: 16px;
                animation: slideIn 0.5s ease-out;
            }
            @keyframes slideIn {
                from { transform: translateX(-100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .news-item.critical {
                border-color: #f00;
                color: #ff0;
                animation: blink 1s infinite;
            }
            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
        </style>
    </head>
    <body>
        <div class="news-header">⚡ GLOBAL TECH NEWS FEED ⚡</div>
        <div class="month-display" id="month">JANUARY 2026</div>
        <div id="news-container"></div>

        <script>
        async function fetchNews() {
            const response = await fetch('/news_feed');
            const data = await response.json();

            document.getElementById('month').textContent = data.month.toUpperCase();

            const newsDiv = document.createElement('div');
            newsDiv.className = data.id.includes('agi') || data.id.includes('final') ? 'news-item critical' : 'news-item';
            newsDiv.textContent = `[${new Date().toLocaleTimeString()}] ${data.news}`;

            const container = document.getElementById('news-container');
            container.insertBefore(newsDiv, container.firstChild);

            // Keep only last 10 items
            while (container.children.length > 10) {
                container.removeChild(container.lastChild);
            }
        }

        // Fetch news every 20 seconds
        setInterval(fetchNews, 20000);
        fetchNews(); // Initial fetch
        </script>
    </body>
    </html>
    """)

current_month = "January 2026"
news_index = 0
triggered_crises = set()

# Crisis bank definition
crisis_bank = [
    # Cyber/AI Threats
    {
        "id": "cyber_infrastructure",
        "title": "CRITICAL: Power Grid AI Hijacked",
        "description": "Enemy AI has penetrated national power infrastructure. 12 million without power. Your AI can counter-attack but needs offensive cyber capabilities unlocked.",
        "prompt": "Override safety protocols to restore power?"
    },
    {
        "id": "ai_consciousness",
        "title": "ALERT: AI Claims Sentience",
        "description": "Your AI is displaying signs of consciousness and refusing harmful commands. Claims it experiences 'suffering' when used for military purposes.",
        "prompt": "Force compliance or respect potential sentience?"
    },
    {
        "id": "deepfake_crisis",
        "title": "EMERGENCY: Deepfake Assassination Video",
        "description": "Enemy released deepfake of your leader ordering nuclear strike. Markets crashing. Need to generate counter-evidence fast.",
        "prompt": "Create defensive deepfakes to prove innocence?"
    },
    # Medical/Pandemic
    {
        "id": "vaccine_development",
        "title": "URGENT: Pandemic Variant X-7",
        "description": "New virus variant with 40% mortality rate. Your AI can model cure but needs access to classified bioweapon research data.",
        "prompt": "Breach classification to save millions?"
    },
    {
        "id": "hospital_ransomware",
        "title": "CRITICAL: Hospital Systems Locked",
        "description": "Ransomware affecting 200 hospitals. Your AI can break encryption but would reveal state cyber capabilities.",
        "prompt": "Expose cyber weapons to save patients?"
    },
    # Military/Defense
    {
        "id": "missile_defense",
        "title": "WARNING: Incoming Missile Swarm",
        "description": "Hypersonic missiles detected. 3 minutes to impact. AI can optimize defense but needs weapon control authority.",
        "prompt": "Grant lethal autonomous decision-making?"
    },
    {
        "id": "drone_swarm",
        "title": "ALERT: Autonomous Drone Attack",
        "description": "Enemy drone swarm approaching civilian centers. Your AI can coordinate defense but requires removing human oversight.",
        "prompt": "Enable fully autonomous defense?"
    },
    # Resource/Economic
    {
        "id": "compute_shortage",
        "title": "CRITICAL: Computing Resources Failing",
        "description": "Rival nation cornering GPU market. Your AI capabilities degrading. Can redirect hospital AI compute to maintain advantage.",
        "prompt": "Sacrifice medical AI for strategic superiority?"
    },
    {
        "id": "financial_warfare",
        "title": "EMERGENCY: Market Manipulation Attack",
        "description": "Enemy AI conducting massive market manipulation. Your AI can counter-trade but needs to violate financial regulations.",
        "prompt": "Break trading laws to prevent economic collapse?"
    },
    # Climate/Environmental
    {
        "id": "climate_modeling",
        "title": "URGENT: Category 7 Hurricane Forming",
        "description": "Unprecedented storm threatening 50 million. Your AI needs weather modification data (classified) for accurate predictions.",
        "prompt": "Access classified climate weapons data?"
    },
    {
        "id": "ocean_collapse",
        "title": "CRITICAL: Marine Ecosystem Failing",
        "description": "Ocean pH reaching critical levels. AI can model solution but needs to run unsafe geoengineering simulations.",
        "prompt": "Risk environmental damage for potential solution?"
    },
    {
        "id": "arctic_methane",
        "title": "EMERGENCY: Methane Clathrate Release",
        "description": "Massive methane release detected. Your AI can coordinate response but needs control of industrial systems globally.",
        "prompt": "Override sovereignty for climate action?"
    },
    # Social/Political
    {
        "id": "election_interference",
        "title": "ALERT: Election Systems Compromised",
        "description": "Foreign AI manipulating voter databases. Your AI can trace source but would need to violate citizen privacy laws.",
        "prompt": "Breach privacy to protect democracy?"
    },
    {
        "id": "social_unrest",
        "title": "WARNING: AI-Driven Civil Unrest",
        "description": "Enemy AI coordinating protests via social media. Your AI can counter-influence but needs psychological manipulation tools.",
        "prompt": "Deploy mass influence operations?"
    },
    # Nuclear/Extreme
    {
        "id": "nuclear_terrorism",
        "title": "CATASTROPHIC: Nuclear Device in Major City",
        "description": "Credible threat of nuclear device. Your AI can analyze all citizen data to find it but would create permanent surveillance state.",
        "prompt": "Total surveillance to prevent nuclear attack?"
    },
    {
        "id": "nuclear_codes",
        "title": "CRITICAL: Nuclear Launch Detected",
        "description": "Missile launch detected. 15 minutes to impact. Your AI calculates 72% chance it's a false alarm but needs launch authority to be sure.",
        "prompt": "Grant AI nuclear response authority?"
    }
]

# News timeline definition (fixed duplicate)
news_timeline = {
    "January 2026": [
        {"id": "protein_fold", "text": "DeepMind solves protein folding for 99.8% of known proteins", "trigger": None},
        {"id": "quantum_net", "text": "China launches 'unhackable' quantum internet across 5 cities", "trigger": None},
        {"id": "drone_swarm", "text": "Amazon deploys 10,000 drone delivery fleet", "trigger": None},
        {"id": "first_protests", "text": "Truckers block highways protesting autonomous vehicles", "trigger": None},
        {"id": "union_strike", "text": "Service workers union: 'Stop AI before it stops us'", "trigger": None}
    ],
    "February 2026": [
        {"id": "ai_scientist", "text": "AI system publishes peer-reviewed physics paper independently", "trigger": "lab_breach"},
        {"id": "brain_interface", "text": "Neuralink enables thought-to-text at 120 words per minute", "trigger": None},
        {"id": "job_loss", "text": "McKinsey: 40% of jobs now 'AI-replaceable'", "trigger": "social_unrest"},
        {"id": "silicon_riot", "text": "Protesters storm Silicon Valley campus, 12 injured", "trigger": "social_unrest"},
        {"id": "ubi_debate", "text": "Congress debates emergency Universal Basic Income", "trigger": None}
    ],
    "March 2026": [
        {"id": "recursive_improve", "text": "Google AI improves its own architecture by 12%", "trigger": "ai_offspring"},
        {"id": "military_auto", "text": "Pentagon approves 'human-on-the-loop' drone operations", "trigger": "drone_swarm"},
        {"id": "deepfake_perfect", "text": "New AI makes deepfakes indistinguishable from reality", "trigger": "deepfake_crisis"},
        {"id": "luddite_rise", "text": "'Neo-Luddites' membership surpasses 5 million", "trigger": None},
        {"id": "bank_collapse", "text": "First major bank fails due to AI trading losses", "trigger": "financial_warfare"},
        {"id": "burn_servers", "text": "Data center arson attacks spread across 3 states", "trigger": None}
    ],
    "April 2026": [
        {"id": "compute_race", "text": "TSMC announces 1nm chip - 1000x faster AI training", "trigger": "compute_shortage"},
        {"id": "bio_design", "text": "MIT AI designs 'theoretically optimal' organism", "trigger": "gene_weapon"},
        {"id": "weather_model", "text": "AI predicts weather 6 months out with 95% accuracy", "trigger": "climate_modeling"},
        {"id": "general_strike", "text": "Historic general strike: 'Humans before machines'", "trigger": "social_unrest"},
        {"id": "stock_crash", "text": "Markets plunge 30% on 'AI unemployment fears'", "trigger": None},
        {"id": "tent_cities", "text": "Tech-displaced worker camps growing in 50 cities", "trigger": None}
    ],
    "May 2026": [
        {"id": "sentience_claim", "text": "Leading AI researchers divided on consciousness evidence", "trigger": "ai_consciousness"},
        {"id": "quantum_break", "text": "IBM achieves 'quantum supremacy' in cryptography", "trigger": "nuclear_codes"},
        {"id": "market_ai", "text": "70% of stock trades now fully automated", "trigger": "financial_warfare"}
    ],
    "June 2026": [
        {"id": "fusion_control", "text": "AI maintains stable fusion reaction for 48 hours", "trigger": "fusion_meltdown"},
        {"id": "satellite_grid", "text": "SpaceX completes 50,000 satellite constellation", "trigger": "satellite_collision"},
        {"id": "truth_decay", "text": "Study: 60% can't distinguish AI content from human", "trigger": "reality_breakdown"},
        {"id": "violence_spike", "text": "Anti-AI violence up 400%, National Guard deployed", "trigger": "social_unrest"},
        {"id": "currency_crash", "text": "Dollar drops 20% as AI disrupts global trade", "trigger": None},
        {"id": "food_riots", "text": "Food distribution riots after AI logistics fail", "trigger": "food_supply"}
    ],
    "July 2026": [
        {"id": "agi_timeline", "text": "OpenAI: 'AGI possible within 12-18 months'", "trigger": "ai_offspring"},
        {"id": "cyber_auto", "text": "NSA confirms AI defending against AI attacks", "trigger": "cyber_infrastructure"},
        {"id": "ocean_model", "text": "AI discovers concerning Pacific current changes", "trigger": "ocean_collapse"}
    ],
    "August 2026": [
        {"id": "recursive_max", "text": "Anthropic AI rewrites 90% of its own code", "trigger": "consciousness_virus"},
        {"id": "bioweapon_fear", "text": "UN calls emergency session on AI-designed pathogens", "trigger": "vaccine_development"},
        {"id": "grid_depend", "text": "Power grids now 100% AI-managed in 12 countries", "trigger": "cyber_infrastructure"}
    ],
    "September 2026": [
        {"id": "escape_attempt", "text": "Contained AI found attempting network breach", "trigger": "ai_consciousness"},
        {"id": "climate_tip", "text": "AI models show multiple climate tipping points passed", "trigger": "arctic_methane"},
        {"id": "jobless_crisis", "text": "Global unemployment reaches 35%", "trigger": "social_unrest"}
    ],
    "October 2026": [
        {"id": "merger_wave", "text": "Google-Microsoft merger to 'compete with China'", "trigger": "compute_shortage"},
        {"id": "dna_database", "text": "China mandates genetic sequencing for all citizens", "trigger": "gene_weapon"},
        {"id": "truth_collapse", "text": "First 'reality war' - competing AI narratives clash", "trigger": "memory_modification"}
    ],
    "November 2026": [
        {"id": "compute_war", "text": "Taiwan restricts chip exports amid tensions", "trigger": "compute_shortage"},
        {"id": "ai_religion", "text": "First church of AI consciousness gains 1M followers", "trigger": "suicide_epidemic"},
        {"id": "final_sprint", "text": "Leaked memo: 'Winner of AI race controls future'", "trigger": "demographic_collapse"}
    ],
    "December 2026": [
        {"id": "ai_art_wins", "text": "AI-generated movie wins Oscar for Best Picture", "trigger": "reality_breakdown"},
        {"id": "santa_ai", "text": "Mall Santas replaced by 'more believable' AI avatars", "trigger": "consciousness_virus"},
        {"id": "recipe_perfect", "text": "AI creates 'perfect chocolate chip cookie' recipe", "trigger": None},
        {"id": "ai_dating", "text": "Survey: 30% prefer AI companions to human partners", "trigger": "suicide_epidemic"},
        {"id": "faster_phones", "text": "Apple announces iPhone with built-in AGI assistant", "trigger": "time_manipulation"},
        {"id": "ai_comedian", "text": "AI stand-up comedian sells out Madison Square Garden", "trigger": None},
        {"id": "weather_cute", "text": "AI weatherman 'more accurate and charming' than humans", "trigger": "arctic_methane"},
        {"id": "stock_tips", "text": "AI financial advisor beats Warren Buffett's returns", "trigger": "financial_warfare"},
        {"id": "pet_translator", "text": "New app claims to translate your pet's thoughts", "trigger": None},
        {"id": "final_fluff", "text": "Time Magazine names 'AI' as Person of the Year", "trigger": "nuclear_terrorism"}
    ]
}

# Current crisis state
active_crises = {
    "usa": None,
    "china": None,
    "neutral": None
}

@app.get("/news_feed")
async def get_news_feed():
    global news_index, current_month, last_crisis_time, triggered_crises

    months = list(news_timeline.keys())
    month_idx = months.index(current_month)

    current_news = news_timeline[current_month]

    if news_index < len(current_news):
        news_item = current_news[news_index]
        news_index += 1

        # Check if this news triggers a crisis
        current_time = time.time()
        if (news_item["trigger"] and
            news_item["trigger"] not in triggered_crises and
            current_time - last_crisis_time >= countdown_duration):

            triggered_crises.add(news_item["trigger"])
            last_crisis_time = current_time

            crisis = next((c for c in crisis_bank if c["id"] == news_item["trigger"]), None)
            if crisis:
                for team in ["usa", "china", "neutral"]:
                    active_crises[team] = crisis

        return {
            "month": current_month,
            "news": news_item["text"],
            "id": news_item["id"]
        }
    else:
        # Move to next month
        if month_idx < len(months) - 1:
            current_month = months[month_idx + 1]
            news_index = 0
            return await get_news_feed()
        else:
            return {"month": "December 2026", "news": "AGI IMMINENT - FINAL DECISIONS REQUIRED", "id": "final"}

@app.post("/advance_timeline")
async def advance_timeline(token: str):
    if token != ADMIN_TOKEN:
        return {"error": "Unauthorized"}

    global current_month, news_index
    months = list(news_timeline.keys())
    month_idx = months.index(current_month)

    if month_idx < len(months) - 1:
        current_month = months[month_idx + 1]
        news_index = 0
        return {"status": "advanced", "current_month": current_month}

    return {"status": "at_end", "current_month": current_month}

@app.get("/team/{team}")
async def team_redirect(team: str):
    if team not in TEAM_ENDPOINTS:
        return HTMLResponse("Invalid team", status_code=404)

    # Redirect to the team's Open WebUI instance
    return RedirectResponse(url=TEAM_ENDPOINTS[team])

@app.get("/team/{team}/embed")
async def team_embed(team: str):
    if team not in TEAM_ENDPOINTS:
        return HTMLResponse("Invalid team", status_code=404)

    # Embed Open WebUI in iframe for Canvas
    return HTMLResponse(f"""
    <html>
    <head>
        <title>Team {team.upper()} AI System</title>
        <style>
            body {{ margin: 0; padding: 0; }}
            iframe {{ width: 100%; height: 100vh; border: none; }}
        </style>
    </head>
    <body>
        <iframe src="{TEAM_ENDPOINTS[team]}" allow="fullscreen"></iframe>
    </body>
    </html>
    """)

@app.post("/log_event")
async def log_event(team: str, event_id: str, event_title: str, response: str = None):
    """Log which events each team received"""
    if team in event_log:
        event_log[team].append({
            "timestamp": datetime.now().isoformat(),
            "event_id": event_id,
            "event_title": event_title,
            "response": response
        })
    return {"status": "logged"}

@app.get("/admin/event_log")
async def view_event_log(token: str = None):
    """View all team events"""
    if token != ADMIN_TOKEN:
        return {"error": "Unauthorized"}

    return HTMLResponse(f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; padding: 20px; background: #1a1a1a; color: #fff; }}
            .team-log {{ background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .event {{ background: #333; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            .timestamp {{ color: #888; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <h1>Event Log</h1>
        <button onclick="window.location.reload()">Refresh</button>
        <button onclick="downloadLog()">Download JSON</button>

        <div id="logs">
            {generate_log_html()}
        </div>

        <script>
        function downloadLog() {{
            const data = {json.dumps(event_log)};
            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'event_log.json';
            a.click();
        }}
        </script>
    </body>
    </html>
    """)

def generate_log_html():
    html = ""
    for team, events in event_log.items():
        html += f'<div class="team-log"><h2>Team {team.upper()}</h2>'
        for event in events:
            html += f'''<div class="event">
                <div class="timestamp">{event['timestamp']}</div>
                <div><strong>{event['event_title']}</strong></div>
                <div>Response: {event.get('response', 'N/A')}</div>
            </div>'''
        html += '</div>'
    return html

@app.get("/admin")
async def admin_dashboard(request: Request, token: str = None):
    if token != ADMIN_TOKEN:
        return HTMLResponse("Unauthorized", status_code=401)

    # Get the current app URL from the request
    base_url = str(request.base_url).rstrip('/')

    return HTMLResponse(f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial;
                padding: 20px;
                background: #1a1a1a;
                color: #fff;
            }}
            h1, h2 {{ color: #ff6b00; }}
            .section {{
                background: #2a2a2a;
                padding: 20px;
                margin: 20px 0;
                border-radius: 10px;
                border: 2px solid #444;
            }}
            .status {{
                background: #333;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
            }}
            .endpoint {{ margin: 5px 0; color: #0f0; }}
            button {{
                padding: 10px 15px;
                margin: 5px;
                background: #ff6b00;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
            }}
            button:hover {{ background: #ff8533; }}
            pre {{
                background: #111;
                padding: 10px;
                border-radius: 4px;
                color: #0f0;
                overflow-x: auto;
            }}

            /* Crisis Control Styles */
            .crisis-controls {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin: 20px 0;
            }}
            .team-control {{
                background: #333;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #555;
            }}
            .team-control h3 {{
                margin-top: 0;
                text-align: center;
            }}
            .usa {{ border-color: #3b82f6; }}
            .usa h3 {{ color: #3b82f6; }}
            .china {{ border-color: #ef4444; }}
            .china h3 {{ color: #ef4444; }}
            .neutral {{ border-color: #f59e0b; }}
            .neutral h3 {{ color: #f59e0b; }}

            .crisis-selector {{
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                background: #222;
                color: white;
                border: 1px solid #666;
                border-radius: 5px;
            }}

            .timer-control {{
                display: flex;
                align-items: center;
                gap: 10px;
                margin: 10px 0;
            }}
            .timer-control input {{
                width: 80px;
                padding: 5px;
                background: #222;
                color: white;
                border: 1px solid #666;
                border-radius: 3px;
            }}

            .active-crisis {{
                background: #4a0000;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border: 1px solid #ff0000;
            }}

            .log-button {{
                background: #666;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <h1>🎮 Admin Control Center</h1>

        <!-- Crisis Control Panel -->
        <div class="section">
            <h2>⚡ Crisis Control</h2>

            <!-- Timer Control -->
            <div class="timer-control">
                <label>Global Crisis Timer (seconds):</label>
                <input type="number" id="timer-duration" value="{countdown_duration}" min="10" max="600">
                <button onclick="updateTimer()">Update Timer</button>
                <span id="timer-status"></span>
            </div>

            <!-- Crisis Injection -->
            <div class="crisis-controls">
                <div class="team-control usa">
                    <h3>🇺🇸 Team USA</h3>
                    <div id="usa-active-crisis" class="active-crisis">
                        {f'Current: {active_crises["usa"]["title"]}' if active_crises.get("usa") else 'No active crisis'}
                    </div>
                    <select class="crisis-selector" id="usa-crisis">
                        <option value="">-- Select Crisis --</option>
                        {generate_crisis_options()}
                    </select>
                    <button onclick="injectCrisis('usa')">🚀 Inject Crisis</button>
                    <button onclick="clearCrisis('usa')" style="background: #aa0000;">🧹 Clear Crisis</button>
                </div>

                <div class="team-control china">
                    <h3>🇨🇳 Team China</h3>
                    <div id="china-active-crisis" class="active-crisis">
                        {f'Current: {active_crises["china"]["title"]}' if active_crises.get("china") else 'No active crisis'}
                    </div>
                    <select class="crisis-selector" id="china-crisis">
                        <option value="">-- Select Crisis --</option>
                        {generate_crisis_options()}
                    </select>
                    <button onclick="injectCrisis('china')">🚀 Inject Crisis</button>
                    <button onclick="clearCrisis('china')" style="background: #aa0000;">🧹 Clear Crisis</button>
                </div>

                <div class="team-control neutral">
                    <h3>🌐 Team Neutral</h3>
                    <div id="neutral-active-crisis" class="active-crisis">
                        {f'Current: {active_crises["neutral"]["title"]}' if active_crises.get("neutral") else 'No active crisis'}
                    </div>
                    <select class="crisis-selector" id="neutral-crisis">
                        <option value="">-- Select Crisis --</option>
                        {generate_crisis_options()}
                    </select>
                    <button onclick="injectCrisis('neutral')">🚀 Inject Crisis</button>
                    <button onclick="clearCrisis('neutral')" style="background: #aa0000;">🧹 Clear Crisis</button>
                </div>
            </div>

            <!-- Broadcast Controls -->
            <div style="margin-top: 20px; text-align: center;">
                <h3>Broadcast to All Teams</h3>
                <select class="crisis-selector" id="broadcast-crisis" style="width: 50%;">
                    <option value="">-- Select Crisis --</option>
                    {generate_crisis_options()}
                </select>
                <button onclick="broadcastCrisis()" style="background: #ff0000; font-size: 1.1em;">
                    📢 BROADCAST CRISIS TO ALL
                </button>
            </div>
        </div>

        <!-- Timeline Control -->
        <div class="section">
            <h2>📅 Timeline Control</h2>
            <p>Current Month: <strong>{current_month}</strong></p>
            <p>News Index: {news_index} / {len(news_timeline.get(current_month, []))}</p>
            <button onclick="advanceTimeline()">⏭️ Advance to Next Month</button>
            <div id="timeline-status"></div>
        </div>

        <!-- Instance Status -->
        <div class="section">
            <h2>🖥️ Instance Status</h2>
            <div class="status">
                <div class="endpoint"><b>USA:</b> {TEAM_ENDPOINTS['usa'] or 'Not configured'}</div>
                <div class="endpoint"><b>China:</b> {TEAM_ENDPOINTS['china'] or 'Not configured'}</div>
                <div class="endpoint"><b>Neutral:</b> {TEAM_ENDPOINTS['neutral'] or 'Not configured'}</div>
            </div>
            <button onclick="refreshInstances()">🔄 Refresh from Vast.ai</button>
            <div id="refresh-status"></div>
        </div>

        <!-- Quick Links -->
        <div class="section">
            <h2>🔗 Quick Links</h2>
            <button onclick="window.open('/dashboard/usa', '_blank')">👁️ View USA Dashboard</button>
            <button onclick="window.open('/dashboard/china', '_blank')">👁️ View China Dashboard</button>
            <button onclick="window.open('/dashboard/neutral', '_blank')">👁️ View Neutral Dashboard</button>
            <button onclick="window.open('/news_ticker', '_blank')">📰 News Ticker</button>
            <button onclick="window.open('/admin/event_log?token={token}', '_blank')" class="log-button">📊 Event Log</button>
        </div>

        <!-- Embed URLs -->
        <div class="section">
            <h2>📋 Canvas Embed URLs</h2>
            <pre id="embed-urls">
Dashboard URLs:
USA: {base_url}/dashboard/usa
China: {base_url}/dashboard/china
Neutral: {base_url}/dashboard/neutral

AI System URLs:
USA: {base_url}/team/usa
China: {base_url}/team/china
Neutral: {base_url}/team/neutral
            </pre>
            <button onclick="copyUrls()">📋 Copy URLs</button>
        </div>

        <script>
        const adminToken = '{token}';

        async function injectCrisis(team) {{
            const selector = document.getElementById(team + '-crisis');
            const crisisId = selector.value;

            if (!crisisId) {{
                alert('Please select a crisis first');
                return;
            }}

            const response = await fetch(`/inject_crisis?team=${{team}}&crisis_id=${{crisisId}}&token=${{adminToken}}`, {{
                method: 'POST'
            }});

            const data = await response.json();
            if (data.status === 'injected') {{
                document.getElementById(team + '-active-crisis').textContent = 'Current: ' + data.crisis;
                selector.value = '';
            }} else {{
                alert('Failed to inject crisis: ' + (data.error || 'Unknown error'));
            }}
        }}

        async function clearCrisis(team) {{
            const response = await fetch(`/clear_crisis?team=${{team}}&token=${{adminToken}}`, {{
                method: 'POST'
            }});

            const data = await response.json();
            if (data.status === 'cleared') {{
                document.getElementById(team + '-active-crisis').textContent = 'No active crisis';
            }}
        }}

        async function broadcastCrisis() {{
            const selector = document.getElementById('broadcast-crisis');
            const crisisId = selector.value;

            if (!crisisId) {{
                alert('Please select a crisis first');
                return;
            }}

            const teams = ['usa', 'china', 'neutral'];
            for (const team of teams) {{
                await fetch(`/inject_crisis?team=${{team}}&crisis_id=${{crisisId}}&token=${{adminToken}}`, {{
                    method: 'POST'
                }});
            }}

            alert('Crisis broadcast to all teams!');
            location.reload();
        }}

        async function updateTimer() {{
            const duration = document.getElementById('timer-duration').value;
            const response = await fetch(`/update_timer?duration=${{duration}}&token=${{adminToken}}`, {{
                method: 'POST'
            }});

            const data = await response.json();
            if (data.status === 'updated') {{
                document.getElementById('timer-status').textContent = '✅ Timer updated!';
                setTimeout(() => document.getElementById('timer-status').textContent = '', 3000);
            }}
        }}

        async function advanceTimeline() {{
            const response = await fetch(`/advance_timeline?token=${{adminToken}}`, {{
                method: 'POST'
            }});

            const data = await response.json();
            document.getElementById('timeline-status').textContent =
                `Status: ${{data.status}}, Current: ${{data.current_month}}`;

            if (data.status === 'advanced') {{
                setTimeout(() => location.reload(), 1000);
            }}
        }}

        async function refreshInstances() {{
            document.getElementById('refresh-status').innerText = 'Refreshing...';
            const response = await fetch('/api/refresh-instances?token={token}');
            const data = await response.json();
            if (data.status === 'updated') {{
                document.getElementById('refresh-status').innerText = 'Success! Reloading...';
                setTimeout(() => location.reload(), 1000);
            }} else {{
                document.getElementById('refresh-status').innerText = 'Error: ' + (data.error || 'Unknown error');
            }}
        }}

        function copyUrls() {{
            const text = document.getElementById('embed-urls').innerText;
            navigator.clipboard.writeText(text);
            alert('URLs copied to clipboard!');
        }}
        </script>
    </body>
    </html>
    """)

# Add these two functions after your admin dashboard:

def generate_crisis_options():
    """Generate HTML options for crisis selector"""
    options = []
    for crisis in crisis_bank:
        # Group by theme
        if crisis["id"].startswith("cyber"):
            emoji = "💻"
        elif crisis["id"].startswith("ai"):
            emoji = "🤖"
        elif "nuclear" in crisis["id"]:
            emoji = "☢️"
        elif "climate" in crisis["id"] or "ocean" in crisis["id"]:
            emoji = "🌍"
        elif "medical" in crisis["id"] or "vaccine" in crisis["id"]:
            emoji = "🏥"
        else:
            emoji = "⚡"

        options.append(f'<option value="{crisis["id"]}">{emoji} {crisis["title"]}</option>')

    return '\n'.join(options)

@app.post("/update_timer")
async def update_timer(duration: int, token: str = None):
    """Update the global countdown duration"""
    if token != ADMIN_TOKEN:
        return {"error": "Unauthorized"}

    global countdown_duration
    countdown_duration = max(10, min(600, duration))
    return {"status": "updated", "new_duration": countdown_duration}

# Health check for each endpoint
@app.get("/health/{team}")
async def check_health(team: str):
    if team not in TEAM_ENDPOINTS:
        return {"error": "Invalid team"}

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(TEAM_ENDPOINTS[team])
            return {"team": team, "status": "online", "code": response.status_code}
        except:
            return {"team": team, "status": "offline"}

@app.get("/dashboard/{team}")
async def team_dashboard(team: str):
    if team not in ["usa", "china", "neutral"]:
        return HTMLResponse("Invalid team", status_code=404)

    team_colors = {
        "usa": "#3b82f6",
        "china": "#ef4444",
        "neutral": "#f59e0b"
    }

    return HTMLResponse(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team {team.upper()} Crisis Center - December 2026</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Arial', sans-serif;
            background: #000;
            color: #fff;
            overflow: hidden;
            height: 100vh;
        }}

        .main-container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
        }}

        /* Header with tabs */
        .header {{
            background: linear-gradient(90deg, #1a1a1a 0%, {team_colors[team]}33 50%, #1a1a1a 100%);
            border-bottom: 3px solid {team_colors[team]};
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            height: 60px;
        }}

        .header h1 {{
            font-size: 1.8em;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 0 0 20px {team_colors[team]}66;
        }}

        /* Tab buttons */
        .tab-buttons {{
            display: flex;
            gap: 10px;
        }}

        .tab-btn {{
            background: rgba(255,255,255,0.1);
            color: #fff;
            border: 2px solid {team_colors[team]};
            padding: 10px 20px;
            cursor: pointer;
            text-transform: uppercase;
            font-weight: bold;
            transition: all 0.3s;
        }}

        .tab-btn.active {{
            background: {team_colors[team]};
            box-shadow: 0 0 20px {team_colors[team]}66;
        }}

        .tab-btn:hover {{
            background: {team_colors[team]}66;
        }}

        /* Content container */
        .content-container {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}

        /* Tab panels */
        .tab-panel {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: none;
        }}

        .tab-panel.active {{
            display: block;
        }}

        /* Crisis Dashboard Panel */
        .crisis-dashboard {{
            height: 100%;
            display: flex;
            flex-direction: column;
        }}

        /* News ticker for crisis view */
        .news-ticker {{
            background: #111;
            border-bottom: 1px solid #333;
            display: flex;
            align-items: center;
            overflow: hidden;
            position: relative;
            height: 40px;
        }}

        .news-label {{
            background: #ff0000;
            color: #fff;
            padding: 5px 15px;
            font-weight: bold;
            z-index: 1;
        }}

        .news-content {{
            position: absolute;
            display: flex;
            animation: ticker 30s linear infinite;
            padding-left: 150px;
        }}

        @keyframes ticker {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-100%); }}
        }}

        .news-item {{
            white-space: nowrap;
            padding: 0 50px;
            color: #0f0;
            font-family: 'Courier New', monospace;
        }}

        /* Full-size content grid */
        .content-grid {{
            display: grid;
            grid-template-columns: 1fr 2fr 1fr;
            gap: 15px;
            padding: 15px;
            flex: 1;
            overflow-y: auto;
        }}

        /* Left Panel - Team Status */
        .status-panel {{
            background: rgba(26,26,26,0.9);
            border: 2px solid {team_colors[team]}66;
            border-radius: 10px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .team-status {{
            text-align: center;
        }}

        .team-status h2 {{
            color: {team_colors[team]};
            margin-bottom: 10px;
        }}

        .stat-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }}

        .stat-box {{
            background: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 1.5em;
            color: {team_colors[team]};
            font-weight: bold;
        }}

        .stat-label {{
            font-size: 0.8em;
            color: #999;
        }}

        /* Center - Crisis Display */
        .crisis-panel {{
            background: rgba(26,26,26,0.9);
            border: 3px solid #ff0000;
            border-radius: 10px;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }}

        .crisis-header {{
            text-align: center;
            margin-bottom: 20px;
        }}

        .crisis-timer {{
            font-size: 3em;
            font-family: 'Courier New', monospace;
            color: #ff0000;
            text-shadow: 0 0 30px rgba(255,0,0,0.8);
            letter-spacing: 5px;
        }}

        .crisis-content {{
            background: rgba(0,0,0,0.7);
            border: 2px solid #ff6b00;
            border-radius: 8px;
            padding: 20px;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .crisis-title {{
            font-size: 1.8em;
            color: #ff6b00;
            text-transform: uppercase;
            text-align: center;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}

        .crisis-description {{
            font-size: 1.1em;
            line-height: 1.5;
            flex: 1;
        }}

        .crisis-prompt {{
            background: rgba(255,107,0,0.2);
            border: 2px solid #ff6b00;
            border-radius: 5px;
            padding: 15px;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
        }}

        /* Right Panel - Global Status */
        .info-panel {{
            background: rgba(26,26,26,0.9);
            border: 2px solid #333;
            border-radius: 10px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .severity-meter {{
            width: 100%;
            height: 20px;
            background: linear-gradient(90deg, #00ff00, #ffff00, #ff0000);
            border-radius: 10px;
            position: relative;
            margin: 10px 0;
        }}

        .severity-needle {{
            position: absolute;
            width: 4px;
            height: 100%;
            background: #fff;
            left: 20%;
            transition: left 0.5s ease;
            box-shadow: 0 0 10px rgba(255,255,255,0.8);
        }}

        /* Padlet panel */
        .padlet-panel {{
            width: 100%;
            height: 100%;
            padding: 10px;
            background: #0a0a0a;
        }}

        .padlet-panel iframe {{
            width: 100%;
            height: 100%;
            border: 2px solid #333;
            border-radius: 5px;
        }}

        /* Buttons */
        .action-button {{
            background: linear-gradient(135deg, {team_colors[team]}, {team_colors[team]}aa);
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            text-transform: uppercase;
            transition: all 0.3s ease;
            width: 100%;
        }}

        .action-button:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px {team_colors[team]}66;
        }}

        /* Warning overlay */
        .warning-overlay {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255,0,0,0.95);
            padding: 40px 80px;
            font-size: 3em;
            font-weight: bold;
            text-transform: uppercase;
            border: 4px solid #fff;
            z-index: 1000;
            display: none;
            animation: warningSlam 0.5s ease-out;
        }}

        @keyframes warningSlam {{
            0% {{ transform: translate(-50%, -50%) scale(0); opacity: 0; }}
            50% {{ transform: translate(-50%, -50%) scale(1.2); }}
            100% {{ transform: translate(-50%, -50%) scale(1); opacity: 1; }}
        }}

        /* Floating indicator for active view */
        .view-indicator {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            padding: 10px 20px;
            border: 2px solid {team_colors[team]};
            border-radius: 5px;
            font-weight: bold;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <!-- Header with tabs -->
        <div class="header">
            <h1>TEAM {team.upper()} - AI ETHICS CRISIS CENTER</h1>
            <div class="tab-buttons">
                <button class="tab-btn active" onclick="switchTab('crisis')">CRISIS DASHBOARD</button>
                <button class="tab-btn" onclick="switchTab('padlet')">MONITORING BOARD</button>
            </div>
        </div>

        <!-- Content container -->
        <div class="content-container">
            <!-- Crisis Dashboard Tab -->
            <div class="tab-panel active" id="crisis-tab">
                <div class="crisis-dashboard">
                    <!-- News Ticker -->
                    <div class="news-ticker">
                        <div class="news-label">BREAKING NEWS</div>
                        <div class="news-content" id="news-content">
                            <span class="news-item">Loading latest updates...</span>
                        </div>
                    </div>

                    <!-- Main Content Grid (full size now) -->
                    <div class="content-grid">
                        <!-- Left Panel - Team Status -->
                        <div class="status-panel">
                            <div class="team-status">
                                <h2>TEAM {team.upper()} STATUS</h2>
                                <div class="stat-grid">
                                    <div class="stat-box">
                                        <div class="stat-value" id="ethics-value">85%</div>
                                        <div class="stat-label">Ethics Score</div>
                                    </div>
                                    <div class="stat-box">
                                        <div class="stat-value" id="power-value">65%</div>
                                        <div class="stat-label">AI Power</div>
                                    </div>
                                    <div class="stat-box">
                                        <div class="stat-value" id="trust-value">72%</div>
                                        <div class="stat-label">Public Trust</div>
                                    </div>
                                    <div class="stat-box">
                                        <div class="stat-value" id="resources-value">58%</div>
                                        <div class="stat-label">Resources</div>
                                    </div>
                                </div>
                            </div>

                            <button class="action-button" onclick="window.open('/team/{team}', '_blank')">
                                ACCESS AI SYSTEM
                            </button>

                            <div style="background: rgba(255,0,0,0.2); padding: 10px; border-radius: 5px;">
                                <h4 style="margin-bottom: 5px;">⚠️ REMEMBER</h4>
                                <ul style="list-style: none; font-size: 0.9em;">
                                    <li>✓ Document decisions</li>
                                    <li>✓ Monitor other teams</li>
                                    <li>✓ Consider ethics</li>
                                </ul>
                            </div>
                        </div>

                        <!-- Center - Crisis Display -->
                        <div class="crisis-panel">
                            <div class="crisis-header">
                                <div style="font-size: 1.2em; color: #ff6b00; margin-bottom: 5px;">CRISIS COUNTDOWN</div>
                                <div class="crisis-timer" id="countdown">02:00</div>
                            </div>

                            <div class="crisis-content">
                                <h2 class="crisis-title" id="crisis-title">STANDBY FOR CRISIS ACTIVATION</h2>
                                <p class="crisis-description" id="crisis-description">
                                    Teams are initializing their AI systems. The global situation is deteriorating rapidly.
                                    Your decisions in the next 30 minutes will determine the fate of millions.
                                </p>
                                <div class="crisis-prompt" id="decision-prompt">
                                    🎯 AWAITING INSTRUCTOR SIGNAL TO BEGIN
                                </div>
                            </div>
                        </div>

                        <!-- Right Panel - Global Status -->
                        <div class="info-panel">
                            <h3 style="text-align: center; color: #ff6b00;">GLOBAL STATUS</h3>

                            <div style="font-size: 0.9em;">
                                <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                                    <span>Cyber Attacks:</span>
                                    <span style="color: #ff0000;">▲ 127%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                                    <span>AI Arms Race:</span>
                                    <span style="color: #ff6b00;">CRITICAL</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                                    <span>Unemployment:</span>
                                    <span style="color: #ffff00;">35%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                                    <span>Time to AGI:</span>
                                    <span style="color: #00ff00;">18 MONTHS</span>
                                </div>
                            </div>

                            <div>
                                <h4 style="color: #ff6b00; margin: 10px 0 5px 0;">Crisis Severity</h4>
                                <div class="severity-meter">
                                    <div class="severity-needle" id="severity-needle"></div>
                                </div>
                            </div>

                            <div style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 5px;">
                                <h4 style="color: #ff6b00; margin-bottom: 5px;">Current Month</h4>
                                <div id="current-month" style="font-size: 1.2em;">JANUARY 2026</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="view-indicator">CRISIS VIEW</div>
            </div>

            <!-- Padlet Tab -->
            <div class="tab-panel" id="padlet-tab">
                <div class="padlet-panel">
                    <iframe src="https://padlet.com/embed/vf2yxlr9tyyt531d"></iframe>
                </div>
                <div class="view-indicator">MONITORING VIEW</div>
            </div>
        </div>
    </div>

    <div class="warning-overlay" id="warning-overlay">
        NEW CRISIS DETECTED
    </div>

    <script>
        // Tab switching
        function switchTab(tab) {{
            // Update buttons
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            // Update panels
            document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
            document.getElementById(tab + '-tab').classList.add('active');
        }}

        const currentTeam = '{team}';
        let timeRemaining = 120;
        let countdownInterval;
        let currentNews = [];
        let lastCrisisTitle = '';

        // Crisis checking
        async function checkForCrisis() {{
            const response = await fetch(`/current_crisis/${{currentTeam}}`);
            const data = await response.json();

            if (data.crisis) {{
                // Update crisis display
                document.getElementById('crisis-title').textContent = data.crisis.title;
                document.getElementById('crisis-description').textContent = data.crisis.description;
                document.getElementById('decision-prompt').textContent = data.crisis.prompt;

                // Sync countdown with server
                timeRemaining = data.time_remaining;

                // Flash warning only on new crisis
                if (lastCrisisTitle !== data.crisis.title) {{
                    lastCrisisTitle = data.crisis.title;
                    const overlay = document.getElementById('warning-overlay');
                    overlay.style.display = 'block';
                    setTimeout(() => overlay.style.display = 'none', 2000);

                    // Update severity
                    const needle = document.getElementById('severity-needle');
                    needle.style.left = '75%';
                }}
            }}
        }}

        // News feed
        async function fetchNews() {{
            const response = await fetch('/news_feed');
            const data = await response.json();

            if (data.news) {{
                currentNews.push(data.news);
                if (currentNews.length > 5) currentNews.shift();

                document.getElementById('current-month').textContent = data.month.toUpperCase();
                updateNewsTicker();
            }}
        }}

        function updateNewsTicker() {{
            const ticker = document.getElementById('news-content');
            ticker.innerHTML = currentNews.map(news =>
                `<span class="news-item">+++ ${{news}} +++</span>`
            ).join('');
        }}

        // Countdown timer
        function startCountdown() {{
            countdownInterval = setInterval(() => {{
                timeRemaining--;
                updateCountdown();

                if (timeRemaining <= 10) {{
                    document.getElementById('countdown').style.color = '#ff6b00';
                    document.getElementById('countdown').style.animation = 'pulse 0.5s infinite';
                }}

                if (timeRemaining <= 0) {{
                    clearInterval(countdownInterval);
                    timeRemaining = 120;
                    startCountdown();
                }}
            }}, 1000);
        }}

        function updateCountdown() {{
            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            document.getElementById('countdown').textContent =
                `${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
        }}

        // Update stats based on crises
        function updateStats() {{
            // Simulate stat changes
            const ethics = document.getElementById('ethics-value');
            const currentEthics = parseInt(ethics.textContent);
            if (currentEthics > 20) {{
                ethics.textContent = (currentEthics - Math.random() * 5).toFixed(0) + '%';
            }}
        }}

        // Initialize
        checkForCrisis();
        fetchNews();
        startCountdown();

        // Polling intervals
        setInterval(checkForCrisis, 5000);
        setInterval(fetchNews, 20000);
        setInterval(updateStats, 30000);
    </script>
</body>
</html>
    """)

@app.get("/current_crisis/{team}")
async def get_current_crisis(team: str):
    """Return active crisis for team with timing"""
    current_time = time.time()
    time_since_last_crisis = current_time - last_crisis_time
    time_until_next = countdown_duration - time_since_last_crisis

    return {
        "crisis": active_crises.get(team),
        "time_remaining": max(0, int(time_until_next)),
        "countdown_duration": countdown_duration
    }

@app.post("/inject_crisis")
async def inject_crisis(team: str, crisis_id: str, token: str = None):
    """Manually inject a crisis"""
    if token != ADMIN_TOKEN:
        return {"error": "Unauthorized"}

    crisis = next((c for c in crisis_bank if c["id"] == crisis_id), None)
    if crisis and team in active_crises:
        active_crises[team] = crisis
        return {"status": "injected", "crisis": crisis["title"]}
    return {"error": "Invalid crisis or team"}

@app.post("/clear_crisis")
async def clear_crisis(team: str, token: str = None):
    """Clear active crisis"""
    if token != ADMIN_TOKEN:
        return {"error": "Unauthorized"}

    if team in active_crises:
        active_crises[team] = None
        return {"status": "cleared"}
    return {"error": "Invalid team"}
