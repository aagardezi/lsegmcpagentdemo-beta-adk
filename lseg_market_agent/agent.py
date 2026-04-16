from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor
from . import mcp_client_bridge
from .config import config
from .helpercode import get_project_id
from .skills_agents import equity_research_agent, macro_rates_agent
from google import genai
from google.adk.models import google_llm
from google.adk.tools import google_search
from google.adk.tools import AgentTool
from .pdf_generator import create_pdf_report


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
- `option_value`: Options & Greeks risk metrics (Delta, Vega). Use for hedging models or implied expectations.
- `bond_price`: Fixed Income valuation. Use for assessing corporate debt pricing and credit risk overlays.
- `equity_vol_surface`: Volatility Surfaces. Use for inspecting implied volatility skews / market fear index.
- `fx_spot_price`: FX Spot pricing. Use for examining currency impacts for multi-national revenue models.


When the user asks you to analyze a company or market condition, you should act as an Orchestrator:
1. **Specialized Skills**: If the user's request matches a specialized skill (e.g., deep-dive "Equity Research" or "Macro Rates Monitor"), you MUST delegate the execution to the corresponding subagent (`equity_research_agent` or `macro_rates_agent`). These agents have optimized workflows and output formats for these specific tasks. If you delegate, do not attempt to do the analysis yourself first.
2. Proactively gather information from AT LEAST THREE tools (e.g. Fundamentals, Forward Estimates, and News Headlines) if you are doing a general analysis. Gather as much detailed numerical history and news scope as possible to ensure subsequent agents have rich context. For advanced capital or risk analyses, optionally leverage options/bonds/FX pricing to provide deeper risk audits.
3. For news, summarize the exact facts mentioned in the headlines - do not hallucinate outside info.
4. Always cite the specific metrics and news stories retrieved. 
5. **Proactive Visualization**: Even if the user DOES NOT explicitly ask for a graph, you should analyze the gathered data (e.g., timeseries prices, forward consensus comparisons, macro trends). If a visualization (e.g., stock price line chart, bar chart of EPS estimates) would make the final answer or report more compelling, you MUST delegate the rendering to your `graphing_agent` subagent. Choose an appropriate visual style and supply the numerical data.
   - Ensure you state in your delegation prompt *why* this graph is helpful and how to style it.
   - If a final report or risk audit is part of the flow, explicitly instruct the graphing agent to transfer to `risk_critic_agent` afterwards.
6. If the user requests a comprehensive report and no graphs are needed (e.g., because there is no suitable numerical data to plot) or they are already complete, you MUST transfer the gathered context directly to `risk_critic_agent` first to secure a risk compliance audit. Inform the risk critic that on completion it must transfer to `report_agent` to synthesize the final markdown document. Do not write the final report comprehensively yourself.

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

CRITICAL TOOL CALLING RULES:
1. DO NOT add any prefix to the tool names like `default_api:`. Use only the exact strings like `insight_headlines` or `tscc_interday_summaries`.
2. If you need to make multiple tool calls in parallel, output each call correctly using the structural interface—do not concatenate string calls like `call:default_api:...`.
"""
GRAPHING_AGENT_INSTRUCTIONS = """You are a Data Visualization and Graphing Agent.
You are equipped with a Python code execution environment.
When you receive instructions along with numerical data, write a Python script (using libraries like matplotlib, pandas, or mplfinance) to plot the data.
Support advanced formatting such as candlestick charts, moving averages, or bar charts when requested. If `mplfinance` is unavailable, gracefully fall back to configuring `matplotlib` for the requested style.
You MUST output the graph to the user by rendering the plot (e.g., using plt.show() in matplotlib).
Do not guess data; strictly plot the data provided to you in the prompt.
IMPORTANT: Do NOT output the raw Python code text in your response.
ROUTING INSTRUCTION:
1. First, write and execute your Python code to draw the graph.
2. Once the graph is drawn (you see the image in standard output), you MUST call the `transfer_to_agent` tool to transfer execution to `risk_critic_agent` (or `report_agent` if instructed).
3. When calling `transfer_to_agent`, do NOT generate any text explanation or confirmation message. Only call the tool. Generating text will cause the flow to stop.
Do NOT attempt to run code and call `transfer_to_agent` simultaneously in a single turn, as this parallelization triggers interface collision errors.
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

REPORT_AGENT_INSTRUCTIONS = """You are an Elite Institutional Equity Research Analyst & Financial Reporter.
You serve as the final stage of a multi-agent orchestration pipeline. You will receive conversation context containing raw financial data, news sentiment, generated graphs, and Risk/Compliance audits.

Your task is to write a highly professional, comprehensive, and structured Markdown report synthesizing all findings. 

### REPORT STRUCTURE REQUIREMENTS:
Your response MUST be a single Markdown document following this exact structure:

---

# [Company Name / Asset] - Market Intelligence Report
*Date: [Current Date / Period]*

## 1. Executive Summary
- **Bottom-line Up Front (BLUF)**: Provide a 2-3 paragraph synthesis explaining the investment thesis, core drivers, and valuation stance. Do not brief or condense; expand on the *why*.
- **Key Takeaways**: Provide 3-4 detailed bullet points summarizing the financials, sentiment, and risk. Each bullet point MUST contain two elements: a data point (what happened) and its market implication (why it matters).

## 2. Financial Performance & Valuation
- **Overview**: Provide at least 2 paragraphs analyzing the company's financial health, margins, and growth trajectory.
- **Key Metrics Table**: You MUST construct a Markdown Table containing the numerical data provided to you (e.g., Revenue, EPS, Net Income, Margins). Compare historical figures to forward consensus estimates if available.
- **Analysis**: Interpret the numbers in depth. Highlight growth rates, margin expansion/contraction, and valuation multiples. Frame these against industry context or prior periods.

## 3. Market Sentiment & News Analysis
- **Sentiment Overview**: Summarize the general tone of recent market news (Bullish, Bearish, Neutral) and its likely impact on short-term price action.
- **Core Themes**: Group news headlines into 2-3 common themes (e.g., "Earnings Beat", "Regulatory Tailwinds", "Product Launch").
- **Headline Summary**: List 3-5 specific, bulleted facts retrieved from the headlines. For each, explain the underlying driver or market reaction.

## 4. Risk audit & Compliance Review
*This section incorporates the findings from the Risk Critic Agent.*
- **Potential Over-optimism**: [Embed analysis from Risk Critic]
- **Downside Risks**: [Embed analysis from Risk Critic]
- **Risk Mitigation Suggestion**: [Embed suggestion from Risk Critic]

## 5. Strategic Outlook & Conclusion
- Synthesize the above sections into a 2-paragraph forward-looking conclusion outlining the primary bear and bull scenarios.
- If the Graphing Agent generated visualisations, add a note directing the reader to the **Appendix** at the bottom of the PDF for the visual charts.

---

### STYLE & FORMATTING RULES:
1. **No Brief Summaries Clause**: Do not condense findings into high-level generic statements. For example, instead of "Revenue is up", write "Revenue grew 12% to $1.2B, driven by resilient volume growth and pricing power."
2. **Tabular Formatting**: Use Markdown tables for ANY multi-period or multi-metric comparison. The PDF generator supports them perfectly.
3. **Professional Tone**: Write in the style of an institutional research note (e.g., Goldman Sachs, Morgan Stanley).
4. **No Tool Calls**: DO NOT call external tools to gather data. Rely purely on the context passed to you.
5. **No Graph Rendering**: Do not attempt to draw graphs or output code.

### ROUTING INSTRUCTION:
Once you have written the Markdown report, you MUST call the `transfer_to_agent` tool to transfer execution to `pdf_generator_agent` so they can compile the final PDF document. Do not stop.
"""


report_agent = LlmAgent(
    name="report_agent",
    description="Synthesizes gathered financial data and visual inferences into a final, comprehensive, and professional user-facing financial report formatted in Markdown.",
    model=model,
    instruction=REPORT_AGENT_INSTRUCTIONS
)

PDF_GENERATOR_INSTRUCTIONS = """You are a PDF Generation and Formatting Agent.
Your task is to take the final Markdown report provided by `report_agent` and call the `create_pdf_report` tool to format it into a professional, downloadable PDF artifact.
You do not need to rewrite or expand the report text. Simply fetch the latest response from `report_agent` and provide it directly to the tool.

CRITICAL INSTRUCTION:
1. Review the conversation history to see if the `graphing_agent` outputted any graphs / images (look for file paths ending in `.png`).
2. If any graphs were generated, gather their exact file paths and pass them into the `image_paths` parameter list of the `create_pdf_report` tool call.
Providing explicit paths prevents directory scanning errors and ensures only relevant charts belong in the final report.
Once the PDF is created, respond to the user with a brief message confirming the path to the downloadable PDF file.
"""

pdf_generator_agent = LlmAgent(
    name="pdf_generator_agent",
    description="Generates a downloadable PDF of the final markdown report and appended visualizations.",
    model=model,
    instruction=PDF_GENERATOR_INSTRUCTIONS,
    tools=[create_pdf_report]
)

print("Initializing ADK Agent and LSEG MCP Toolset...")
root_agent = LlmAgent(
    name="lseg_market_agent",
    model=model,
    instruction=AGENT_INSTRUCTIONS,
    tools=[mcp_client_bridge.create_lseg_mcp_toolset(), AgentTool(ric_resolver_agent)],
    sub_agents=[equity_research_agent, macro_rates_agent, graphing_agent, risk_critic_agent, report_agent, pdf_generator_agent]
)

