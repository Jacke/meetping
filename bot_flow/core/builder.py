"""
Fluent API for building declarative bot flows.
"""
from typing import Callable, Optional, Dict, Any, List
from .state import StateNode, Flow, Button, TriggerType, PollingConfig


class StateBuilder:
    """
    Builder for constructing a single state with fluent API.

    Usage:
        state_builder
            .on_command("/start")
            .reply("Hello!")
            .button("Next", goto="next_state")
    """

    def __init__(self, name: str, flow_builder: 'FlowBuilder'):
        self._state = StateNode(name=name)
        self._flow_builder = flow_builder

    def on_command(self, command: str) -> 'StateBuilder':
        """Set trigger to a command (e.g., /start)"""
        self._state.trigger_type = TriggerType.COMMAND
        self._state.trigger_value = command
        return self

    def on_callback(self, pattern: str) -> 'StateBuilder':
        """Set trigger to a callback query pattern"""
        self._state.trigger_type = TriggerType.CALLBACK
        self._state.trigger_value = pattern
        return self

    def on_message(self) -> 'StateBuilder':
        """Set trigger to any text message"""
        self._state.trigger_type = TriggerType.MESSAGE
        return self

    def on_enter(self, func: Callable) -> 'StateBuilder':
        """Set action to execute when entering this state"""
        self._state.on_enter = func
        return self

    def action(self, func: Callable) -> 'StateBuilder':
        """Add an action to execute in this state"""
        self._state.actions.append(func)
        return self

    def reply(self, text: str, **kwargs) -> 'StateBuilder':
        """
        Set message to send to user.

        Args:
            text: Message text (supports template vars like {user.first_name})
            **kwargs: Additional arguments (parse_mode, etc.)
        """
        self._state.message = text
        self._state.message_kwargs = kwargs
        return self

    def button(self, text: str, callback_data: Optional[str] = None,
               goto: Optional[str] = None) -> 'StateBuilder':
        """
        Add inline keyboard button.

        Args:
            text: Button text
            callback_data: Callback data (auto-generated if not provided)
            goto: Target state name
        """
        if callback_data is None:
            # Auto-generate callback_data from text
            callback_data = text.lower().replace(' ', '_')

        self._state.add_button(text, callback_data, goto or "")
        return self

    def transition(self, trigger: Optional[str] = None, to: Optional[str] = None) -> 'StateBuilder':
        """
        Add manual transition.

        Args:
            trigger: Trigger value (callback_data, command, etc.)
            to: Target state name
        """
        if trigger is None and to is not None:
            # Auto transition (no trigger)
            self._state.auto_transition = to
        elif trigger and to:
            self._state.add_transition(trigger, to)
        return self

    def poll(self, check_function: Callable[[Any], bool],
             interval: int = 10) -> 'StateBuilder':
        """
        Enable polling mode for this state.

        The check_function will be called every `interval` seconds.
        Use .on_condition() to define what happens when check returns True.

        Args:
            check_function: Function that returns bool (receives context)
            interval: Polling interval in seconds
        """
        self._state.polling = PollingConfig(
            check_function=check_function,
            interval=interval
        )
        return self

    def on_condition(self, predicate: Callable[[Any], bool],
                     goto: str) -> 'StateBuilder':
        """
        Add conditional transition.

        If this state has polling enabled, this sets the on_true_goto.
        Otherwise, it adds a regular transition with a condition.

        Args:
            predicate: Condition function (receives context)
            goto: Target state if condition is true
        """
        if self._state.polling:
            # Use predicate from polling config, set goto
            self._state.polling.on_true_goto = goto
        else:
            # For non-polling states, add as transition with condition
            # (this would need executor support for runtime condition checking)
            self._state.transitions['condition'] = goto

        return self

    def otherwise(self, goto: str) -> 'StateBuilder':
        """
        Set the fallback transition if polling condition is False.
        Only works if this state has polling enabled.

        Args:
            goto: Target state if condition is false
        """
        if self._state.polling:
            self._state.polling.on_false_goto = goto
        return self

    def final(self) -> 'StateBuilder':
        """Mark this state as final (no transitions out)"""
        self._state.is_final = True
        return self

    def build_state(self) -> StateNode:
        """Build and return the StateNode"""
        return self._state

    # Fluent API - allow chaining back to FlowBuilder
    def state(self, name: str) -> 'StateBuilder':
        """
        Finish current state and start building a new one.
        Returns a new StateBuilder for the next state.
        """
        self._flow_builder._add_state(self._state)
        return self._flow_builder.state(name)

    def build(self) -> Flow:
        """
        Finish current state and build the complete flow.
        Validates the flow and returns it.
        """
        self._flow_builder._add_state(self._state)
        return self._flow_builder.build()


class FlowBuilder:
    """
    Main builder for constructing bot flows.

    Usage:
        flow = (
            FlowBuilder("my_bot")
            .state("welcome")
                .on_command("/start")
                .reply("Hello!")
                .button("Start", goto="next")
            .state("next")
                .reply("Next step")
                .final()
            .build()
        )
    """

    def __init__(self, name: str):
        self._flow = Flow(name=name)
        self._current_state_builder: Optional[StateBuilder] = None

    def state(self, name: str) -> StateBuilder:
        """
        Start building a new state.

        Args:
            name: Unique state name

        Returns:
            StateBuilder for fluent API chaining
        """
        # Save previous state if exists
        if self._current_state_builder:
            self._add_state(self._current_state_builder.build_state())

        self._current_state_builder = StateBuilder(name, self)
        return self._current_state_builder

    def _add_state(self, state: StateNode) -> None:
        """Internal: Add completed state to flow"""
        self._flow.add_state(state)

    def build(self) -> Flow:
        """
        Build and validate the complete flow.

        Returns:
            Validated Flow object

        Raises:
            ValueError: If flow validation fails
        """
        # Add last state if not added yet
        if self._current_state_builder:
            self._add_state(self._current_state_builder.build_state())

        # Validate flow
        errors = self._flow.validate()
        if errors:
            error_msg = "Flow validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)

        return self._flow

    def set_initial_state(self, name: str) -> 'FlowBuilder':
        """
        Explicitly set the initial state.
        By default, the first state added becomes the initial state.

        Args:
            name: Name of the initial state
        """
        self._flow.initial_state = name
        return self


# Convenience function for creating flows
def create_flow(name: str) -> FlowBuilder:
    """
    Create a new flow builder.

    Args:
        name: Flow name

    Returns:
        FlowBuilder instance
    """
    return FlowBuilder(name)
