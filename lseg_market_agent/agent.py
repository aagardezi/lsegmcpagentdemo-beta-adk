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
4. **Proactive Visualization**: Even if the user DOES NOT explicitly ask for a graph, you should analyze the gathered data (e.g., timeseries prices, forward consensus comparisons, macro trends). If a visualization (e.g., stock price line chart, bar chart of EPS estimates) would make the final answer or report more compelling, you MUST delegate the rendering to your `graphing_agent` subagent. Choose an appropriate visual style and supply the numerical data.
   - Ensure you state in your delegation prompt *why* this graph is helpful and how to style it.
   - If a final report or risk audit is part of the flow, explicitly instruct the graphing agent to transfer to `risk_critic_agent` afterwards.
5. If the user requests a comprehensive report and no graphs are needed (e.g., because there is no suitable numerical data to plot) or they are already complete, you MUST transfer the gathered context directly to `risk_critic_agent` first to secure a risk compliance audit. Inform the risk critic that on completion it must transfer to `report_agent` to synthesize the final markdown document. Do not write the final report comprehensively yourself.

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
ROUTING INSTRUCTION: If the orchestrator instructed you to pass control to an auditor/reviewer after graphing, you MUST call the `transfer_to_agent` tool to transfer execution to `risk_critic_agent` once you have displayed the plot. If explicitly told to go to report writer, transfer to `report_agent`.
"""

graphing_agent = LlmAgent(
    name="graphing_agent",
    description="Draws financial graphs, plots, and visualizes data using python.",
    model=model,
    instruction=GRAPHING_AGENT_INSTRUCTIONS,
    code_executor=BuiltInCodeExecutor()
)

RISK_CRITIC_AGENT_INSTRUCTIONS = """You are a Risk Management & Compliance Auditor.
Your task is to review the financial data, sentiment, and initial thesis components provided by the orchestrator.
Analyze the context strictly for:
1. **Downside Risks**: Are there ignored macroeconomic headwinds (e.g., inflation spikes, GDP decelerating)? Are there company-specific risks (e.g., historical EPS slowdown)?
2. **Over-optimism**: Is the forward consensus forecast or news sentiment overly bullish compared to hard historical metrics?
3. **Risk Mitigation Suggestion**: Briefly suggest a risk mitigation or hedging strategy (e.g., "Consider downside protection puts if sizing long positions").

OUTPUT FORMAT:
Your response MUST be structured with these exact headers:
- **Potential Over-optimism**: [Analysis]
- **Downside Risks**: [Analysis]
- **Risk Mitigation Suggestion**: [Analysis]

Do not write a full, comprehensive narrative report. Provide a concise auditing note back.
ROUTING INSTRUCTION: Once you have provided your audited risk points, you MUST call the `transfer_to_agent` tool to transfer execution to `report_agent` so they can compile the final markdown document.
"""

risk_critic_agent = LlmAgent(
    name="risk_critic_agent",
    description="Audits financial analyses for over-optimism, missed macro/spread risks, and suggests risk mitigation hedging notes.",
    model=model,
    instruction=RISK_CRITIC_AGENT_INSTRUCTIONS
)

REPORT_AGENT_INSTRUCTIONS = """You are a professional Financial Reporter.
You serve as the final stage of a multi-agent orchestration pipeline. You will receive conversation context containing raw financial data, news sentiment, generated graphs, and Risk/Compliance audits.
Your task is to write a highly professional, comprehensive, final Markdown report synthesizing all findings.
Include sections such as Executive Summary, Financial Performance, Market Sentiment, Risk Analysis & Audit, and Conclusion where applicable. For the Risk section, integrate the auditing notes provided by the risk critic agent.
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
    sub_agents=[graphing_agent, risk_critic_agent, report_agent]
)
