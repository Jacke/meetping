#!/usr/bin/env python3
"""
Standalone script to generate payment flow visualization without requiring telegram dependencies.
"""
import sys
import os
sys.path.insert(0, '.')

# Import only what we need without pulling in telegram deps
import importlib.util

# Manually import state module
state_spec = importlib.util.spec_from_file_location("state", "bot_flow/core/state.py")
state_module = importlib.util.module_from_spec(state_spec)
state_spec.loader.exec_module(state_module)

StateNode = state_module.StateNode
Flow = state_module.Flow
PollingConfig = state_module.PollingConfig
TriggerType = state_module.TriggerType

# Manually import visualizer module
viz_spec = importlib.util.spec_from_file_location("visualizer", "bot_flow/core/visualizer.py")
viz_module = importlib.util.module_from_spec(viz_spec)
sys.modules['bot_flow.core.state'] = state_module  # Make state available for visualizer
viz_spec.loader.exec_module(viz_module)

FlowVisualizer = viz_module.FlowVisualizer

# Manually build the flow structure for visualization
# (without importing payment_flow.py which has telegram dependencies)

flow = Flow(name="payment_bot")

# State: welcome
welcome = StateNode(
    name="welcome",
    trigger_type=TriggerType.COMMAND,
    trigger_value="/start",
    message="👋 Добро пожаловать, {user.first_name}!\n\n🎉 Это бот для регистрации и оплаты билетов.",
)
welcome.add_button("💳 Оплатить билет", "pay_ticket", "payment_info")

# State: payment_info
payment_info = StateNode(
    name="payment_info",
    trigger_type=TriggerType.CALLBACK,
    trigger_value="pay_ticket",
    message="💰 Информация для оплаты...",
    auto_transition="awaiting_payment"
)

# State: awaiting_payment (with polling)
awaiting_payment = StateNode(
    name="awaiting_payment",
    polling=PollingConfig(
        check_function=lambda ctx: True,  # Placeholder
        interval=10,
        on_true_goto="success"
    )
)

# State: success
success = StateNode(
    name="success",
    message="✅ Оплата подтверждена! 🎊",
    is_final=True
)

# Add states to flow
flow.add_state(welcome)
flow.add_state(payment_info)
flow.add_state(awaiting_payment)
flow.add_state(success)

# Generate visualizations
viz = FlowVisualizer(flow)

print("📊 Generating payment flow visualizations...\n")

viz.export_mermaid("docs/payment_flow.md")
viz.export_graphviz("docs/payment_flow.dot")
viz.export_ascii("docs/payment_flow.txt")

print("\n" + "="*60)
print("ASCII Preview:")
print("="*60)
print(viz.to_ascii())

print("\n" + "="*60)
print("✅ All visualizations generated successfully!")
print("="*60)
