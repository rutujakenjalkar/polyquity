# Recommendation Agent Module

from tools.top_ipo_tool import top_ipo_tool
from tools.postgres_tool import get_user_profile
from tools.similarity_tool import similarity_tool
from tools.logger_utils import get_logger, set_run_id
from tools.sentiment_tool import sentiment_tool

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.globals import set_debug
set_debug(False)

logger = get_logger(__name__, "workflow.log")

# 1. Load the Groq key from your .env
load_dotenv()

# 2. Define specialized Advisory tools

@tool
def get_sentiment_scores_tool(candidates_input: str) -> str:
    """Call this tool after get_similar_ipos_tool or get_top_ipos_tool.
    Pass the entire output of either tool as input.
    Fetches market news, scores sentiment using FinBERT and returns 
    ordered candidates with composite scores."""
    logger.info("Tool call started: get_sentiment_scores_tool")
    result = sentiment_tool(candidates_input)
    logger.info("Tool call completed: get_sentiment_scores_tool")
    return result



@tool
def get_user_profile_tool(wallet_address: str) -> str:
    """Always call this tool first with the user's wallet address. 
    Returns whether the user has investment history or not."""
    logger.info("Tool call started: get_user_profile_tool")
    result = get_user_profile(wallet_address)
    logger.info("Tool call completed: get_user_profile_tool")
    return result

@tool
def get_top_ipos_tool(dummy: str = "run") -> str:
    """Call this tool only when get_user_profile_tool returns has_profile as false.
    Returns top 5 IPOs for new users with no investment history."""
    logger.info("Tool call started: get_top_ipos_tool")
    result = top_ipo_tool()
    logger.info("Tool call completed: get_top_ipos_tool")
    return result

@tool
def get_similar_ipos_tool(postgres_tool_output: str) -> str:
    """Call this tool when get_user_profile_tool returns has_profile as true.
    Pass the entire output of get_user_profile_tool as input.
    Returns top 5 similar IPOs based on user investment profile."""
    logger.info("Tool call started: get_similar_ipos_tool")
    result = similarity_tool(postgres_tool_output)
    logger.info("Tool call completed: get_similar_ipos_tool")
    return result

# 3. Initialize Groq (using Llama 3.1 for best tool-calling)
# Updated for March 2026 standards
llm = ChatGroq(
    model="llama-3.3-70b-versatile", # Updated model ID
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)


# 4. Create the Agent
# This replaces the old create_react_agent pattern
tools = [get_user_profile_tool, get_top_ipos_tool, get_similar_ipos_tool,get_sentiment_scores_tool]

advisor_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="You are a Senior Financial Advisor. Be concise, professional, and always use tools for calculations."
)

if __name__ == "__main__":
    
    # 5. Execute the Advisory Task
    user_query = "Give me IPO recommendations for wallet 0x2b3c4d5e6f7890abcdef1234567890abcdef1235"
    run_id = set_run_id()
    logger.info("Starting recommendation workflow for query: %s", user_query)

    # The agent returns a dictionary containing the full message history
    response = advisor_agent.invoke({"messages": [("user", user_query)]})
    logger.info("Recommendation workflow completed")

    # Print only the final answer from the agent (the last message in the history)
    print(response["messages"][-1].content)
    print("done")

    conversation_history = response["messages"]  # full history incl. tool calls

    print("\nType your follow-up questions (or 'exit' to quit):\n")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        conversation_history.append(("user", user_input))
        response = advisor_agent.invoke({"messages": conversation_history})
        conversation_history = response["messages"]  # keep history growing
        print(f"\nAdvisor: {response['messages'][-1].content}\n")
