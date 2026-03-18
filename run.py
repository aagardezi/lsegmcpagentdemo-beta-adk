import argparse
import asyncio
import os
import sys
from dotenv import load_dotenv

from google.adk.runners import InMemoryRunner
from google.genai import types

# Load local .env
load_dotenv()

from lseg_market_agent.agent import root_agent

# Use the logging utility exactly as GEMINI.MD suggests
from google.adk.cli.utils import logs
logs.log_to_tmp_folder()

async def main():
    parser = argparse.ArgumentParser(description="LSEG ADK Demo Runner")
    parser.add_argument("--prompt", type=str, required=False, 
                        default="Analyze Apple's (AAPL.O) recent financial fundamentals, check the latest news sentiment around it, fetch analyst consensus estimates for the next year, and overlay recent US macroeconomic conditions (like CPI & GDP) to provide a complete investment summary.")
    args = parser.parse_args()

    app_name = "lseg_adk_demo"

    # Instantiate the agent
    print("Connecting to LSEG MCP Server...")
    try:
        agent = root_agent
    except Exception as e:
        print(f"Error connecting or authenticating to LSEG MCP: {e}")
        sys.exit(1)

    print("Initializing ADK Runner...")
    runner = InMemoryRunner(agent=agent, app_name=app_name)

    print("Creating Session...")
    session = await runner.session_service.create_session(
        app_name=app_name, user_id="default_user"
    )

    print(f"\nSending Prompt: '{args.prompt}'\n")
    user_message = types.Content(
        role="user", parts=[types.Part.from_text(text=args.prompt)]
    )

    final_response = None
    
    print("LLM is processing (this may take a minute with multiple tool calls)...")
    try:
        async for event in runner.run_async(
            user_id="default_user",
            session_id=session.id,
            new_message=user_message
        ):
            # The events stream handles tool calls and responses.
            # Only intercepting final messages
            if getattr(event, 'is_final_response', lambda: False)() and event.content:
                final_response = event
                break
    except Exception as e:
        print(f"Execution Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("FINAL AGENT RESPONSE")
    print("="*80 + "\n")
    
    if final_response and final_response.content and final_response.content.parts:
        print(final_response.content.parts[0].text)
    else:
        print("No final response generated or error occurred.")

if __name__ == "__main__":
    asyncio.run(main())
