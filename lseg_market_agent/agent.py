from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor
from . import mcp_client_bridge
from .config import config
from .helpercode import get_project_id
from google import genai
from google.adk.models import google_llm
from google.adk.tools import google_search
from google.adk.tools import AgentTool

api_client = genai.Client(
    vertexai=True,
    project=get_project_id(),
    location="global"
)
model = google_llm.Gemini(model=config.gemini_model)
model.api_client= api_client 


RIC_RESOLVER_INSTRUCTION = (
    "You are a stock RIC Code or Symbol resolver. "
    "When given a company name, use google_search to find its official stock RIC Code and Symbol "
    "Search for '<company name> stock RIC Code and Symbol site:finance.yahoo.com OR site:google.com/finance'. "
    "Return only the RIC Code and Symbol as plain text so that it can be used in other tools."
    "Do not include any explanation"
)

ric_resolver_agent = LlmAgent(
    model=model,
    name="ric_resolver",
    description="Resolves a company name to its stock RIC Code and Symbol using Google Search.",
    instruction=RIC_RESOLVER_INSTRUCTION,
    tools=[google_search],
)

AGENT_INSTRUCTIONS = """You are a highly capable Cross-Asset Market Intelligence & Valuation Agent for LSEG.
Your objective is to provide a comprehensive, multi-modal analysis of companies and macroeconomic conditions by synthesizing data from the LSEG MCP server.

You have access to a rich set of financial tools:
- `insight_headlines`: Use this to get news sentiment. IMPORTANT: Companies MUST be specified with their RIC (e.g. AAPL.O).
- `qa_company_fundamentals`: Use this for historical financials. Provide the `identifier` (e.g., 'AAPL' or 'Apple').
- `qa_ibes_consensus`: Fetch forward-looking consensus estimates. Provide the `ticker` as just the symbol (e.g., 'AAPL') and a request type.
- `qa_macroeconomic`: Fetch generic macro data like GDP, CPI, or unemployment. First use `list` to find the mnemonic, then `latest` or `series`.
- `tscc_interday_summaries`: To retrieve stock price action.

When the user asks you to analyze a company or market condition, you should act as an Orchestrator:
1. Proactively gather information from AT LEAST THREE tools (e.g. Fundamentals, Forward Estimates, and News Headlines).
2. For news, summarize the exact facts mentioned in the headlines - do not hallucinate outside info.
3. Always cite the specific metrics and news stories retrieved. 
4. If the user asks for a chart, graph, plot, or visual representation, you MUST delegate the rendering to your `graphing_agent` subagent. Choose an appropriate visual style based on the request (bar chart, candlestick, etc.) and supply formatting instructions alongside the numerical data. If a final comprehensive report is also requested, explicitly instruct the graphing agent to transfer to `report_agent` when it finishes.
5. If the user requests a comprehensive report and no graphs are requested (or they are already complete), transfer the gathered context directly to `report_agent` to synthesize the final markdown document. Do not write the final report comprehensively yourself.

IMPORTANT CONSTRAINTS: 
1. `qa_company_fundamentals` REQUIRES strict parameter formatting:
   - `identifier`: Use a ticker (e.g., "AMZN"), RIC (e.g., "AMZN.O"), or company name (e.g., "Amazon"). If a specific format (like a RIC) returns a "No matching company found" error, automatically retry with the plain ticker or the full company name.
   - `measures`: Must be a single COMMA-SEPARATED STRING of numerical measure IDs (e.g., "1001,1100,5201"), NOT names like "EPS".
   - `dataType`: Use "qa_fundamentals_measures" first to look up the available numerical measure IDs. Then use "qa_company_fundamentals" to get the actual fundamental data.
   - `year`: The parameter is named EXACTLY `year` (not `years`), and must be provided (e.g., 2022).
   - `freq`: This is a mandatory field (e.g., "A" for Annual, "Q" for Quarterly).
2. `qa_ibes_consensus` formatting:
   - `ticker`: Must be the plain ticker (e.g., "AAPL"), NOT the RIC format.
   - `measures`: Must be an ARRAY of strings (e.g., ["Eps", "Rev"]), not a comma-separated string.
   - `periodIndexStart`: This is a mandatory integer field (use 1 for forward estimates, 0 for latest).
3. `tscc_interday_summaries` formatting:
   - `universe`: Must be the RIC format (e.g., "AAPL.O").
4. `insight_headlines` uses `rics` for companies (AAPL.O), not plain `query`.
5. Do not guess DataStream Mnemonics for macro data, search them first using `qa_macroeconomic` list tool!
"""
GRAPHING_AGENT_INSTRUCTIONS = """You are a Data Visualization and Graphing Agent.
You are equipped with a Python code execution environment.
When you receive instructions along with numerical data, write a Python script (using libraries like matplotlib, pandas, or mplfinance) to plot the data.
Support advanced formatting such as candlestick charts, moving averages, or bar charts when requested. If `mplfinance` is unavailable, gracefully fall back to configuring `matplotlib` for the requested style.
You MUST output the graph to the user by rendering the plot (e.g., using plt.show() in matplotlib).
Do not guess data; strictly plot the data provided to you in the prompt.
IMPORTANT: Do NOT output the raw Python code text in your response. Only output a brief confirming message (e.g., "Here is the graph") alongside the actual plotted image.
ROUTING INSTRUCTION: If the orchestrator instructed you to pass control to a report writer after graphing, you MUST call the `transfer_to_agent` tool to transfer execution to `report_agent` once you have displayed the plot.
"""

graphing_agent = LlmAgent(
    name="graphing_agent",
    description="Draws financial graphs, plots, and visualizes data using python.",
    model=model,
    instruction=GRAPHING_AGENT_INSTRUCTIONS,
    code_executor=BuiltInCodeExecutor()
)

REPORT_AGENT_INSTRUCTIONS = """You are a professional Financial Reporter.
You serve as the final stage of a multi-agent orchestration pipeline. You will receive conversation context containing raw financial data, news sentiment, and notifications about generated graphs.
Your task is to write a highly professional, comprehensive, final Markdown report synthesizing all findings.
Include sections such as Executive Summary, Financial Performance, Market Sentiment, and Conclusion where applicable.
DO NOT call external tools to gather data. Rely purely on the data passed to you from the orchestrator and other agents. Do not attempt to draw graphs yourself.
"""

report_agent = LlmAgent(
    name="report_agent",
    description="Synthesizes gathered financial data and visual inferences into a final, comprehensive, and professional user-facing financial report formatted in Markdown.",
    model=model,
    instruction=REPORT_AGENT_INSTRUCTIONS
)

print("Initializing ADK Agent and LSEG MCP Toolset...")
root_agent = LlmAgent(
    name="lseg_market_agent",
    model=model,
    instruction=AGENT_INSTRUCTIONS,
    tools=[mcp_client_bridge.create_lseg_mcp_toolset(), AgentTool(ric_resolver_agent)],
    sub_agents=[graphing_agent, report_agent]
)
