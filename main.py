"""
Main Disaster Management RAG System
Multimodal Agentic RAG for Flight Tracking, Weather, and Disaster Management
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import Config
from utils.database import DatabaseManager
from utils.vector_db import VectorDBManager
from utils.llm_client import get_llm_client
from agents.orchestrator_agent import OrchestratorAgent
from agents.flight_agent import FlightAgent
from agents.weather_agent import WeatherAgent
from agents.disaster_agent import DisasterAgent
from agents.consensus_agent import ConsensusAgent
import json
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama for Windows
init(autoreset=True)

class DisasterRAGSystem:
    """
    Main system class that coordinates all agents and manages the RAG pipeline
    """
    
    def __init__(self):
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}🚀 Initializing Disaster Management RAG System")
        print(f"{Fore.CYAN}{'='*80}\n")
        
        # Initialize core components
        print(f"{Fore.YELLOW}📊 Initializing database...")
        self.db = DatabaseManager()
        
        print(f"{Fore.YELLOW}🔍 Initializing vector database...")
        self.vector_db = VectorDBManager()
        
        print(f"{Fore.YELLOW}🤖 Initializing LLM client...")
        self.llm = get_llm_client()
        
        # Initialize agents
        print(f"{Fore.YELLOW}🎯 Initializing orchestrator agent...")
        self.orchestrator = OrchestratorAgent()
        
        print(f"{Fore.YELLOW}✈️  Initializing flight agent...")
        self.flight_agent = FlightAgent(self.db, self.vector_db)
        
        print(f"{Fore.YELLOW}🌤️  Initializing weather agent...")
        self.weather_agent = WeatherAgent(self.db, self.vector_db)
        
        print(f"{Fore.YELLOW}🔥 Initializing disaster agent...")
        self.disaster_agent = DisasterAgent(self.db, self.vector_db)
        
        print(f"{Fore.YELLOW}🤝 Initializing consensus agent...")
        self.consensus_agent = ConsensusAgent(self.db)
        
        print(f"\n{Fore.GREEN}✅ System initialized successfully!\n")
    
    def process_query(self, query: str) -> dict:
        """
        Process user query through the complete RAG pipeline
        
        Args:
            query: User query string
            
        Returns:
            Complete response dictionary
        """
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}📝 Processing Query: {query}")
        print(f"{Fore.CYAN}{'='*80}\n")
        
        start_time = datetime.now()
        
        # Step 1: Orchestration - Classify and route query
        print(f"{Fore.YELLOW}Step 1: Query Classification and Routing{Style.RESET_ALL}")
        routing_plan = self.orchestrator.route_query(query)
        
        query_type = routing_plan["classification"]["query_type"]
        requires_consensus = routing_plan["requires_consensus"]
        
        print(f"   Query Type: {Fore.MAGENTA}{query_type}{Style.RESET_ALL}")
        print(f"   Consensus Required: {Fore.MAGENTA}{requires_consensus}{Style.RESET_ALL}\n")
        
        # Step 2: Execute agents
        print(f"{Fore.YELLOW}Step 2: Executing Specialized Agents{Style.RESET_ALL}")
        agent_results = {}
        execution_order = routing_plan["execution_order"]
        
        for agent_name in execution_order:
            sub_query = routing_plan["sub_queries"].get(agent_name, query)
            
            print(f"   {Fore.CYAN}→ {agent_name.title()} Agent: {sub_query[:50]}...{Style.RESET_ALL}")
            
            # Create context with previous results
            context = self.orchestrator.create_agent_context(
                sub_query,
                routing_plan["classification"],
                agent_results if agent_results else None
            )
            
            # Execute appropriate agent
            if agent_name == "flight":
                result = self.flight_agent.process(sub_query, context)
            elif agent_name == "weather":
                result = self.weather_agent.process(sub_query, context)
            elif agent_name == "disaster":
                result = self.disaster_agent.process(sub_query, context)
            else:
                result = {"error": f"Unknown agent: {agent_name}"}
            
            agent_results[agent_name] = result
            
            # Print quick summary
            data_count = result.get("data_count", 0) or result.get("event_count", 0)
            print(f"      {Fore.GREEN}✓ Retrieved {data_count} data points{Style.RESET_ALL}")
        
        # Step 3: Consensus (if needed)
        final_response = None
        
        if requires_consensus and len(agent_results) > 1:
            print(f"\n{Fore.YELLOW}Step 3: Consensus and Cross-Intelligence Analysis{Style.RESET_ALL}")
            consensus_result = self.consensus_agent.process(
                query,
                agent_results,
                routing_plan["classification"]
            )
            final_response = consensus_result
            print(f"   {Fore.GREEN}✓ Cross-intelligence analysis complete{Style.RESET_ALL}")
            print(f"   Correlations Found: {Fore.MAGENTA}{len(consensus_result.get('correlations', []))}{Style.RESET_ALL}")
            print(f"   Severity Level: {Fore.MAGENTA}{consensus_result.get('severity_assessment', {}).get('level', 'unknown')}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}Step 3: Simple Response (No Consensus Needed){Style.RESET_ALL}")
            # Single agent response
            primary_agent = routing_plan["classification"]["primary_agent"]
            final_response = agent_results.get(primary_agent, {})
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"\n{Fore.GREEN}✅ Query processing complete in {execution_time:.2f}s{Style.RESET_ALL}\n")
        
        return {
            "query": query,
            "timestamp": start_time.isoformat(),
            "execution_time_seconds": execution_time,
            "routing_plan": routing_plan,
            "agent_results": agent_results,
            "final_response": final_response,
            "metadata": {
                "query_type": query_type,
                "agents_used": list(agent_results.keys()),
                "consensus_applied": requires_consensus
            }
        }
    
    def load_adsb_data(self, excel_path: str = None):
        """Load ADS-B data from Excel file"""
        excel_path = excel_path or Config.ADSB_DATA_PATH
        
        if not os.path.exists(excel_path):
            print(f"{Fore.RED}❌ ADS-B data file not found: {excel_path}{Style.RESET_ALL}")
            return False
        
        print(f"\n{Fore.CYAN}Loading ADS-B data from: {excel_path}{Style.RESET_ALL}")
        self.db.load_adsb_data(excel_path)
        
        # Also add to vector database (sample)
        flights = self.db.execute_query(
            "SELECT * FROM aircraft WHERE flight IS NOT NULL LIMIT 100"
        )
        
        if flights:
            self.vector_db.add_flight_data(flights)
            print(f"{Fore.GREEN}✅ ADS-B data loaded into both SQL and vector databases{Style.RESET_ALL}\n")
        
        return True
    
    def load_disaster_data(self):
        """Load current disaster data from APIs"""
        print(f"\n{Fore.CYAN}Loading current disaster events...{Style.RESET_ALL}")
        
        events = self.disaster_agent.api_tool.get_active_events(limit=50)
        
        for event in events:
            self.db.insert_disaster_event(event)
            self.vector_db.add_disaster_event(event)
        
        print(f"{Fore.GREEN}✅ Loaded {len(events)} disaster events{Style.RESET_ALL}\n")
    
    def interactive_mode(self):
        """Run system in interactive chat mode"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}💬 Interactive Mode - Disaster Management RAG Chatbot")
        print(f"{Fore.CYAN}{'='*80}\n")
        print(f"{Fore.YELLOW}Commands:")
        print(f"  - Type your question about flights, weather, or disasters")
        print(f"  - 'load data' - Load ADS-B and disaster data")
        print(f"  - 'stats' - Show system statistics")
        print(f"  - 'exit' or 'quit' - Exit the system")
        print(f"{Style.RESET_ALL}\n")
        
        while True:
            try:
                user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print(f"\n{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}\n")
                    break
                
                elif user_input.lower() == 'load data':
                    self.load_adsb_data()
                    self.load_disaster_data()
                    continue
                
                elif user_input.lower() == 'stats':
                    self.show_statistics()
                    continue
                
                # Process query
                result = self.process_query(user_input)
                
                # Display response
                print(f"\n{Fore.CYAN}{'─'*80}")
                print(f"{Fore.CYAN}Assistant:{Style.RESET_ALL}\n")
                
                if "unified_response" in result.get("final_response", {}):
                    # Consensus response
                    print(result["final_response"]["unified_response"])
                elif "answer" in result.get("final_response", {}):
                    # Single agent response
                    print(result["final_response"]["answer"])
                else:
                    print(f"{Fore.RED}Error: Unable to generate response{Style.RESET_ALL}")
                
                print(f"\n{Fore.CYAN}{'─'*80}{Style.RESET_ALL}\n")
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}\n")
                break
            except Exception as e:
                print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}\n")
    
    def show_statistics(self):
        """Show system statistics"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}📊 System Statistics")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # Database stats
        aircraft_count = self.db.execute_query("SELECT COUNT(*) as count FROM aircraft")[0]["count"]
        disaster_count = self.db.execute_query("SELECT COUNT(*) as count FROM disaster_events")[0]["count"]
        weather_count = self.db.execute_query("SELECT COUNT(*) as count FROM weather_events")[0]["count"]
        
        print(f"  {Fore.YELLOW}Database Records:{Style.RESET_ALL}")
        print(f"    Aircraft: {Fore.MAGENTA}{aircraft_count}{Style.RESET_ALL}")
        print(f"    Disaster Events: {Fore.MAGENTA}{disaster_count}{Style.RESET_ALL}")
        print(f"    Weather Events: {Fore.MAGENTA}{weather_count}{Style.RESET_ALL}\n")
        
        # Vector DB stats
        print(f"  {Fore.YELLOW}Vector Database Collections:{Style.RESET_ALL}")
        print(f"    Flights: {Fore.MAGENTA}{self.vector_db.get_collection_count('flights')}{Style.RESET_ALL}")
        print(f"    Weather: {Fore.MAGENTA}{self.vector_db.get_collection_count('weather')}{Style.RESET_ALL}")
        print(f"    Disasters: {Fore.MAGENTA}{self.vector_db.get_collection_count('disasters')}{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")


def main():
    """Main entry point"""
    print(f"""
{Fore.CYAN}╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        Disaster Management Multimodal Agentic RAG System      ║
║                                                                ║
║  Flight Tracking • Weather Analysis • Disaster Monitoring     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
    
    # Initialize system
    system = DisasterRAGSystem()
    
    # Check if data should be loaded
    print(f"{Fore.YELLOW}Would you like to load initial data? (y/n): {Style.RESET_ALL}", end="")
    response = input().strip().lower()
    
    if response == 'y':
        system.load_adsb_data()
        system.load_disaster_data()
    
    # Run interactive mode
    system.interactive_mode()


if __name__ == "__main__":
    main()
