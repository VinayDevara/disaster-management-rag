
import sys
import os
import json
import time
from colorama import Fore, Style, init

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import DisasterRAGSystem

# Initialize colorama
init(autoreset=True)

def run_metrics_test():
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📊 Running Query Performance Metrics Test")
    print(f"{Fore.CYAN}{'='*80}\n")

    # Initialize system
    try:
        system = DisasterRAGSystem()
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to initialize system: {e}")
        return

    # Define test queries based on user request
    test_queries = [
        {
            "type": "Single-Domain (Flight)",
            "query": "List flights in October 2025."
        },
        {
            "type": "Geographic (Weather)",
            "query": "Weather events in California."
        },
        {
            "type": "Semantic (Disaster)",
            "query": "Disasters similar to wildfires."
        },
        {
            "type": "Cross-Domain (Complex)",
            "query": "Give information about 3 recent disasters and current weather conditions there."
        }
    ]

    print(f"{Fore.YELLOW}🚀 Starting test execution with {len(test_queries)} queries...\n")

    for i, test_case in enumerate(test_queries, 1):
        print(f"{Fore.CYAN}{'-'*60}")
        print(f"{Fore.CYAN}Test #{i}: {test_case['type']}")
        print(f"{Fore.CYAN}Query: {test_case['query']}")
        print(f"{Fore.CYAN}{'-'*60}{Style.RESET_ALL}\n")

        try:
            # Process query
            result = system.process_query(test_case['query'])
            
            # Extract execution time
            exec_time = result.get("execution_time_seconds", 0)
            print(f"{Fore.GREEN}✅ Completed in {exec_time:.4f} seconds{Style.RESET_ALL}\n")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error processing query: {e}{Style.RESET_ALL}\n")

    # Print final metrics summary
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📈 Final Performance Metrics Summary")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    summary = system.metrics_tracker.get_summary()
    print(json.dumps(summary, indent=2))

    # Save metrics to file
    with open("metrics_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{Fore.GREEN}✅ Metrics saved to metrics_report.json{Style.RESET_ALL}\n")

if __name__ == "__main__":
    run_metrics_test()
