import os
import sys

from src.agents.core.factory import create_ems_agent

try:
    agent = create_ems_agent(include_domain_agents=False)
    for tool in agent.tools:
        print(getattr(tool, "name", str(tool)))
except Exception as e:
    print(f"Error: {e}")
