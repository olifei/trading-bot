from google.adk.agents import Agent
from google.adk.tools import preload_memory
from google.genai import types

from trading_assistant import prompt
from trading_assistant import config
from trading_assistant.services.market.market_tool import create_market_price_tool, create_exchange_rate_tool
from trading_assistant.services.utils.calculator_tool import create_calculator_tool
from trading_assistant.observability.callbacks import log_user_intent, log_tool_call, log_tool_result, log_agent_outcome


def create_market_data_agent():
    market_price_tool = create_market_price_tool()
    exchange_rate_tool = create_exchange_rate_tool()
    calculator_tool = create_calculator_tool()
    
    market_data_agent = Agent(
        model=config.MARKET_DATA_AGENT_CONFIG["model"],
        name="market_data_agent",
        description="Provides market price and exchange rate queries",
        instruction=prompt.MARKET_DATA_AGENT_INSTR,
        tools=[
            market_price_tool,
            exchange_rate_tool,
            calculator_tool,
            preload_memory
        ],
        before_model_callback=log_user_intent,
        before_tool_callback=log_tool_call,
        after_tool_callback=log_tool_result,
        after_agent_callback=log_agent_outcome,
        generate_content_config=types.GenerateContentConfig(
            temperature=config.MARKET_DATA_AGENT_CONFIG["temperature"],
            max_output_tokens=config.MARKET_DATA_AGENT_CONFIG.get("max_output_tokens"),
            top_p=config.MARKET_DATA_AGENT_CONFIG.get("top_p"),
            top_k=config.MARKET_DATA_AGENT_CONFIG.get("top_k"),
        ),
    )
    
    return market_data_agent
