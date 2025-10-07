"""
Flow visualization utilities for generating diagrams.
"""
from typing import List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .state import Flow, StateNode
else:
    try:
        from .state import Flow, StateNode
    except ImportError:
        # When imported standalone, these will be injected
        Flow = None  # type: ignore
        StateNode = None  # type: ignore


class FlowVisualizer:
    """
    Generates visual representations of bot flows.

    Supports:
    - Mermaid diagrams (markdown-compatible)
    - GraphViz DOT format
    - ASCII art (simple text representation)
    """

    def __init__(self, flow: Flow):
        self.flow = flow

    def to_mermaid(self, diagram_type: str = "stateDiagram-v2") -> str:
        """
        Generate Mermaid diagram code.

        Args:
            diagram_type: "stateDiagram-v2" or "graph TD" (flowchart)

        Returns:
            Mermaid diagram as string
        """
        if diagram_type == "stateDiagram-v2":
            return self._to_mermaid_state_diagram()
        else:
            return self._to_mermaid_flowchart()

    def _to_mermaid_state_diagram(self) -> str:
        """Generate Mermaid state diagram"""
        lines = ["stateDiagram-v2"]

        # Add initial state marker
        if self.flow.initial_state:
            lines.append(f"    [*] --> {self.flow.initial_state}")

        # Add states and transitions
        for state_name, state in self.flow.states.items():
            # Add transitions
            for trigger, target in state.transitions.items():
                label = self._format_trigger_label(trigger, state)
                lines.append(f"    {state_name} --> {target}: {label}")

            # Add auto transitions
            if state.auto_transition:
                lines.append(f"    {state_name} --> {state.auto_transition}: auto")

            # Add polling transitions
            if state.polling:
                if state.polling.on_true_goto:
                    lines.append(
                        f"    {state_name} --> {state.polling.on_true_goto}: "
                        f"check passed ({state.polling.interval}s)"
                    )
                # Self-loop for polling
                lines.append(f"    {state_name} --> {state_name}: polling...")

            # Mark final states
            if state.is_final:
                lines.append(f"    {state_name} --> [*]")

            # Add state notes for actions
            if state.actions:
                action_names = [f.__name__ for f in state.actions]
                note = "\\n".join(action_names)
                lines.append(f"    note right of {state_name}")
                lines.append(f"        Actions:\\n{note}")
                lines.append(f"    end note")

        return "\n".join(lines)

    def _to_mermaid_flowchart(self) -> str:
        """Generate Mermaid flowchart"""
        lines = ["graph TD"]

        # Add initial state
        if self.flow.initial_state:
            lines.append(f"    START([Start]) --> {self.flow.initial_state}")

        # Add states and transitions
        for state_name, state in self.flow.states.items():
            # State node (shape based on type)
            if state.is_final:
                shape_start, shape_end = "([", "])"
            elif state.polling:
                shape_start, shape_end = "{", "}"  # Diamond for decision
            else:
                shape_start, shape_end = "[", "]"  # Rectangle

            node_label = f"{state_name}{shape_start}{state.name}{shape_end}"

            # Transitions
            for trigger, target in state.transitions.items():
                label = self._format_trigger_label(trigger, state)
                lines.append(f"    {state_name} -->|{label}| {target}")

            # Auto transition
            if state.auto_transition:
                lines.append(f"    {state_name} --> {state.auto_transition}")

            # Polling
            if state.polling:
                if state.polling.on_true_goto:
                    lines.append(
                        f"    {state_name} -->|check passed| {state.polling.on_true_goto}"
                    )
                lines.append(f"    {state_name} -->|wait {state.polling.interval}s| {state_name}")

            # Final states
            if state.is_final:
                lines.append(f"    {state_name} --> END([End])")

        return "\n".join(lines)

    def _format_trigger_label(self, trigger: str, state: StateNode) -> str:
        """Format trigger for display"""
        # Check if it's a button callback
        for btn in state.buttons:
            if btn.callback_data == trigger:
                return f"click '{btn.text}'"

        # Check if it's a command
        if state.trigger_value and state.trigger_value.startswith('/'):
            return state.trigger_value

        return trigger

    def to_graphviz(self) -> str:
        """
        Generate GraphViz DOT format.

        Returns:
            DOT format string
        """
        lines = ['digraph BotFlow {']
        lines.append('    rankdir=TB;')
        lines.append('    node [shape=box, style=rounded];')
        lines.append('')

        # Add initial state
        lines.append('    START [label="Start", shape=circle, style=filled, fillcolor=green];')
        if self.flow.initial_state:
            lines.append(f'    START -> {self.flow.initial_state};')

        # Add states
        for state_name, state in self.flow.states.items():
            # State styling
            if state.is_final:
                style = 'shape=doublecircle, style=filled, fillcolor=lightblue'
            elif state.polling:
                style = 'shape=diamond, style=filled, fillcolor=yellow'
            else:
                style = 'shape=box, style="rounded,filled", fillcolor=lightgray'

            label = state.name
            if state.message:
                # Truncate message for label
                msg_preview = state.message[:30].replace('\n', ' ').replace('"', '\\"')
                label += f'\\n"{msg_preview}..."'

            lines.append(f'    {state_name} [label="{label}", {style}];')

            # Transitions
            for trigger, target in state.transitions.items():
                label = self._format_trigger_label(trigger, state)
                lines.append(f'    {state_name} -> {target} [label="{label}"];')

            # Auto transition
            if state.auto_transition:
                lines.append(f'    {state_name} -> {state.auto_transition} [style=dashed];')

            # Polling
            if state.polling:
                if state.polling.on_true_goto:
                    lines.append(
                        f'    {state_name} -> {state.polling.on_true_goto} '
                        f'[label="check passed", color=green];'
                    )
                lines.append(
                    f'    {state_name} -> {state_name} '
                    f'[label="poll {state.polling.interval}s", color=gray, style=dashed];'
                )

        lines.append('}')
        return '\n'.join(lines)

    def to_ascii(self) -> str:
        """
        Generate simple ASCII art representation.

        Returns:
            ASCII diagram as string
        """
        lines = [f"Flow: {self.flow.name}"]
        lines.append("=" * 50)

        if self.flow.initial_state:
            lines.append(f"START -> {self.flow.initial_state}")
            lines.append("")

        for state_name, state in self.flow.states.items():
            lines.append(f"[{state_name}]")

            if state.trigger_value:
                lines.append(f"  Trigger: {state.trigger_value}")

            if state.message:
                msg_preview = state.message[:50].replace('\n', ' ')
                lines.append(f"  Message: {msg_preview}...")

            if state.buttons:
                lines.append(f"  Buttons:")
                for btn in state.buttons:
                    lines.append(f"    - {btn.text} -> {btn.goto}")

            if state.actions:
                action_names = [f.__name__ for f in state.actions]
                lines.append(f"  Actions: {', '.join(action_names)}")

            if state.transitions:
                lines.append(f"  Transitions:")
                for trigger, target in state.transitions.items():
                    lines.append(f"    {trigger} -> {target}")

            if state.auto_transition:
                lines.append(f"  Auto -> {state.auto_transition}")

            if state.polling:
                lines.append(f"  Polling: every {state.polling.interval}s")
                if state.polling.on_true_goto:
                    lines.append(f"    -> {state.polling.on_true_goto} (on success)")

            if state.is_final:
                lines.append(f"  [FINAL]")

            lines.append("")

        return "\n".join(lines)

    def export_mermaid(self, filepath: str, diagram_type: str = "stateDiagram-v2") -> None:
        """
        Export Mermaid diagram to a markdown file.

        Args:
            filepath: Output file path (.md)
            diagram_type: Diagram type
        """
        diagram = self.to_mermaid(diagram_type)

        with open(filepath, 'w') as f:
            f.write(f"# {self.flow.name} - Flow Diagram\n\n")
            f.write("```mermaid\n")
            f.write(diagram)
            f.write("\n```\n")

        print(f"✅ Mermaid diagram exported to: {filepath}")

    def export_graphviz(self, filepath: str) -> None:
        """
        Export GraphViz DOT file.

        Args:
            filepath: Output file path (.dot)
        """
        dot = self.to_graphviz()

        with open(filepath, 'w') as f:
            f.write(dot)

        print(f"✅ GraphViz DOT file exported to: {filepath}")
        print(f"💡 Generate image with: dot -Tpng {filepath} -o {filepath}.png")

    def export_ascii(self, filepath: str) -> None:
        """
        Export ASCII diagram to text file.

        Args:
            filepath: Output file path (.txt)
        """
        ascii_diagram = self.to_ascii()

        with open(filepath, 'w') as f:
            f.write(ascii_diagram)

        print(f"✅ ASCII diagram exported to: {filepath}")


def visualize(flow: Flow) -> FlowVisualizer:
    """
    Convenience function to create a visualizer.

    Usage:
        flow = FlowBuilder("bot").state(...).build()
        visualize(flow).export_mermaid("diagram.md")
    """
    return FlowVisualizer(flow)
