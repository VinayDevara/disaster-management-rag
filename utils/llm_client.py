"""
LLM Client for Groq API
Handles all LLM interactions with error handling and retries
"""
import os
import json
from typing import Dict, List, Optional, Any
from groq import Groq
from config.config import Config

class LLMClient:
    """
    Unified LLM client for Groq API
    Can be easily swapped for SLM later
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.GROQ_API_KEY
        self.model = model or Config.GROQ_MODEL
        self.client = Groq(api_key=self.api_key)
        
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = Config.TEMPERATURE,
        max_tokens: int = Config.MAX_TOKENS,
        json_mode: bool = False
    ) -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to expect JSON output
            
        Returns:
            Generated text response
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=Config.TOP_P,
                response_format={"type": "json_object"} if json_mode else {"type": "text"}
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_tools(
        self,
        prompt: str,
        system_prompt: str,
        tools: List[Dict],
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate response with tool calling capability
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            tools: List of available tools
            tool_choice: Tool selection strategy
            
        Returns:
            Dictionary with response and tool calls
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS
            )
            
            choice = response.choices[0]
            result = {
                "content": choice.message.content,
                "tool_calls": []
            }
            
            # Extract tool calls if present
            if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
            
            return result
        
        except Exception as e:
            print(f"❌ LLM Tool Error: {e}")
            return {
                "content": f"Error: {str(e)}",
                "tool_calls": []
            }
    
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
