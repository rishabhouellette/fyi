"""Compatibility shim for scheduler engine legacy import path."""

from backend.services.scheduler_engine import SchedulerEngine, get_scheduler_engine  # noqa: F401

engine = get_scheduler_engine()

__all__ = ["SchedulerEngine", "engine", "get_scheduler_engine"]
