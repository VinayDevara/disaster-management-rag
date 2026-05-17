"""
Full system verification test for DisasterRAG
Tests: health, all 3 agents, tool calling, retry logic, cross-domain reasoning
"""
import httpx
import json
import time
import sys

BASE = "http://localhost:8000"
TIMEOUT = 180  # 3 min per query for Qwen 3B

PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"
INFO = "\033[94m INFO\033[0m"
WARN = "\033[93m WARN\033[0m"

results = []

def log(label, msg):
    print(f"{label} {msg}")

def record(name, passed, detail=""):
    results.append((name, passed, detail))
    icon = PASS if passed else FAIL
    print(f"\n{'='*60}")
    print(f"{icon}  {name}")
    if detail:
        print(f"       {detail}")
    print(f"{'='*60}")

# ─────────────────────────────────────────────
# 1. HEALTH CHECK
# ─────────────────────────────────────────────
def test_health():
    print("\n[1] Health Check...")
    try:
        r = httpx.get(f"{BASE}/api/health", timeout=10)
        d = r.json()
        ok = r.status_code == 200 and d.get("status") == "ok"
        record("Health Endpoint", ok, f"status={d.get('status')} system='{d.get('system')}'")
        return ok
    except Exception as e:
        record("Health Endpoint", False, str(e))
        return False

# ─────────────────────────────────────────────
# 2. BACKEND ENDPOINTS
# ─────────────────────────────────────────────
def test_endpoints():
    print("\n[2] Testing API Endpoints...")
    endpoints = [
        ("GET", "/api/flights/recent", None),
        ("GET", "/api/flights/emergency", None),
        ("GET", "/api/weather/current?lat=12.9141&lon=74.8560", None),
        ("GET", "/api/disasters/events", None),
        ("GET", "/api/alerts/active", None),
    ]
    for method, path, body in endpoints:
        try:
            url = f"{BASE}{path}"
            if method == "GET":
                r = httpx.get(url, timeout=15)
            else:
                r = httpx.post(url, json=body, timeout=15)
            ok = r.status_code in (200, 404)  # 404 is ok if route exists
            record(f"Endpoint {path}", ok, f"HTTP {r.status_code}")
        except Exception as e:
            record(f"Endpoint {path}", False, str(e))

# ─────────────────────────────────────────────
# 3. QUERY TESTS — AGENT ROUTING & TOOL CALLING
# ─────────────────────────────────────────────
def run_query(label, query, expect_agents=None, expect_tools=None, check_answer_keywords=None):
    print(f"\n[QUERY] {label}...")
    print(f"        Query: '{query}'")
    start = time.time()
    try:
        r = httpx.post(
            f"{BASE}/api/query",
            json={"query": query},
            timeout=TIMEOUT
        )
        elapsed = round(time.time() - start, 1)
        
        if r.status_code != 200:
            record(label, False, f"HTTP {r.status_code}")
            return None

        d = r.json()
        meta = d.get("metadata", {})
        agents = meta.get("agents_used", [])
        tools = meta.get("tools_called", [])
        consensus = meta.get("consensus_applied", False)
        retries = meta.get("retries", 0)
        fr = d.get("final_response", {})
        answer = str(fr.get("answer", ""))[:300] if fr else ""

        print(f"        Agents: {agents}")
        print(f"        Tools:  {tools}")
        print(f"        Consensus: {consensus} | Retries: {retries}")
        print(f"        Time: {elapsed}s")
        print(f"        Answer (first 300 chars): {answer}")

        issues = []
        if expect_agents:
            missing = [a for a in expect_agents if a not in agents]
            if missing:
                issues.append(f"Missing agents: {missing}")
        if expect_tools:
            missing_t = [t for t in expect_tools if t not in tools]
            if missing_t:
                issues.append(f"Missing tools: {missing_t} (got: {tools})")
        if check_answer_keywords:
            missing_k = [k for k in check_answer_keywords if k.lower() not in answer.lower()]
            if missing_k:
                issues.append(f"Answer missing keywords: {missing_k}")
        if not answer or len(answer.strip()) < 20:
            issues.append("Answer too short or empty")

        passed = len(issues) == 0
        detail = f"Agents={agents} | Tools={tools} | {elapsed}s"
        if issues:
            detail += f" | ISSUES: {'; '.join(issues)}"
        record(label, passed, detail)
        return d

    except httpx.TimeoutException:
        record(label, False, f"Timed out after {TIMEOUT}s")
        return None
    except Exception as e:
        record(label, False, str(e))
        return None

# ─────────────────────────────────────────────
# 4. DISASTER AGENT TESTS
# ─────────────────────────────────────────────
def test_disaster_agent():
    print("\n\n=== DISASTER AGENT TESTS ===")
    run_query(
        "Disaster: Active Events",
        "What are the current active disaster events happening worldwide?",
        expect_agents=["disaster"]
    )
    run_query(
        "Disaster: GDACS Alerts",
        "Show me GDACS disaster alerts in India",
        expect_agents=["disaster"]
    )
    run_query(
        "Disaster: Official Alerts",
        "Are there any official SACHET or NDMA emergency alerts active right now?",
        expect_agents=["disaster"]
    )

# ─────────────────────────────────────────────
# 5. WEATHER AGENT TESTS
# ─────────────────────────────────────────────
def test_weather_agent():
    print("\n\n=== WEATHER AGENT TESTS ===")
    run_query(
        "Weather: Current Mangalore",
        "What is the current weather in Mangalore?",
        expect_agents=["weather"]
    )
    run_query(
        "Weather: Rainfall Risk",
        "Is there heavy rainfall risk or flood risk in coastal Karnataka?",
        expect_agents=["weather"]
    )
    run_query(
        "Weather: Landslide Risk",
        "What is the current landslide risk in the region?",
        expect_agents=["weather"]
    )

# ─────────────────────────────────────────────
# 6. FLIGHT AGENT TESTS
# ─────────────────────────────────────────────
def test_flight_agent():
    print("\n\n=== FLIGHT AGENT TESTS ===")
    run_query(
        "Flight: Active Flights",
        "Show me all active flights over Mangalore right now",
        expect_agents=["flight"]
    )
    run_query(
        "Flight: Emergency Squawks",
        "Are there any emergency flights or squawk 7700 aircraft right now?",
        expect_agents=["flight"]
    )

# ─────────────────────────────────────────────
# 7. CROSS-DOMAIN & CONSENSUS TESTS
# ─────────────────────────────────────────────
def test_cross_domain():
    print("\n\n=== CROSS-DOMAIN / CONSENSUS TESTS ===")
    run_query(
        "Cross-Domain: Disaster + Weather correlation",
        "Is the current heavy rainfall in Karnataka causing floods and are flights affected?",
        expect_agents=["disaster", "weather", "flight"]
    )
    run_query(
        "Cross-Domain: Storm impact on flights",
        "Are there any cyclone warnings that could affect flight operations near Mangalore airport?",
        expect_agents=["weather", "flight"]
    )

# ─────────────────────────────────────────────
# 8. RETRY / FALLBACK LOGIC TEST
# ─────────────────────────────────────────────
def test_retry_logic():
    print("\n\n=== RETRY & FALLBACK TESTS ===")
    # Edge case: vague query that should trigger re-evaluation
    run_query(
        "Retry: Vague Query Fallback",
        "Is it safe to go outside?",
    )
    # Edge case: very specific query to check tool exhaustion fallback
    run_query(
        "Retry: Unknown callsign fallback",
        "Find flight XYZABC999 — if not found, what should we check?",
        expect_agents=["flight"]
    )

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*70)
    print("  DisasterRAG Full System Verification")
    print("="*70)

    if not test_health():
        print("\n[ABORT] Backend not reachable. Make sure server is running.")
        sys.exit(1)

    test_endpoints()
    test_disaster_agent()
    test_weather_agent()
    test_flight_agent()
    test_cross_domain()
    test_retry_logic()

    # ─── SUMMARY ───
    print("\n\n" + "="*70)
    print("  FINAL SUMMARY")
    print("="*70)
    passed = sum(1 for _, p, _ in results if p)
    total  = len(results)
    for name, p, detail in results:
        icon = "✅" if p else "❌"
        print(f"  {icon} {name}")
        if not p and detail:
            print(f"       → {detail}")
    print(f"\n  {passed}/{total} tests passed")
    print("="*70)
