"""
LLM Client for DisasterRAG local Qwen inference.

This module uses Ollama exclusively and applies the shared disaster/tooling
instruction block to all direct generation and tool-calling requests.
"""
import json
from typing import Dict, List, Optional, Any
from groq import Groq
from openai import OpenAI
import dspy
from crewai import LLM
from config.config import Config


class LLMClient:
    """
    Unified local LLM client backed by Ollama and Qwen.

    The client always talks to the local Ollama daemon. A shared disaster
    instruction block is prepended to requests so the model consistently
    follows the tool-calling and grounding rules.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, provider: Optional[str] = None):
        self.provider = provider or Config.LLM_PROVIDER
        
        if self.provider == "openai":
            self.api_key = api_key or Config.OPENAI_API_KEY
            self.model = model or Config.OPENAI_MODEL
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.api_key = api_key or Config.GROQ_API_KEY
            self.model = model or Config.GROQ_MODEL
            self.client = Groq(api_key=self.api_key)
            
        self.init_dspy()

    # ── DSPy configuration ──────────────────────────────────────────────

    def init_dspy(self):
        """Initialize DSPy globally with the selected model"""
        if self.provider == "openai":
            lm = dspy.LM(f'openai/{self.model}', api_key=self.api_key)
        else:
            lm = dspy.LM(f'groq/{self.model}', api_key=self.api_key)
        dspy.configure(lm=lm)
        return lm
        
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = Config.TEMPERATURE,
        max_tokens: int = Config.MAX_TOKENS,
        json_mode: bool = False,
    ) -> str:
        messages = [{"role": "system", "content": self._compose_system_prompt(system_prompt)}]
        messages.append({"role": "user", "content": prompt})
        try:
            return self._ollama_chat(messages, temperature, max_tokens, json_mode)
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return f"Error generating response locally: {str(e)}"

    def generate_with_tools(
        self,
        prompt: str,
        system_prompt: str,
        tools: List[Dict],
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": self._compose_system_prompt(system_prompt)},
            {"role": "user", "content": prompt},
        ]
        try:
            return self._ollama_chat_with_tools(
                messages, tools, Config.TEMPERATURE, Config.MAX_TOKENS,
            )
        except Exception as e:
            return {"content": f"Error generating tool response locally: {str(e)}", "tool_calls": []}

    # ── Higher-level helpers (unchanged logic, use generate()) ──────────

    def classify_query(self, query: str, categories: List[str]) -> Dict[str, Any]:
        """
        Classify query into categories using LLM
        
        Args:
            query: User query
            categories: List of possible categories
            
        Returns:
            Dictionary with classification results
        """
        system_prompt = f"""You are a query classification system for disaster management.
Analyze the user query and determine which domain(s) it belongs to.

Available domains:
{', '.join(categories)}

Return a JSON object with:
1. primary_domain: The main domain for this query
2. secondary_domains: List of related domains (can be empty)
3. reasoning: Brief explanation of classification
4. query_complexity: "simple" or "complex"
5. requires_cross_intelligence: true if multiple domains need to be correlated

Example output:
{{
  "primary_domain": "flight",
  "secondary_domains": ["weather"],
  "reasoning": "Query asks about flight diversions which requires flight data and weather conditions",
  "query_complexity": "complex",
  "requires_cross_intelligence": true
}}
"""
        
        response = self.generate(
            prompt=f"Classify this query: {query}",
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.3
        )
        
        try:
            return json.loads(response)
        except:
            return {
                "primary_domain": categories[0],
                "secondary_domains": [],
                "reasoning": "Failed to parse classification",
                "query_complexity": "simple",
                "requires_cross_intelligence": False
            }
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text using LLM
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of entity types and values
        """
        system_prompt = """Extract entities from the text and return as JSON.

Categories to extract:
- flight_numbers: Flight identifiers (e.g., AA100, UAL456)
- locations: Cities, countries, airports (e.g., LAX, London, JFK)
- aircraft_types: Aircraft models (e.g., Boeing 737, A320)
- dates: Date references (e.g., today, March 15, 2024)
- disaster_types: Types of disasters (e.g., hurricane, earthquake, wildfire)
- coordinates: Latitude/longitude pairs

Return JSON format:
{
  "flight_numbers": [...],
  "locations": [...],
  "aircraft_types": [...],
  "dates": [...],
  "disaster_types": [...],
  "coordinates": [...]
}
"""
        
        response = self.generate(
            prompt=f"Extract entities from: {text}",
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.2
        )
        
        try:
            return json.loads(response)
        except:
            return {
                "flight_numbers": [],
                "locations": [],
                "aircraft_types": [],
                "dates": [],
                "disaster_types": [],
                "coordinates": []
            }


# Singleton instance
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

def get_crewai_llm():
    from crewai import LLM
    if Config.LLM_PROVIDER == "openai":
        return LLM(model=f"openai/{Config.OPENAI_MODEL}", api_key=Config.OPENAI_API_KEY)
    return LLM(model=f"groq/{Config.GROQ_MODEL}", api_key=Config.GROQ_API_KEY)

def get_crewai_tool_llm():
    from crewai import LLM
    if Config.LLM_PROVIDER == "openai":
        return LLM(model=f"openai/{Config.OPENAI_MODEL}", api_key=Config.OPENAI_API_KEY)
    return LLM(model=f"groq/{Config.GROQ_MODEL}", api_key=Config.GROQ_API_KEY)