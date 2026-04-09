import json
d = json.load(open('benchmark_results.json'))
print(f"{len(d)} queries completed")
for r in d:
    print(f"  Q{r['id']}: {r['category']} t={r['response_time_sec']:.1f}s")
