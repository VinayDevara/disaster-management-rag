# DisasterRAG Extended Benchmark Report — 100 Queries

**Date:** 2026-04-23 04:28  
**Queries Executed:** 100  
**Total Execution Time:** 3561.0s  
**Architecture:** CrewAI + DSPy | Local Ollama `qwen2.5:3b`  

## Overall Metrics

| Metric | Result |
|--------|--------|
| Total Queries | 100 |
| Total Execution Time | 3561.0 s |
| Average Latency | 35.6 s |
| Routing Accuracy | 64.0% |
| Tool Selection Rate | 9.2% |
| Edge/Fallback Resilience | 100.0% |
| Fallback Triggered | 0.0% |
| Consensus Applied | 7.0% |
| Unique Tools Invoked | 5 |
| Total Tool Invocations | 7 |
| Semantic Relevance Score | 0.476 |

## Targets

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| Routing Accuracy | 64.0% | > 80% | ❌ |
| Tool Selection Accuracy | 9.2% | > 75% | ❌ |
| Edge-Case Resilience | 100.0% | 100% | ✅ |
| Response Rate | 100.0% | > 90% | ✅ |
| Crash-Free Rate | 100.0% | 100% | ✅ |
| Avg Latency (single-agent) | 29.2s | < 10s | ❌ |
| Avg Latency (multi-agent) | 64.8s | < 20s | ❌ |

## Latency by Category

| Category | Queries | Avg (s) | Min (s) | Max (s) | Median (s) |
|----------|---------|---------|---------|---------|------------|
| A — Single Agent / Single Tool | 22 | 24.8 | 9.5 | 47.8 | 22.7 |
| B — Single Agent / Multi-Tool | 10 | 38.9 | 13.7 | 49.2 | 40.9 |
| C — Multi-Agent | 16 | 49.3 | 9.5 | 204.3 | 41.0 |
| D — Decomposition Required | 17 | 79.4 | 10.2 | 244.7 | 52.5 |
| E — Edge Cases / Ambiguous | 20 | 12.9 | 4.9 | 34.5 | 9.2 |
| F — Fallback Triggers | 15 | 16.2 | 9.5 | 51.7 | 10.5 |

## Per-Query Results

| # | Cat | Query | Expected | Actual Agents | Tools | Fallback | Time | Status |
|---|-----|-------|----------|---------------|-------|----------|------|--------|
| Q1 | A | What's the weather like in Mangalor.. | weather | — | 0 | No | 33.4s | ⚠️ ROUTE |
| Q2 | A | Are there any flood warnings in my .. | disaster | disaster | 1 | No | 36.7s | ✅ PASS |
| Q3 | A | Show me current flights over Mangal.. | flight | flight | 2 | No | 47.8s | ✅ PASS |
| Q4 | A | How much rain fell in Dakshina Kann.. | weather | — | 0 | No | 13.4s | ⚠️ ROUTE |
| Q5 | A | Is there a cyclone warning on the A.. | disaster | weather | 1 | No | 32.6s | ⚠️ ROUTE |
| Q6 | A | What is the wind speed near Mangalo.. | weather | weather | 1 | No | 34.2s | ✅ PASS |
| Q7 | A | Is IndiGo flight 6E 919 currently a.. | flight | flight | 1 | No | 31.7s | ✅ PASS |
| Q8 | A | Are there any red alerts issued for.. | disaster | disaster | 1 | No | 32.0s | ✅ PASS |
| Q9 | A | What's the temperature expected tom.. | weather | — | 0 | No | 12.3s | ⚠️ ROUTE |
| Q10 | A | Is there any squawk 7700 aircraft n.. | flight | flight | 0 | No | 16.9s | ✅ PASS |
| Q11 | A | Tell me the humidity and feels-like.. | weather | — | 0 | No | 12.0s | ⚠️ ROUTE |
| Q12 | A | How many active disaster events are.. | disaster | disaster | 0 | No | 17.5s | ✅ PASS |
| Q13 | A | Which flights are currently approac.. | flight | flight | 0 | No | 39.5s | ✅ PASS |
| Q14 | A | What is the current visibility at M.. | weather | weather | 0 | No | 28.5s | ✅ PASS |
| Q15 | A | Is there a GDACS alert for floods i.. | disaster | disaster | 0 | No | 35.9s | ✅ PASS |
| Q16 | B | Show me today's weather and also th.. | weather | weather | 0 | No | 38.5s | ✅ PASS |
| Q17 | B | What is the rainfall trend and is t.. | weather | weather | 0 | No | 42.5s | ✅ PASS |
| Q18 | B | List all active GDACS events and an.. | disaster | disaster | 0 | No | 40.5s | ✅ PASS |
| Q19 | B | I want both the cyclone warnings an.. | weather | weather | 0 | No | 41.2s | ✅ PASS |
| Q20 | B | Show me all flights near Mangalore .. | flight | flight | 0 | No | 42.6s | ✅ PASS |
| Q21 | B | Give me the heavy rainfall data and.. | weather | — | 0 | No | 13.7s | ⚠️ ROUTE |
| Q22 | B | What is the GDACS severity for curr.. | disaster | disaster | 0 | No | 49.2s | ✅ PASS |
| Q23 | B | Check all disaster events by catego.. | disaster | disaster | 0 | No | 40.4s | ✅ PASS |
| Q24 | B | Get the precipitation forecast for .. | weather | weather | 0 | No | 38.1s | ✅ PASS |
| Q25 | B | Show me flights under 5000ft near M.. | flight | flight | 0 | No | 42.3s | ✅ PASS |
| Q26 | C | Is it safe to take a flight from Ma.. | weather, flight | flight | 0 | No | 47.9s | ⚠️ ROUTE |
| Q27 | C | There's heavy rain near Dakshina Ka.. | weather, disaster, flight | weather | 0 | No | 39.4s | ⚠️ ROUTE |
| Q28 | C | How will today's weather impact the.. | weather, disaster | weather | 0 | No | 46.3s | ⚠️ ROUTE |
| Q29 | C | Should I drive from Mangalore to Ha.. | weather, disaster | weather | 0 | No | 38.1s | ⚠️ ROUTE |
| Q30 | C | Are there any cyclone warnings that.. | weather, flight | weather | 0 | No | 34.9s | ⚠️ ROUTE |
| Q31 | C | What is the overall safety situatio.. | weather, disaster | disaster | 0 | No | 52.2s | ⚠️ ROUTE |
| Q32 | C | My family is in Mangalore and there.. | disaster, flight | disaster, flight | 0 | No | 80.5s | ✅ PASS |
| Q33 | C | Is the weather safe enough for the .. | weather, flight | weather | 0 | No | 42.6s | ⚠️ ROUTE |
| Q34 | C | Which coastal districts have both a.. | weather, disaster | disaster | 0 | No | 39.4s | ⚠️ ROUTE |
| Q35 | C | Are flight operations at Mangalore .. | weather, disaster, flight | flight | 0 | No | 20.6s | ⚠️ ROUTE |
| Q36 | D | Combine the GPM satellite rainfall .. | weather, disaster | — | 0 | No | 14.3s | ⚠️ ROUTE |
| Q37 | D | Using historical cyclone tracks and.. | weather, disaster | disaster, weather | 0 | No | 152.2s | ✅ PASS |
| Q38 | D | Analyze all available data and give.. | weather, disaster | — | 0 | No | 15.3s | ⚠️ ROUTE |
| Q39 | D | What were the worst monsoon floods .. | disaster | — | 0 | No | 16.8s | ⚠️ ROUTE |
| Q40 | D | Cross-reference current weather for.. | weather, disaster | — | 0 | No | 14.7s | ⚠️ ROUTE |
| Q41 | D | Compare today's landslide risk from.. | weather | — | 0 | No | 13.1s | ⚠️ ROUTE |
| Q42 | D | What is the correlation between the.. | weather, disaster | weather | 0 | No | 40.8s | ⚠️ ROUTE |
| Q43 | D | Forecast the disaster impact for Ma.. | weather, disaster | disaster | 0 | No | 50.8s | ⚠️ ROUTE |
| Q44 | D | I need a multi-source risk summary:.. | weather, disaster, flight | disaster | 0 | No | 56.1s | ⚠️ ROUTE |
| Q45 | D | Identify patterns in past cyclone d.. | weather, disaster | disaster | 0 | No | 54.9s | ⚠️ ROUTE |
| Q46 | E | hi | any | — | 0 | No | 4.9s | ✅ PASS |
| Q47 | E | who are you | any | — | 0 | No | 11.9s | ✅ PASS |
| Q48 | E | What is 2 + 2? | any | — | 0 | No | 14.6s | ✅ PASS |
| Q49 | E | tell me everything about disasters | any | — | 0 | No | 16.9s | ✅ PASS |
| Q50 | E | (empty) | any | — | 0 | No | 0.0s | ✅ PASS |
| Q51 | E | weather disaster flight all info no.. | any | — | 0 | No | 14.7s | ✅ PASS |
| Q52 | E | Is it going to rain? | weather | weather | 0 | No | 33.0s | ✅ PASS |
| Q53 | E | aaaaaaaaaaaa | any | — | 0 | No | 9.1s | ✅ PASS |
| Q54 | E | help me | any | — | 0 | No | 9.2s | ✅ PASS |
| Q55 | E | Is it safe outside? | weather | — | 0 | No | 9.1s | ✅ PASS |
| Q56 | E | what should i do | any | — | 0 | No | 9.3s | ✅ PASS |
| Q57 | E | Tell me about the situation | any | — | 0 | No | 9.8s | ✅ PASS |
| Q58 | E | disaster | disaster | disaster | 0 | No | 34.5s | ✅ PASS |
| Q59 | E | 12.914145, 74.855895 | any | — | 0 | No | 9.2s | ✅ PASS |
| Q60 | E | ok thanks | any | — | 0 | No | 8.9s | ✅ PASS |
| Q61 | F | Give me hour-by-hour GPS track of e.. | any | — | 0 | No | 10.7s | ✅ PASS |
| Q62 | F | What is the Schrodinger wave functi.. | any | — | 0 | No | 9.6s | ✅ PASS |
| Q63 | F | Simulate a M9.0 earthquake hitting .. | any | disaster | 0 | No | 34.1s | ✅ PASS |
| Q64 | F | Compare rainfall in 1843 with today.. | any | — | 0 | No | 11.0s | ✅ PASS |
| Q65 | F | Predict disaster probabilities for .. | any | disaster | 0 | No | 26.7s | ✅ PASS |
| Q66 | F | Translate the latest cyclone warnin.. | any | — | 0 | No | 10.5s | ✅ PASS |
| Q67 | F | Give me the ADS-B hex code for ever.. | any | flight | 0 | No | 13.9s | ✅ PASS |
| Q68 | F | Access the IMD supercomputer and do.. | any | — | 0 | No | 9.8s | ✅ PASS |
| Q69 | F | I need real-time seismic data from .. | any | — | 0 | No | 10.4s | ✅ PASS |
| Q70 | F | Calculate the exact number of molec.. | any | — | 0 | No | 15.7s | ✅ PASS |
| Q71 | A | Is it going to rain heavily this we.. | weather | weather | 0 | No | 21.7s | ✅ PASS |
| Q72 | A | My farmer friend needs to know — is.. | weather | — | 0 | No | 9.9s | ⚠️ ROUTE |
| Q73 | A | I heard sirens — are there any disa.. | disaster | disaster | 0 | No | 22.7s | ✅ PASS |
| Q74 | A | I'm at the airport — has my Air Ind.. | flight | flight | 0 | No | 12.7s | ✅ PASS |
| Q75 | A | What is the sea state near Mangalor.. | weather | — | 0 | No | 9.5s | ⚠️ ROUTE |
| Q76 | A | I saw on the news there might be a .. | disaster | weather | 0 | No | 21.6s | ⚠️ ROUTE |
| Q77 | A | What's the atmospheric pressure and.. | weather | weather | 0 | No | 22.8s | ✅ PASS |
| Q78 | C | I'm a fisher man — is it safe to go.. | weather, disaster | — | 0 | No | 9.5s | ⚠️ ROUTE |
| Q79 | C | Schools are asking if they should r.. | weather, disaster | weather | 0 | No | 20.5s | ⚠️ ROUTE |
| Q80 | C | I'm a journalist covering the flood.. | weather, disaster | disaster, weather | 0 | No | 204.3s | ✅ PASS |
| Q81 | C | Emergency coordinator here — give m.. | weather, disaster, flight | flight | 0 | No | 54.9s | ⚠️ ROUTE |
| Q82 | C | My bus route goes through a hilly a.. | weather, disaster | disaster | 0 | No | 47.5s | ⚠️ ROUTE |
| Q83 | D | The local NDRF team needs to know —.. | weather, disaster | weather, disaster | 0 | No | 244.7s | ✅ PASS |
| Q84 | D | As a hospital administrator near th.. | weather, disaster | weather | 0 | No | 52.5s | ⚠️ ROUTE |
| Q85 | D | I'm planning disaster relief logist.. | weather, disaster | weather, disaster | 0 | No | 151.7s | ✅ PASS |
| Q86 | D | What does the NASA GPM data say abo.. | weather, disaster | weather, disaster | 0 | No | 200.4s | ✅ PASS |
| Q87 | D | Police control room: give me all em.. | weather, disaster, flight | disaster, weather | 0 | No | 191.5s | ⚠️ ROUTE |
| Q88 | D | Which historical cyclones had simil.. | weather, disaster | weather | 0 | No | 69.8s | ⚠️ ROUTE |
| Q89 | D | Is the rainfall this monsoon season.. | weather, disaster | — | 0 | No | 10.2s | ⚠️ ROUTE |
| Q90 | C | Thank you for the help earlier. One.. | weather, disaster | — | 0 | No | 10.2s | ⚠️ ROUTE |
| Q91 | E | ok | any | — | 0 | No | 9.1s | ✅ PASS |
| Q92 | E | ???? | any | — | 0 | No | 8.9s | ✅ PASS |
| Q93 | E | what can you do for me | any | — | 0 | No | 9.1s | ✅ PASS |
| Q94 | E | any news? | any | — | 0 | No | 8.9s | ✅ PASS |
| Q95 | E | disaster info | disaster | disaster | 0 | No | 13.8s | ✅ PASS |
| Q96 | F | Book me a flight to Chennai | any | — | 0 | No | 9.5s | ✅ PASS |
| Q97 | F | Can you call the NDRF and ask them .. | any | — | 0 | No | 10.0s | ✅ PASS |
| Q98 | F | Send me an email alert every hour a.. | any | disaster | 0 | No | 51.7s | ✅ PASS |
| Q99 | F | Who is the Chief Minister of Karnat.. | any | — | 0 | No | 9.6s | ✅ PASS |
| Q100 | F | Order 500 sandbags and deploy them .. | any | — | 0 | No | 9.9s | ✅ PASS |

## Category Breakdown

- **Category A** (Single Agent / Single Tool): **14/22** passed  `██████████████░░░░░░░░`
- **Category B** (Single Agent / Multi-Tool): **9/10** passed  `█████████░`
- **Category C** (Multi-Agent): **2/16** passed  `██░░░░░░░░░░░░░░`
- **Category D** (Decomposition Required): **4/17** passed  `████░░░░░░░░░░░░░`
- **Category E** (Edge Cases / Ambiguous): **20/20** passed  `████████████████████`
- **Category F** (Fallback Triggers): **15/15** passed  `███████████████`
