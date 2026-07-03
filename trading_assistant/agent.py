from google.adk.agents import Agent
from google.genai import types

from trading_assistant import prompt
from trading_assistant import config
from trading_assistant.tools.memory import load_user_profile
from trading_assistant.tools.compliance import kyc_compliance_check
from trading_assistant.tools.compaction import compact_history
from trading_assistant.observability.callbacks import log_user_intent, log_agent_outcome

from trading_assistant.sub_agents.spot.agent import create_spot_agent
from trading_assistant.sub_agents.portfolio.agent import create_portfolio_agent
from trading_assistant.sub_agents.market_data.agent import create_market_data_agent
from trading_assistant.sub_agents.convert.agent import create_convert_agent



spot_agent = create_spot_agent()
portfolio_agent = create_portfolio_agent()
market_data_agent = create_market_data_agent()
convert_agent = create_convert_agent()

root_agent = Agent(
    model=config.ROOT_AGENT_CONFIG["model"],
    name="trading_assistant",
    description="Trading assistant handling various trading requests",
    instruction=prompt.ROOT_AGENT_INSTR,
    sub_agents=[
        spot_agent,
        convert_agent,
        portfolio_agent,
        market_data_agent,
    ],
    before_agent_callback=load_user_profile,
    before_model_callback=[compact_history, kyc_compliance_check, log_user_intent],
    after_agent_callback=log_agent_outcome,
    generate_content_config=types.GenerateContentConfig(
        temperature=config.ROOT_AGENT_CONFIG["temperature"],
        max_output_tokens=config.ROOT_AGENT_CONFIG.get("max_output_tokens"),
        top_p=config.ROOT_AGENT_CONFIG.get("top_p"),
        top_k=config.ROOT_AGENT_CONFIG.get("top_k"),
    ),
)
