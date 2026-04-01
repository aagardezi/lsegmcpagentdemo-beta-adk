import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import InMemoryRunner
from google.genai import types
from lseg_market_agent.agent import root_agent

async def main():
    print("Initializing InMemoryRunner with root_agent...")
    runner = InMemoryRunner(agent=root_agent, app_name="debug")
    
    session = await runner.session_service.create_session(
        app_name="debug", user_id="default_user"
    )

    prompt = "What was Microsoft's (MSFT.O) Gross Income and EPS for 2022 and 2023?"
    print(f"\nUser: {prompt}\n")

    user_message = types.Content(
        role="user", parts=[types.Part.from_text(text=prompt)]
    )

    async for event in runner.run_async(
        user_id="default_user",
        session_id=session.id,
        new_message=user_message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"Agent Thought/Response: {part.text}")
                elif part.function_call:
                    print(f"Agent wants to call tool: {part.function_call.name} with args: {part.function_call.args}")
        elif event.is_final_response():
             print(f"\nAgent Final Response: {event.content.parts[0].text if event.content and event.content.parts else 'No response'}")

if __name__ == "__main__":
    asyncio.run(main())
