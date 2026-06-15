import unittest
from unittest.mock import patch, MagicMock

# Create a mock response for requests.post
mock_response = MagicMock()
mock_response.json.return_value = {"access_token": "dummy_token", "expires_in": 7200}
mock_response.status_code = 200

# Patch requests.post globally before importing agent
with patch("requests.post", return_value=mock_response) as mock_post:
    from lseg_market_agent.agent import root_agent

def test_agent_structure() -> None:
    assert root_agent.name == "lseg_market_agent"
    assert len(root_agent.sub_agents) == 4
    
    # Verify that the instruction string does not contain legacy tool names
    instructions = root_agent.instruction
    assert "tscc_interday_summaries" not in instructions
    assert "historical_pricing_summaries" in instructions

def test_historical_pricing_summaries_parameters() -> None:
    instructions = root_agent.instruction
    # Assert instructions explain how to structure parameters for historical_pricing_summaries
    assert "universe" in instructions
    assert "startDate" in instructions
    assert "endDate" in instructions
    assert "YYYY-MM-DD" in instructions

def test_root_agent_domain_coverage() -> None:
    instructions = root_agent.instruction
    
    # Equity Research
    assert "qa_company_fundamentals" in instructions
    assert "qa_ibes_consensus" in instructions
    assert "important_company_news" in instructions or "insight_headlines" in instructions
    assert "option_value" in instructions
    assert "equity_vol_surface" in instructions
    
    # Fixed Income & Credit Audits
    assert "fixed_income_bond_reference" in instructions
    assert "fixed_income_risk_analytics" in instructions
    assert "interest_rate_curve" in instructions
    assert "inflation_curve" in instructions
    assert "credit_curve" in instructions
    
    # FX & Currency Hedging
    assert "fx_spot_price" in instructions
    assert "fx_forward_curve" in instructions
    assert "fx_forward_price" in instructions
    assert "fx_event_tracker" in instructions
    
    # FTSE Index Benchmarking (IXM)
    assert "ixm_list_indexes" in instructions
    assert "ixm_compare_index_return_time_series" in instructions
    assert "ixm_index_risk_time_series" in instructions
    assert "ixm_index_sector_risk" in instructions

def test_graphing_agent_instructions() -> None:
    graphing_subagent = next(a for a in root_agent.sub_agents if a.name == "graphing_agent")
    instr = graphing_subagent.instruction
    
    # Assert yield curves, index return comparisons, implied volatility surfaces are covered
    assert "interest_rate_curve" in instr
    assert "ixm_compare_index_return_time_series" in instr
    assert "equity_vol_surface" in instr

def test_risk_critic_agent_instructions() -> None:
    risk_critic_subagent = next(a for a in root_agent.sub_agents if a.name == "risk_critic_agent")
    instr = risk_critic_subagent.instruction
    
    # Assert audit duration/convexity mismatches, credit default curves risk, currency hedging costs
    assert "duration/convexity mismatch" in instr or "duration/convexity" in instr
    assert "credit default curve" in instr or "credit_curve" in instr
    assert "currency hedging cost" in instr or "hedging cost" in instr

def test_report_agent_instructions() -> None:
    report_subagent = next(a for a in root_agent.sub_agents if a.name == "report_agent")
    instr = report_subagent.instruction
    
    # Assert report template contains dedicated sections
    assert "Credit & Debt Overlays" in instr
    assert "Currency Hedging Analysis" in instr
    assert "Benchmark Performance (IXM)" in instr
