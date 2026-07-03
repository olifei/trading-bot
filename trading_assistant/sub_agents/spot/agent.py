from google.adk.agents import Agent
from google.genai import types

from trading_assistant import prompt
from trading_assistant import config
from trading_assistant.tools.compliance import kyc_compliance_check, region_compliance_check, trade_params_compliance_check
from trading_assistant.tools.memory import load_user_profile

from trading_assistant.services.portfolio.portfolio_tool import create_get_portfolio_tool
from trading_assistant.services.market.market_tool import create_market_price_tool
from trading_assistant.services.utils.calculator_tool import create_calculator_tool
from trading_assistant.sub_agents.spot.tools import spot_order_tool


def create_spot_agent():
    portfolio_tool = create_get_portfolio_tool()
    market_price_tool = create_market_price_tool()
    calculator_tool = create_calculator_tool()
    
    spot_agent = Agent(
        model=config.SPOT_AGENT_CONFIG["model"],
        name="spot_agent",
        description="Specialized agent for handling spot trading (buy/sell cryptocurrencies)",
        instruction=prompt.SPOT_AGENT_INSTR,
        tools=[
            portfolio_tool,
            market_price_tool,
            spot_order_tool,
            calculator_tool
        ],
        before_agent_callback=load_user_profile,
        before_model_callback=[kyc_compliance_check, region_compliance_check],
        before_tool_callback=trade_params_compliance_check,
        generate_content_config=types.GenerateContentConfig(
            temperature=config.SPOT_AGENT_CONFIG["temperature"],
            max_output_tokens=config.SPOT_AGENT_CONFIG.get("max_output_tokens"),
            top_p=config.SPOT_AGENT_CONFIG.get("top_p"),
            top_k=config.SPOT_AGENT_CONFIG.get("top_k"),
        )
    )
    
    return spot_agent
