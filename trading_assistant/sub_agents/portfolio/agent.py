from google.adk.agents import Agent
from google.genai import types

from trading_assistant import prompt
from trading_assistant import config
from trading_assistant.tools.memory import load_user_profile

from trading_assistant.services.portfolio.portfolio_tool import create_get_portfolio_tool
from trading_assistant.services.market.market_tool import create_market_price_tool
from trading_assistant.services.utils.calculator_tool import create_calculator_tool


def create_portfolio_agent():
    portfolio_tool = create_get_portfolio_tool()
    market_price_tool = create_market_price_tool()
    calculator_tool = create_calculator_tool()
    
    portfolio_agent = Agent(
        model=config.PORTFOLIO_AGENT_CONFIG["model"],
        name="portfolio_agent",
        description="Handles portfolio queries",
        instruction=prompt.PORTFOLIO_AGENT_INSTR,
        tools=[
            portfolio_tool,
            market_price_tool,
            calculator_tool
        ],
        before_agent_callback=load_user_profile,
        generate_content_config=types.GenerateContentConfig(
            temperature=config.PORTFOLIO_AGENT_CONFIG["temperature"],
            max_output_tokens=config.PORTFOLIO_AGENT_CONFIG.get("max_output_tokens"),
            top_p=config.PORTFOLIO_AGENT_CONFIG.get("top_p"),
            top_k=config.PORTFOLIO_AGENT_CONFIG.get("top_k"),
        ),
    )
    
    return portfolio_agent
