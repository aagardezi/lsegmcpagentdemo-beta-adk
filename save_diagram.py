import asyncio
from dotenv import load_dotenv
load_dotenv()

from lseg_market_agent.agent import root_agent
from google.adk.cli.agent_graph import get_agent_graph

async def main():
    png_bytes = await get_agent_graph(root_agent, None, image=True)
    with open("agent_diagram.png", "wb") as f:
        f.write(png_bytes)
    print("Graph saved to agent_diagram.png")
    
if __name__ == "__main__":
    asyncio.run(main())
