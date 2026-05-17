#!/usr/bin/env python3
"""Test script for the local Ollama/Qwen LLM client."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.llm_client import get_llm_client

def test_basic_generation():
    """Test basic text generation"""
    print("Testing basic text generation...")
    client = get_llm_client()
    response = client.generate("Say hello in one sentence")
    print(f"Response: {response}")
    print(f"Active provider: {client._active_provider}")
    return response

def test_tool_calling():
    """Test tool calling with DSPy"""
    print("\nTesting tool calling with DSPy...")
    client = get_llm_client()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_active_events",
                "description": "Get currently active disaster events worldwide.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max events to return"}
                    },
                    "required": [],
                },
            },
        }
    ]

    result = client.generate_with_tools(
        prompt="Find one recent disaster event and explain why it matters.",
        system_prompt="Use the available tool before answering.",
        tools=tools,
    )
    print(f"Tool call result: {result}")

    classification = client.classify_query("What flights are near Mumbai?", ["flight", "weather", "disaster"])
    print(f"Query classification: {classification}")

    return result

if __name__ == "__main__":
    print("Starting LLM client tests...")
    try:
        test_basic_generation()
        test_tool_calling()
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()