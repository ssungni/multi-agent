"""Lecture 04: BaseAgent implementation - Agentic Loop.

This package contains the core implementation of the agent system:
- BaseAgent: Core agent loop with LLM and tool execution
- MaxIterationError: Exception for max iteration exceeded
- BaseAgentState: State management model for agents
- BaseTool: Abstract base class for agent tools
- ToolResult: Result schema for tool execution

These components form the foundation for building LLM-based agents with
tool integration, state management, and the agentic loop pattern.
"""

from lec04_01_base_agent.base import BaseAgent, MaxIterationError
from lec04_01_base_agent.state import BaseAgentState, TState
from lec04_01_base_agent.tool import BaseTool, ToolResult

__all__ = [
    "BaseAgent",
    "MaxIterationError",
    "BaseAgentState",
    "TState",
    "BaseTool",
    "ToolResult",
]
