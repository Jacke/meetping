"""
Bot Flow - Declarative Telegram Bot Framework

A fluent API for building Telegram bots with automatic flow visualization.
"""
from .state import StateNode, Flow, Button, TriggerType, PollingConfig
from .builder import FlowBuilder, StateBuilder, create_flow
from .executor import FlowExecutor, FlowContext
from .visualizer import FlowVisualizer, visualize

__all__ = [
    # State
    'StateNode',
    'Flow',
    'Button',
    'TriggerType',
    'PollingConfig',

    # Builder
    'FlowBuilder',
    'StateBuilder',
    'create_flow',

    # Executor
    'FlowExecutor',
    'FlowContext',

    # Visualizer
    'FlowVisualizer',
    'visualize',
]

__version__ = '0.1.0'
