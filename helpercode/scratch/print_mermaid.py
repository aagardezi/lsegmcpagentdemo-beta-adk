import asyncio
from dotenv import load_dotenv
load_dotenv()
from lseg_market_agent.agent import root_agent
from google.adk.cli.agent_graph import get_agent_graph

async def main():
    graph_text = await get_agent_graph(root_agent, None)
    print(graph_text)
    
if __name__ == "__main__":
    asyncio.run(main())
