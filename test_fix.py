"""End-to-end test: disaster agent with qwen/qwen3-32b"""
from utils.llm_client import get_llm_client
from utils.database import DatabaseManager
from utils.vector_db import VectorDBManager
from agents.disaster_agent import DisasterAgent

print("Initializing...")
llm = get_llm_client()
db = DatabaseManager()
vdb = VectorDBManager()
agent = DisasterAgent(db, vdb)

query = "give one recent landslide in india and its current condition"
print(f"Running query: {query}")
result = agent.process(query)

print()
print("=" * 60)
print("Status:", result.get("status"))
print("Agent:", result.get("agent"))
answer = result.get("answer", "")
print("Answer length:", len(answer))
print("Answer preview:", answer[:500])
