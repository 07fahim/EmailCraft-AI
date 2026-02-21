"""
Unit tests for AI agents
"""
import pytest
from agents.planner_agent import PlannerAgent
from agents.generation_agent import GenerationAgent


def test_planner_agent_initialization():
    """Test planner agent can be initialized."""
    agent = PlannerAgent()
    assert agent is not None


def test_generation_agent_initialization():
    """Test generation agent can be initialized."""
    agent = GenerationAgent()
    assert agent is not None


# Add more tests as needed
