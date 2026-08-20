import pandas as pd
import json
import time
import os
from l2_engine import analyze_privacy_routing, MessageGroupTracker, compute_priority, answer_demo_query

l2_messages = pd.read_csv("Level_2/L2_Candidate_Dataset/l2_messages.csv")
demo_messages = pd.read_csv("Level_2/L2_Candidate_Dataset/l2_demo_messages.csv")
demo_queries = pd.read_csv("Level_2/L2_Candidate_Dataset/l2_demo_queries.csv")

# Run Benchmark
tracker = MessageGroupTracker()
privacy_records = []
priority_records = []

t0 = time.perf_counter()
# 1. Process L2 Messages (MSG_0901 to MSG_1080)
for _, r in l2_messages.iterrows():
    p = analyze_privacy_routing(r['message_id'], r['message'])
    privacy_records.append(p)
    gid = tracker.process_message(r['message_id'], r['timestamp'], r['message'], p)
    ginfo = tracker.groups.get(gid) if gid else None
    prio = compute_priority(r['message_id'], r['message'], p, ginfo)
    priority_records.append(prio)

# 2. Process Demo Messages (DEMO_001 to DEMO_024)
demo_priv = []
demo_prio = []
for _, r in demo_messages.iterrows():
    p = analyze_privacy_routing(r['message_id'], r['message'])
    demo_priv.append(p)
    gid = tracker.process_message(r['message_id'], r['timestamp'], r['message'], p)
    ginfo = tracker.groups.get(gid) if gid else None
    prio = compute_priority(r['message_id'], r['message'], p, ginfo)
    demo_prio.append(prio)
t1 = time.perf_counter()

# 3. Process Queries
t_q0 = time.perf_counter()
query_results = []
for _, r in demo_queries.iterrows():
    ans = answer_demo_query(r['query_id'], r['query'], tracker.groups, demo_prio, demo_priv)
    query_results.append(ans)
t_q1 = time.perf_counter()

# Write JSON Files
with open("Level_2/priority_output.json", "w") as f:
    json.dump(priority_records + demo_prio, f, indent=2)

with open("Level_2/related_groups.json", "w") as f:
    json.dump(tracker.groups, f, indent=2)

with open("Level_2/privacy_routing.json", "w") as f:
    json.dump(privacy_records + demo_priv, f, indent=2)

with open("Level_2/benchmark_queries_output.json", "w") as f:
    json.dump(query_results, f, indent=2)

print("--- BENCHMARK RESULTS ---")
print(f"Total Batch Ingestion Time (204 msgs): {(t1 - t0)*1000:.2f} ms")
print(f"Average Ingestion Latency: {((t1 - t0)/204)*1000:.4f} ms/msg")
print(f"Total 8 Queries QA Time: {(t_q1 - t_q0)*1000:.2f} ms")
print(f"Average Query Latency: {((t_q1 - t_q0)/8)*1000:.4f} ms/query")