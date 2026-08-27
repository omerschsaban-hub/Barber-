"""Compatibility exports for the shared engineering operation engine.

The service implementation lives in ``services.engine.operation_engine`` so the
FastAPI and MCP adapters use the same deterministic operation behavior. This
module preserves the historical ``engineering.app.operation_engine`` import
path used by the composed engineering app and contract tests.
"""
from services.engine.operation_engine import *  # noqa: F401,F403
from services.engine.operation_engine import run_tool_operation

__all__ = ["run_tool_operation"]
