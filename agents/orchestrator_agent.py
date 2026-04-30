"""
Orchestrator Agent - Central Hub Pattern
Routes queries, manages agent execution with retry logic,
evaluates results for re-invocation, and falls back to FlightAgent if needed.
"""
from typing import Dict, List, Any, Optional
from utils.llm_client import get_llm_client
from agents.dspy_signatures import (
    ClassifyQuery,
    DecomposeQuery,
    EvaluateResults,
)
from config.config import Config
import json
import dspy
from datetime import datetime


class OrchestratorAgent:
    """
    Central hub orchestrator that:
    1. Classifies and decomposes user queries (DSPy)
    2. Actively invokes sub-agents (not just planning)
    3. Can re-invoke agents with refined queries based on intermediate results
    4. Retries failed agent calls (configurable MAX_RETRIES)
    5. Falls back to FlightAgent as backup orchestrator if primary fails
    """

    MAX_RETRIES = int(getattr(Config, "MAX_RETRIES", 2))
    MAX_REINVOCATIONS = int(getattr(Config, "MAX_REINVOCATIONS", 2))

    def __init__(self, flight_agent, weather_agent, disaster_agent, consensus_agent):
        self.llm = get_llm_client()

        # Agent registry — orchestrator holds direct connections to every sub-agent
        self.agents = {
            "flight": flight_agent,
            "weather": weather_agent,
            "disaster": disaster_agent,
        }
        self.consensus_agent = consensus_agent

        # DSPy predictors for structured decisions
        self.classify_predictor = dspy.Predict(ClassifyQuery)
        self.decompose_predictor = dspy.Predict(DecomposeQuery)
        self.evaluate_predictor = dspy.Predict(EvaluateResults)

    # ── Public entry point ──────────────────────────────────────────────────

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main entry point.  Runs the hub loop; on failure falls back to
        FlightAgent acting as a simplified orchestrator.
        """
        try:
            return self._hub_process(query)
        except Exception as e:
            print(f"⚠️ Primary orchestrator failed: {e}")
            print("🔄 Falling back to Flight Agent as backup orchestrator...")
            return self._fallback_process(query, str(e))

    # ── Core hub loop ───────────────────────────────────────────────────────

    def _hub_process(self, query: str) -> Dict[str, Any]:
        start_time = datetime.now()

        # 1 ── Classify
        print(f"\n🎯 Orchestrator classifying query: {query}")
        classification = self._classify_query(query)

        print(f"📋 Classification:")
        print(f"   Type: {classification['query_type']}")
        print(f"   Primary Agent: {classification['primary_agent']}")
        print(f"   Secondary Agents: {classification.get('secondary_agents', [])}")
        print(f"   Cross-Intelligence: {classification.get('requires_cross_intelligence', False)}")

        # 1a ── Short-circuit: general/conversational queries go straight to LLM
        if classification["query_type"] == "general" or classification["primary_agent"] == "none":
            print("💬 General query — responding directly via LLM (no agent)")
            return self._handle_general_query(query, start_time)

        # 2 ── Decompose into sub-queries
        sub_queries = self._decompose_query(query, classification)
        print(f"📝 Sub-queries: {list(sub_queries.keys())}")

        # 3 ── Execute each agent with retry
        print("\n⚡ Executing agents...")
        agent_results: Dict[str, Any] = {}
        execution_order = self._get_execution_order(classification, sub_queries)

        for agent_name in execution_order:
            sub_query = sub_queries.get(agent_name, query)
            context = self._build_context(classification, agent_results)
            result = self._execute_with_retry(agent_name, sub_query, context)
            agent_results[agent_name] = result

        # 4 ── Evaluate — decide if any agent needs re-invocation
        reinvocations = self._evaluate_and_reinvoke(query, agent_results, classification)
        for agent_name, refined_query in reinvocations.items():
            print(f"   🔁 Re-invoking {agent_name.title()} Agent: {refined_query[:60]}...")
            context = self._build_context(classification, agent_results)
            result = self._execute_with_retry(agent_name, refined_query, context)
            agent_results[agent_name] = result  # update with refined result

        # 5 ── Consensus if multi-agent and cross-intelligence required
        requires_consensus = (
            len(agent_results) > 1
            and classification.get("requires_cross_intelligence", False)
        )

        if requires_consensus:
            print("\n🤝 Running consensus analysis...")
            final_response = self._execute_consensus(query, agent_results, classification)
        else:
            primary = classification["primary_agent"]
            final_response = agent_results.get(primary, next(iter(agent_results.values()), {}))

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        print(f"\n✅ Query processing complete in {execution_time:.2f}s\n")

        return {
            "query": query,
            "timestamp": start_time.isoformat(),
            "execution_time_seconds": execution_time,
            "classification": classification,
            "agent_results": agent_results,
            "final_response": final_response,
            "metadata": {
                "query_type": classification["query_type"],
                "agents_used": list(agent_results.keys()),
                "consensus_applied": requires_consensus,
                "orchestrator": "primary",
            },
        }

    # ── Classification & decomposition ──────────────────────────────────────

    def _classify_query(self, query: str) -> Dict[str, Any]:
        """Classify query using DSPy structured prediction."""
        try:
            result = self.classify_predictor(query=query)
            classification = (
                result.output.model_dump()
                if hasattr(result.output, "model_dump")
                else result.output.dict()
            )
            classification["extracted_entities"] = {}
        except Exception as e:
            print(f"⚠️ DSPy classification failed: {e}")
            classification = {
                "query_type": "simple",
                "primary_agent": "flight",
                "secondary_agents": [],
                "requires_cross_intelligence": False,
                "reasoning": f"Classification failed ({e}), defaulting to flight agent",
                "extracted_entities": {},
            }

        # Validate — normalize to lowercase first (DSPy may return uppercase)
        valid_agents = ["flight", "weather", "disaster", "none"]
        primary = str(classification.get("primary_agent", "flight")).lower().strip()
        query_type = str(classification.get("query_type", "simple")).lower().strip()

        # If classified as general, force primary_agent to none
        if query_type == "general":
            classification["primary_agent"] = "none"
            classification["query_type"] = "general"
        else:
            # For non-general queries, only flight/weather/disaster are valid
            if primary not in ["flight", "weather", "disaster"]:
                primary = "flight"
            classification["primary_agent"] = primary

        classification["secondary_agents"] = [
            a.lower().strip()
            for a in classification.get("secondary_agents", [])
            if a.lower().strip() in ["flight", "weather", "disaster"]
            and a.lower().strip() != classification["primary_agent"]
        ]

        return classification

    def _decompose_query(self, query: str, classification: Dict) -> Dict[str, str]:
        """Decompose complex query into agent-specific sub-queries."""
        if classification.get("query_type") == "simple":
            return {classification["primary_agent"]: query}

        try:
            result = self.decompose_predictor(
                query=query,
                primary_agent=classification["primary_agent"],
                secondary_agents=str(classification.get("secondary_agents", [])),
            )
            sub_q = (
                result.output.model_dump()
                if hasattr(result.output, "model_dump")
                else result.output.dict()
            )
            sub_queries = {k: v for k, v in sub_q.items() if v and isinstance(v, str) and v.strip()}
            if not sub_queries:
                raise ValueError("No sub-queries extracted")
        except Exception as e:
            print(f"⚠️ DSPy decomposition failed: {e}")
            agents = [classification["primary_agent"]] + classification.get("secondary_agents", [])
            sub_queries = {agent: query for agent in agents}

        return sub_queries

    # ── General / conversational query handler ──────────────────────────────

    def _handle_general_query(self, query: str, start_time) -> Dict[str, Any]:
        """Respond to greetings and general questions directly via LLM — no agents."""
        general_system = (
            "You are DisasterRAG, an AI assistant for the Disaster Management Intelligence System. "
            "You help users understand disasters, weather, and flight safety in India (especially Karnataka). "
            "For greetings and general questions, respond warmly and concisely. "
            "Let users know you can answer questions about: active disasters, weather conditions, "
            "flight tracking, cyclone warnings, flood alerts, and emergency logistics. "
            "Keep your response short and friendly."
        )
        try:
            answer = self.llm.generate(query, system_prompt=general_system)
        except Exception as e:
            print(f"⚠️ General LLM call failed: {e}")
            answer = (
                "Hello! I'm DisasterRAG, your Disaster Management Intelligence System. "
                "I can help you with:\n"
                "- 🌪️ Active disasters and alerts\n"
                "- 🌤️ Weather conditions and forecasts\n"
                "- ✈️ Flight tracking and safety\n"
                "- 🚨 Cyclone warnings and flood alerts\n\n"
                "What would you like to know?"
            )

        end_time = datetime.now()
        return {
            "query": query,
            "timestamp": start_time.isoformat(),
            "execution_time_seconds": (end_time - start_time).total_seconds(),
            "classification": {"query_type": "general", "primary_agent": "none"},
            "agent_results": {},
            "final_response": {"answer": answer},
            "metadata": {
                "query_type": "general",
                "agents_used": [],
                "consensus_applied": False,
                "orchestrator": "direct_llm",
            },
        }

    # ── Agent execution with retry ──────────────────────────────────────────

    def _execute_with_retry(
        self,
        agent_name: str,
        query: str,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Execute an agent with retry logic."""
        last_error = None

        for attempt in range(self.MAX_RETRIES + 1):
            prefix = "🔄" if attempt > 0 else "→"
            print(f"   {prefix} {agent_name.title()} Agent (attempt {attempt + 1}): {query[:60]}...")

            try:
                result = self.agents[agent_name].process(query, context)

                # Check if result is usable
                answer = str(result.get("answer", ""))
                has_data = (result.get("data_count", 0) or result.get("event_count", 0)) > 0

                if answer and "Error" not in answer:
                    data_count = result.get("data_count", 0) or result.get("event_count", 0)
                    print(f"     ✓ Retrieved {data_count} data points")
                    return result

                # Result has issues but may be partially usable
                if attempt == self.MAX_RETRIES:
                    print(f"     ⚠️ Returning partial result after {attempt + 1} attempts")
                    result["status"] = "partial"
                    return result

                last_error = answer or "Empty response"
                print(f"     ⚠️ Attempt {attempt + 1} returned errors, retrying...")

            except Exception as e:
                last_error = str(e)
                print(f"     ✗ Attempt {attempt + 1} failed: {e}")

                if attempt == self.MAX_RETRIES:
                    return {
                        "agent": agent_name,
                        "query": query,
                        "answer": f"Agent failed after {self.MAX_RETRIES + 1} attempts: {last_error}",
                        "status": "failed",
                        "data_count": 0,
                    }

        # Should not reach here, but just in case
        return {
            "agent": agent_name,
            "query": query,
            "answer": f"Agent exhausted retries: {last_error}",
            "status": "failed",
            "data_count": 0,
        }

    # ── Consensus execution ─────────────────────────────────────────────────

    def _execute_consensus(
        self, query: str, agent_results: Dict[str, Any], classification: Dict
    ) -> Dict[str, Any]:
        """Execute consensus with retry."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                return self.consensus_agent.process(query, agent_results, classification)
            except Exception as e:
                print(f"     ⚠️ Consensus attempt {attempt + 1} failed: {e}")
                if attempt == self.MAX_RETRIES:
                    # Fall back to concatenating agent answers
                    parts = []
                    for name, result in agent_results.items():
                        parts.append(f"### {name.capitalize()} Agent\n{result.get('answer', 'No data')}\n")
                    return {
                        "unified_response": "\n".join(parts),
                        "status": "fallback",
                        "error": str(e),
                    }

    # ── Result evaluation & re-invocation ───────────────────────────────────

    def _evaluate_and_reinvoke(
        self, query: str, results: Dict[str, Any], classification: Dict
    ) -> Dict[str, str]:
        """
        Evaluate agent results using DSPy and determine if any agent needs
        re-invocation with a refined query.  Returns dict of agent_name → refined_query.
        """
        if not classification.get("requires_cross_intelligence", False):
            return {}

        try:
            results_summary = {
                agent: {
                    "has_answer": bool(r.get("answer")),
                    "data_count": r.get("data_count", 0) or r.get("event_count", 0),
                    "status": r.get("status", "unknown"),
                    "answer_preview": str(r.get("answer", ""))[:300],
                }
                for agent, r in results.items()
            }

            eval_result = self.evaluate_predictor(
                original_query=query,
                agent_results=json.dumps(results_summary, default=str),
                classification=json.dumps(classification, default=str),
            )

            decision = (
                eval_result.output.model_dump()
                if hasattr(eval_result.output, "model_dump")
                else eval_result.output.dict()
            )

            if decision.get("needs_reinvocation"):
                reinvocations = decision.get("reinvocations", {})
                # Validate: only allow known agents, cap count
                valid = {
                    k: v
                    for k, v in reinvocations.items()
                    if k in self.agents and isinstance(v, str) and v.strip()
                }
                # Limit to MAX_REINVOCATIONS
                return dict(list(valid.items())[: self.MAX_REINVOCATIONS])

        except Exception as e:
            print(f"⚠️ Result evaluation failed: {e}")

        return {}

    # ── Fallback orchestrator ───────────────────────────────────────────────

    def _fallback_process(self, query: str, error_msg: str) -> Dict[str, Any]:
        """Delegate to FlightAgent as backup orchestrator."""
        return self.agents["flight"].process_as_orchestrator(
            query, self.agents, self.consensus_agent, error_msg
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _get_execution_order(
        self, classification: Dict, sub_queries: Dict
    ) -> List[str]:
        """Determine optimal agent execution order."""
        order = []
        primary = classification.get("primary_agent")
        if primary in sub_queries:
            order.append(primary)
        for agent in classification.get("secondary_agents", []):
            if agent in sub_queries and agent not in order:
                order.append(agent)
        for agent in sub_queries:
            if agent not in order:
                order.append(agent)
        return order

    def _build_context(
        self, classification: Dict, previous_results: Optional[Dict] = None
    ) -> Dict:
        """Build context dict to pass to an agent."""
        context = {
            "original_query": classification.get("original_query", ""),
            "query_type": classification.get("query_type"),
            "entities": classification.get("extracted_entities", {}),
            "cross_intelligence_required": classification.get(
                "requires_cross_intelligence", False
            ),
        }
        if previous_results:
            # Pass summaries of previous results to avoid huge payloads
            context["previous_results"] = {
                agent: {
                    "answer_preview": str(r.get("answer", ""))[:500],
                    "data_count": r.get("data_count", 0) or r.get("event_count", 0),
                }
                for agent, r in previous_results.items()
            }
        return context


if __name__ == "__main__":
    # Quick smoke test (requires real agent instances)
    print("Orchestrator module loaded successfully.")
    orchestrator = OrchestratorAgent.__new__(OrchestratorAgent)
    print("OrchestratorAgent class instantiation stub OK.")
