# Recommendation Agent Module

import os
import json
from dotenv import load_dotenv
from langchain.hub import pull

from langchain.agents import AgentExecutor, create_agent
from langchain_groq import ChatGroq
from langchain_core.tools import tool

from tools.top_ipo_tool import top_ipo_tool
from tools.postgres_tool import get_user_profile

result = top_ipo_tool()
print(result)
print(get_user_profile("0x1234567890abcdef1234567890abcdef12345678"))
#print(AgentExecutor)