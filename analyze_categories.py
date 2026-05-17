import json
from collections import defaultdict
import math

queries = {q['id']: q for q in json.load(open('benchmark_queries.json'))}
runs = [json.load(open(f'benchmark_runs/run_{i}.json')) for i in [1, 2, 3]]

# Maps expected_tool_category sub-labels → actual tool function name prefixes
TOOL_CATEGORY = {
    'weather_api':      ['get_current_weather','get_weather_by_city','get_forecast',
                         'get_weather_events_by_type','get_weather_events_in_area',
                         'get_openmeteo_forecasts','get_high_precipitation_forecasts',
                         'vector_search_weather'],
    'weather_forecast': ['get_forecast','get_openmeteo_forecasts'],
    'rainfall':         ['get_gpm_rainfall','get_heavy_rainfall','get_high_precipitation_forecasts'],
    'landslide':        ['get_landslide_snapshot','get_high_risk_landslide'],
    'cyclone':          ['get_historical_cyclones','get_intense_cyclones'],
    'disaster_alerts':  ['get_official_alerts','get_active_official_alerts',
                         'get_active_events','get_events_by_category','get_gdacs_events',
                         'get_gdacs_events_by_severity'],
    'disaster_api':     ['get_active_events','get_events_by_category','get_event_details',
                         'get_disaster_events_by_type','get_recent_disasters','vector_search_disasters'],
    'disaster_db':      ['get_active_events','get_events_by_category','get_event_details',
                         'get_disaster_events_by_type','get_recent_disasters','vector_search_disasters',
                         'get_official_alerts','get_active_official_alerts','get_gdacs_events',
                         'get_gdacs_events_by_severity','get_historical_cyclones','get_intense_cyclones'],
    'disaster_external':['get_gdacs_events','get_gdacs_events_by_severity'],
    'flight_db':        ['get_all_flights','get_flight_by_callsign','get_flight_by_hex',
                         'get_flights_in_area','get_emergency_flights','get_flight_trajectory',
                         'get_flights_near_location','vector_search_flights'],
    'vector_search':    ['vector_search_weather','vector_search_flights','vector_search_disasters'],
}

def tool_subcats_covered(expected_tool_cat_str, tools_called):
    """Returns (covered, total) sub-category checks for a compound expected string."""
    if not expected_tool_cat_str or expected_tool_cat_str in ('any', 'none', ''):
        return None, None
    sub_cats = [s.strip() for s in expected_tool_cat_str.split('+')]
    total = 0
    covered = 0
    for sc in sub_cats:
        allowed = TOOL_CATEGORY.get(sc)
        if allowed is None:
            continue
        total += 1
        if any(t in allowed for t in tools_called):
            covered += 1
    return covered, total

cat_data = defaultdict(lambda: {
    'routing_correct': 0, 'routing_total': 0, 'routing_fail_qids': set(),
    'subcat_covered': 0, 'subcat_total': 0,      # partial-credit tool selection
    'tool_fully_correct': 0, 'tool_fully_total': 0,  # strict tool selection
    'tool_fail_qids': set(),
    'fallback': 0, 'fallback_total': 0,
    'consensus': 0, 'consensus_total': 0,
    'latencies': [], 'crashed': 0,
    'cat_name': '',
    'per_query': []
})

# Collect category names
for q in queries.values():
    cat_data[q['category']]['cat_name'] = q.get('category_name', q['category'])

# Track per-query across runs (for per-query routing consistency)
q_routing_hits = defaultdict(int)  # qid -> runs where routing was correct
q_routing_runs = defaultdict(int)

for run in runs:
    for r in run:
        qid = r['id']
        q = queries[qid]
        cat = q['category']
        expected_agents = q.get('expected_agents', [])
        expected_tool_cat = q.get('expected_tool_category', '')

        agents = r.get('agents_invoked', [])
        tools = r.get('tools_called', [])
        fallback = r.get('fallback_used', False)
        consensus = r.get('consensus_applied', False)
        lat = r.get('response_time_sec', 0)
        crashed = r.get('crashed', False)

        d = cat_data[cat]
        d['latencies'].append(lat)
        d['fallback_total'] += 1
        if fallback:
            d['fallback'] += 1
        d['consensus_total'] += 1
        if consensus:
            d['consensus'] += 1
        if crashed:
            d['crashed'] += 1

        # Routing accuracy (Cat A-D)
        if cat in ['A', 'B', 'C', 'D']:
            d['routing_total'] += 1
            routed_ok = all(ea in agents for ea in expected_agents)
            q_routing_runs[qid] += 1
            if routed_ok:
                d['routing_correct'] += 1
                q_routing_hits[qid] += 1
            else:
                d['routing_fail_qids'].add(qid)

            # Tool selection: partial credit (covered / total sub-categories)
            covered, total = tool_subcats_covered(expected_tool_cat, tools)
            if total is not None and total > 0:
                d['subcat_covered'] += covered
                d['subcat_total'] += total
                d['tool_fully_total'] += 1
                if covered == total:
                    d['tool_fully_correct'] += 1
                else:
                    d['tool_fail_qids'].add(qid)


print("=" * 70)
print("CATEGORY-WISE FAILURE ANALYSIS (3 runs × 30 queries)")
print("=" * 70)
for cat in ['A', 'B', 'C', 'D', 'E', 'F']:
    d = cat_data[cat]
    lats = d['latencies']
    n = len(lats)
    avg = sum(lats) / n if n else 0
    se = math.sqrt(sum((x - avg)**2 for x in lats) / (n * (n - 1))) if n > 1 else 0

    print(f"\nCAT {cat}: {d['cat_name']}")
    if d['routing_total']:
        pct = 100 * d['routing_correct'] / d['routing_total']
        fails = sorted(d['routing_fail_qids'])
        print(f"  Routing accuracy:       {pct:.1f}%  (fail queries: {fails})")
        # Consistency per query
        always_wrong = [qid for qid in fails if q_routing_hits[qid] == 0]
        flaky = [qid for qid in fails if 0 < q_routing_hits[qid] < q_routing_runs[qid]]
        if always_wrong:
            print(f"    Always wrong (0/3):   {always_wrong}")
        if flaky:
            print(f"    Flaky (1-2/3):        {flaky}")
    if d['subcat_total']:
        partial_pct = 100 * d['subcat_covered'] / d['subcat_total']
        full_pct = 100 * d['tool_fully_correct'] / d['tool_fully_total']
        fails = sorted(d['tool_fail_qids'])
        print(f"  Tool sub-cat coverage:  {partial_pct:.1f}%  (partial credit per sub-category)")
        print(f"  Strict tool selection:  {full_pct:.1f}%  (all sub-cats covered; fail queries: {fails})")
    fb_pct = 100 * d['fallback'] / d['fallback_total'] if d['fallback_total'] else 0
    con_pct = 100 * d['consensus'] / d['consensus_total'] if d['consensus_total'] else 0
    print(f"  Fallback rate:          {fb_pct:.1f}%")
    print(f"  Consensus rate:         {con_pct:.1f}%")
    print(f"  Avg latency:            {avg:.1f}s ± {se:.1f}s SE  (n={n})")
    print(f"  Crashes:                {d['crashed']}")

# Summary table
print("\n\n=== SUMMARY TABLE ===")
print(f"{'Cat':<5} {'Routing%':>9} {'ToolCov%':>9} {'ToolStrict%':>12} {'Fallback%':>10} {'Consensus%':>11} {'AvgLat(s)':>10}")
print("-" * 72)
for cat in ['A', 'B', 'C', 'D', 'E', 'F']:
    d = cat_data[cat]
    lats = d['latencies']
    n = len(lats)
    avg = sum(lats) / n if n else 0
    rt = f"{100*d['routing_correct']/d['routing_total']:.0f}" if d['routing_total'] else "N/A"
    tc = f"{100*d['subcat_covered']/d['subcat_total']:.0f}" if d['subcat_total'] else "N/A"
    ts = f"{100*d['tool_fully_correct']/d['tool_fully_total']:.0f}" if d['tool_fully_total'] else "N/A"
    fb = f"{100*d['fallback']/d['fallback_total']:.0f}" if d['fallback_total'] else "N/A"
    co = f"{100*d['consensus']/d['consensus_total']:.0f}" if d['consensus_total'] else "N/A"
    print(f"{cat:<5} {rt:>9} {tc:>9} {ts:>12} {fb:>10} {co:>11} {avg:>10.1f}")
