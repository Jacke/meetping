"""
Core state management classes for declarative Telegram bot flows.
"""
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any
from enum import Enum


class TriggerType(Enum):
    """Types of triggers that can activate a state"""
    COMMAND = "command"
    CALLBACK = "callback"
    MESSAGE = "message"
    AUTO = "auto"


@dataclass
class Button:
    """Inline keyboard button with transition"""
    text: str
    callback_data: str
    goto: Optional[str] = None  # Target state name


@dataclass
class Transition:
    """Transition between states"""
    from_state: str
    to_state: str
    trigger: Optional[str] = None  # Command, callback pattern, etc.
    condition: Optional[Callable[[Any], bool]] = None  # Predicate function


@dataclass
class PollingConfig:
    """Configuration for polling-based state checking"""
    check_function: Callable[[Any], bool]
    interval: int = 10  # seconds
    on_true_goto: Optional[str] = None
    on_false_goto: Optional[str] = None
    max_attempts: Optional[int] = None


@dataclass
class StateNode:
    """
    Represents a single state in the bot flow.

    A state can have:
    - Entry actions (executed when entering the state)
    - Messages to send to the user
    - Inline keyboard buttons
    - Transitions to other states
    - Polling configuration for background checks
    """
    name: str

    # Triggers
    trigger_type: Optional[TriggerType] = None
    trigger_value: Optional[str] = None  # e.g., "/start" for commands

    # Actions
    on_enter: Optional[Callable] = None  # Action when entering state
    actions: List[Callable] = field(default_factory=list)  # Sequential actions

    # User interaction
    message: Optional[str] = None  # Message to send
    message_kwargs: Dict[str, Any] = field(default_factory=dict)  # parse_mode, etc.
    buttons: List[Button] = field(default_factory=list)

    # Transitions
    transitions: Dict[str, str] = field(default_factory=dict)  # trigger -> target_state
    auto_transition: Optional[str] = None  # Automatic transition after actions

    # Polling (for async checks like payment confirmation)
    polling: Optional[PollingConfig] = None

    # State properties
    is_final: bool = False

    def add_button(self, text: str, callback_data: str, goto: str) -> 'StateNode':
        """Add an inline keyboard button"""
        self.buttons.append(Button(text, callback_data, goto))
        self.transitions[callback_data] = goto
        return self

    def add_transition(self, trigger: str, goto: str) -> 'StateNode':
        """Add a transition"""
        self.transitions[trigger] = goto
        return self

    def has_transition_to(self, target: str) -> bool:
        """Check if state has transition to target"""
        return target in self.transitions.values() or self.auto_transition == target


@dataclass
class Flow:
    """
    Represents the complete bot flow graph.

    Contains all states and their relationships.
    Provides methods for validation and traversal.
    """
    name: str
    states: Dict[str, StateNode] = field(default_factory=dict)
    initial_state: Optional[str] = None

    def add_state(self, state: StateNode) -> 'Flow':
        """Add a state to the flow"""
        self.states[state.name] = state
        if self.initial_state is None:
            self.initial_state = state.name
        return self

    def get_state(self, name: str) -> Optional[StateNode]:
        """Get state by name"""
        return self.states.get(name)

    def has_state(self, name: str) -> bool:
        """Check if state exists"""
        return name in self.states

    def validate(self) -> List[str]:
        """
        Validate the flow graph.
        Returns list of validation errors.
        """
        errors = []

        # Check initial state exists
        if not self.initial_state:
            errors.append("No initial state defined")
        elif not self.has_state(self.initial_state):
            errors.append(f"Initial state '{self.initial_state}' does not exist")

        # Check all transitions point to valid states
        for state_name, state in self.states.items():
            for trigger, target in state.transitions.items():
                if not self.has_state(target):
                    errors.append(
                        f"State '{state_name}' has transition to non-existent state '{target}'"
                    )

            if state.auto_transition and not self.has_state(state.auto_transition):
                errors.append(
                    f"State '{state_name}' has auto_transition to non-existent state '{state.auto_transition}'"
                )

            if state.polling and state.polling.on_true_goto:
                if not self.has_state(state.polling.on_true_goto):
                    errors.append(
                        f"State '{state_name}' polling on_true_goto points to non-existent state '{state.polling.on_true_goto}'"
                    )

        # Check for unreachable states (except initial and command-triggered states)
        reachable = self._find_reachable_states()
        for state_name in self.states:
            state = self.states[state_name]
            # Command-triggered states are valid entry points and don't need to be reachable
            is_command_entry = state.trigger_type == TriggerType.COMMAND
            if state_name not in reachable and state_name != self.initial_state and not is_command_entry:
                errors.append(f"State '{state_name}' is unreachable")

        return errors

    def _find_reachable_states(self) -> set:
        """Find all states reachable from initial state"""
        if not self.initial_state:
            return set()

        reachable = set()
        to_visit = [self.initial_state]

        while to_visit:
            current = to_visit.pop()
            if current in reachable:
                continue

            reachable.add(current)
            state = self.get_state(current)

            if state:
                # Add transition targets
                for target in state.transitions.values():
                    if target not in reachable:
                        to_visit.append(target)

                # Add auto_transition
                if state.auto_transition and state.auto_transition not in reachable:
                    to_visit.append(state.auto_transition)

                # Add polling transitions
                if state.polling:
                    if state.polling.on_true_goto and state.polling.on_true_goto not in reachable:
                        to_visit.append(state.polling.on_true_goto)
                    if state.polling.on_false_goto and state.polling.on_false_goto not in reachable:
                        to_visit.append(state.polling.on_false_goto)

        return reachable

    def find_path(self, from_state: str, to_state: str) -> Optional[List[str]]:
        """
        Find a path between two states using BFS.
        Returns list of state names or None if no path exists.
        """
        if not self.has_state(from_state) or not self.has_state(to_state):
            return None

        if from_state == to_state:
            return [from_state]

        visited = set()
        queue = [(from_state, [from_state])]

        while queue:
            current, path = queue.pop(0)

            if current in visited:
                continue
            visited.add(current)

            state = self.get_state(current)
            if not state:
                continue

            # Get all possible next states
            next_states = set(state.transitions.values())
            if state.auto_transition:
                next_states.add(state.auto_transition)
            if state.polling:
                if state.polling.on_true_goto:
                    next_states.add(state.polling.on_true_goto)
                if state.polling.on_false_goto:
                    next_states.add(state.polling.on_false_goto)

            for next_state in next_states:
                if next_state == to_state:
                    return path + [next_state]

                if next_state not in visited:
                    queue.append((next_state, path + [next_state]))

        return None
