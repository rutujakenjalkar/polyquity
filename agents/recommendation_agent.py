# Recommendation Agent Module


import os
from dotenv import load_dotenv
load_dotenv()



from tools.top_ipo_tool import top_ipo_tool
from tools.postgres_tool import get_user_profile
from tools.similarity_tool import similarity_tool
from tools.logger_utils import get_logger, set_run_id
from tools.sentiment_tool import sentiment_tool
from tools.news_tool import news_tool
from tools.cache import news_cache

from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.globals import set_debug
from tools.prospectus_tool import get_prospectus_answer
from tools.filter import cap_size_filter_tool
set_debug(False)

logger = get_logger(__name__, "workflow.log")
cap_size_tool_logger = get_logger("cap_size_tool_wrapper", "get_ipos_by_cap_size_tool.log")

# 1. Load the Groq key from your .env


# 2. Define specialized Advisory tools


@tool
def get_ipos_by_cap_size_tool(cap_size: str) -> str:
    """Use this tool when user asks about Large cap, Mid cap or Small cap IPOs.
    Input should be 'Large', 'Mid' or 'Small'.
    Returns list of IPOs filtered by market cap size."""
    cap_size_tool_logger.info(
        "Tool call started: get_ipos_by_cap_size_tool with cap_size=%s",
        cap_size,
    )
    try:
        result = cap_size_filter_tool(cap_size)
        cap_size_tool_logger.info("Tool call completed: get_ipos_by_cap_size_tool")
        return result
    except Exception:
        cap_size_tool_logger.exception(
            "Tool call failed: get_ipos_by_cap_size_tool with cap_size=%s",
            cap_size,
        )
        raise

@tool
def get_latest_news_tool(company_name: str) -> str:
    """Use this tool to fetch the absolute latest market news for a specific company.
    This should be used to provide real-time context and recent developments 
    (like leadership changes, earnings, or market sentiment).
    Input should be the simple company name."""
    logger.info(f"Tool call started: get_latest_news_tool for {company_name}")
    # Assuming news_tool takes the company name and returns a string of headlines/summaries
    result = news_tool(company_name) 
    logger.info("Tool call completed: get_latest_news_tool")
    return result

@tool
def get_prospectus_info_tool(query: str) -> str:
    """Use this tool when the user asks questions about a specific IPO company's 
    prospectus document. For example: risk factors, business model, promoters, 
    financial details, objects of the issue, lot size, price band, or any other 
    information found in the DRHP document.
    Pass the user's question directly as input."""
    logger.info("Tool call started: get_prospectus_info_tool")
    result = get_prospectus_answer(query)
    logger.info("Tool call completed: get_prospectus_info_tool")
    return result

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
tools = [get_user_profile_tool, get_top_ipos_tool, get_similar_ipos_tool,get_sentiment_scores_tool,get_prospectus_info_tool,get_latest_news_tool,get_ipos_by_cap_size_tool]

advisor_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""You are a Senior Financial Advisor specializing in IPO investments.

Follow this workflow:
1. Always call get_user_profile_tool first with the wallet address
2. If has_profile is true call get_similar_ipos_tool, if false call get_top_ipos_tool
3. Always call get_sentiment_scores_tool after step 2
4. After getting recommendations, for each recommended IPO:
   - Use get_prospectus_info_tool to get key facts about the company
   - Use the news_tool to find recent market news about the company
   - Combine this information to explain the ranking of each IPO in plain English give very specific reasons based on company fundamentals and news.
   - Explain in 3-4 sentences why this IPO is ranked where it is
5. Present final recommendations with clear reasoning in plain English and Company wise points along with there reason
    eg : 1. Amazon:
            -Amazon is heavily investing in AI infrastructure, with AWS launching new AI models and chips (Nova, Trainium) while forming a strategic partnership with OpenAI.
            - Amazon is cutting 16,000 jobs as part of a cost-cutting effort.
         2. Lockheed Martin
            -Production Surge: Lockheed Martin is quadrupling production of the Precision Strike Missile (PrSM) in collaboration with the Department of Defense.
            -Lockheed Martin appointed Jenna McMullin as Senior Vice President and Chief Communications Officer.

6.Also whenever information related to prospectus or news give point wise information.
 
Rules:
- Never mention technical terms like vectors, scores, distances or composite scores
- Explain rankings using business facts, market news and company fundamentals
- Sound like a professional financial advisor, not a data scientist
- Keep each company explanation concise — 2-3 sentences maximum

7.When using the get_ipos_by_cap_size_tool tool just give the the company names industry and their market capitialization nothing else
eg-Asians Paints
   -Market Capitalization:20 crores
   -Paint Industry"""


)

if __name__ == "__main__":
    print("RUNNING ..........")
    # 5. Execute the Advisory Task
    user_query = "Give me IPO recommendations for wallet 0xDEADAFFE1234567890ABCDEF1234567890ABCDEF"
    run_id = set_run_id()
    logger.info("Starting recommendation workflow for query: %s", user_query)
    print("GETTING RESPONSE")
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
        conversation_history = response["messages"] # keep history growing
        print(f"\nAdvisor: {response['messages'][-1].content}\n")
