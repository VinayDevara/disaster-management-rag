"""
Orchestrator Agent - Routes queries to specialized agents
Classifies complex queries and coordinates multi-agent responses
"""
from typing import Dict, List, Any, Optional
from utils.llm_client import get_llm_client
import json

class OrchestratorAgent:
    """
    Orchestration layer that:
    1. Classifies user queries
    2. Routes to appropriate specialized agents
    3. Coordinates multi-domain queries
    4. Manages agent communication
    """
    
    def __init__(self):
        self.llm = get_llm_client()
        
        self.system_prompt = """You are an Orchestrator Agent for a disaster management system.

Your role is to analyze user queries and route them to the appropriate specialized agents:

1. FLIGHT AGENT - Handles:
   - Flight tracking and ADS-B data
   - Aircraft positions and trajectories
   - Emergency flight situations
   - Flight diversions and delays
   - Aviation safety queries

2. WEATHER AGENT - Handles:
   - Current weather conditions
   - Weather forecasts
   - Severe weather events
   - Meteorological data
   - Weather impact on operations

3. DISASTER AGENT - Handles:
   - Natural disaster events
   - Wildfires, earthquakes, floods, storms
   - Disaster impact assessment
   - Emergency situations
   - Disaster location and severity

Query Classification Guidelines:
- SIMPLE queries need ONE agent
- COMPLEX queries need MULTIPLE agents
- Cross-intelligence queries require correlation between domains

Examples:
- "What flights are near Los Angeles?" → Flight Agent only
- "Show active wildfires" → Disaster Agent only
- "Are there flights affected by the California wildfires?" → Flight + Disaster (complex)
- "What's the weather in the hurricane zone and are flights diverted?" → Weather + Flight (complex)

Return JSON with:
{{
  "query_type": "simple" or "complex",
  "primary_agent": "flight|weather|disaster",
  "secondary_agents": ["agent1", "agent2"],
  "requires_cross_intelligence": true/false,
  "reasoning": "explanation",
  "extracted_entities": {{
    "locations": [],
    "flight_numbers": [],
    "disaster_types": [],
    "coordinates": []
  }}
}}
"""
    
    def classify_query(self, query: str) -> Dict[str, Any]:
        """
        Classify and route query to appropriate agents
        
        Args:
            query: User query
            
        Returns:
            Classification and routing information
        """
        print(f"🎯 Orchestrator classifying query: {query}")
        
        # Use LLM for intelligent classification
        classification_response = self.llm.generate(
            prompt=f"Classify this query and determine routing:\n\nQuery: {query}",
            system_prompt=self.system_prompt,
            json_mode=True,
            temperature=0.3
        )
        
        try:
            classification = json.loads(classification_response)
        except:
            # Fallback classification
            classification = {
                "query_type": "simple",
                "primary_agent": "flight",
                "secondary_agents": [],
                "requires_cross_intelligence": False,
                "reasoning": "Failed to parse classification, defaulting to flight agent",
                "extracted_entities": {}
            }
        
        # Validate and sanitize classification
        valid_agents = ["flight", "weather", "disaster"]
        
        if classification.get("primary_agent") not in valid_agents:
            classification["primary_agent"] = "flight"
        
        classification["secondary_agents"] = [
            agent for agent in classification.get("secondary_agents", [])
            if agent in valid_agents and agent != classification["primary_agent"]
        ]
        
        return classification
    
    def decompose_complex_query(self, query: str, classification: Dict) -> Dict[str, str]:
        """
        Decompose complex query into sub-queries for each agent
        
        Args:
            query: Original user query
            classification: Query classification
            
        Returns:
            Dictionary mapping agent names to their specific sub-queries
        """
        if classification.get("query_type") == "simple":
            return {classification["primary_agent"]: query}
        
        # Use LLM to break down complex query
        decomposition_prompt = f"""Break down this complex query into specific sub-queries for each agent.

Original Query: {query}

Primary Agent: {classification['primary_agent']}
Secondary Agents: {classification['secondary_agents']}

Create focused sub-queries that each agent can answer independently.
The consensus agent will later correlate the results.

Return JSON:
{{
  "flight": "specific flight-related question" (if needed),
  "weather": "specific weather-related question" (if needed),
  "disaster": "specific disaster-related question" (if needed)
}}

Only include agents that are needed for this query.
"""
        
        decomposition_response = self.llm.generate(
            prompt=decomposition_prompt,
            system_prompt=self.system_prompt,
            json_mode=True,
            temperature=0.4
        )
        
        try:
            sub_queries = json.loads(decomposition_response)
        except:
            # Fallback: send full query to all agents
            agents = [classification["primary_agent"]] + classification.get("secondary_agents", [])
            sub_queries = {agent: query for agent in agents}
        
        return sub_queries
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """
        Complete routing process: classify, decompose, and prepare execution
        
        Args:
            query: User query
            
        Returns:
            Routing plan with classification and sub-queries
        """
        # Step 1: Classify
        classification = self.classify_query(query)
        
        print(f"📋 Classification:")
        print(f"   Type: {classification['query_type']}")
        print(f"   Primary Agent: {classification['primary_agent']}")
        print(f"   Secondary Agents: {classification.get('secondary_agents', [])}")
        print(f"   Cross-Intelligence: {classification.get('requires_cross_intelligence', False)}")
        
        # Step 2: Decompose if complex
        if classification.get("query_type") == "complex":
            sub_queries = self.decompose_complex_query(query, classification)
            print(f"📝 Sub-queries: {list(sub_queries.keys())}")
        else:
            sub_queries = {classification["primary_agent"]: query}
        
        # Step 3: Create routing plan
        routing_plan = {
            "original_query": query,
            "classification": classification,
            "sub_queries": sub_queries,
            "execution_order": self._determine_execution_order(classification, sub_queries),
            "requires_consensus": classification.get("requires_cross_intelligence", False)
        }
        
        return routing_plan
    
    def _determine_execution_order(self, classification: Dict, sub_queries: Dict) -> List[str]:
        """
        Determine optimal execution order for agents
        
        Some queries may have dependencies (e.g., get disaster location first,
        then query flights in that area)
        """
        execution_order = []
        
        # Primary agent first
        primary = classification.get("primary_agent")
        if primary in sub_queries:
            execution_order.append(primary)
        
        # Secondary agents
        for agent in classification.get("secondary_agents", []):
            if agent in sub_queries and agent not in execution_order:
                execution_order.append(agent)
        
        # Add any remaining agents from sub_queries
        for agent in sub_queries:
            if agent not in execution_order:
                execution_order.append(agent)
        
        return execution_order
    
    def create_agent_context(
        self,
        query: str,
        classification: Dict,
        previous_results: Optional[Dict] = None
    ) -> Dict:
        """
        Create context to pass to agents
        
        Args:
            query: Query for this specific agent
            classification: Overall classification
            previous_results: Results from previously executed agents
            
        Returns:
            Context dictionary
        """
        context = {
            "original_query": classification.get("original_query", query),
            "query_type": classification.get("query_type"),
            "entities": classification.get("extracted_entities", {}),
            "cross_intelligence_required": classification.get("requires_cross_intelligence", False)
        }
        
        # Add relevant info from previous agents
        if previous_results:
            context["previous_results"] = previous_results
        
        return context


if __name__ == "__main__":
    # Test orchestrator
    orchestrator = OrchestratorAgent()
    
    # Test simple query
    print("=" * 80)
    print("TEST 1: Simple Query")
    print("=" * 80)
    plan1 = orchestrator.route_query("Show me all emergency flights")
    print(json.dumps(plan1, indent=2))
    
    # Test complex query
    print("\n" + "=" * 80)
    print("TEST 2: Complex Query")
    print("=" * 80)
    plan2 = orchestrator.route_query("Are there any flights near the California wildfires?")
    print(json.dumps(plan2, indent=2))
