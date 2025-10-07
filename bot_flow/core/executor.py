"""
Executor for running declarative bot flows with python-telegram-bot.
"""
import asyncio
import os
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from .state import Flow, StateNode, TriggerType


class FlowContext:
    """
    Context object passed to state actions.
    Provides access to user data, bot, environment, and custom variables.
    """

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE, flow: Flow):
        self.update = update
        self.context = context
        self.flow = flow
        self.user = update.effective_user
        self.chat = update.effective_chat
        self._data: Dict[str, Any] = {}
        self.poll_result: Optional[bool] = None

    def set(self, key: str, value: Any) -> None:
        """Store data in context"""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve data from context"""
        return self._data.get(key, default)

    @property
    def env(self) -> Dict[str, str]:
        """Access to environment variables"""
        return os.environ

    def format_message(self, template: str) -> str:
        """
        Format message template with context variables.

        Supports:
            {user.first_name}, {user.username}, {user.id}
            {env.VAR_NAME}
            {ctx.var_name} - custom context variables
        """
        formatted = template

        # User variables
        if self.user:
            formatted = formatted.replace('{user.first_name}', self.user.first_name or '')
            formatted = formatted.replace('{user.username}', self.user.username or '')
            formatted = formatted.replace('{user.id}', str(self.user.id))

        # Environment variables
        import re
        env_pattern = r'\{env\.([A-Z_]+)\}'
        for match in re.finditer(env_pattern, formatted):
            var_name = match.group(1)
            formatted = formatted.replace(match.group(0), os.getenv(var_name, ''))

        # Context variables
        ctx_pattern = r'\{ctx\.([a-z_]+)\}'
        for match in re.finditer(ctx_pattern, formatted):
            var_name = match.group(1)
            formatted = formatted.replace(match.group(0), str(self.get(var_name, '')))

        return formatted


class FlowExecutor:
    """
    Executes a declarative Flow with python-telegram-bot.

    Handles:
    - State transitions
    - Action execution
    - Message sending
    - Polling for background checks
    """

    def __init__(self, flow: Flow, bot_token: str):
        self.flow = flow
        self.bot_token = bot_token
        self.application: Optional[Application] = None

        # Track user states: user_id -> current_state_name
        self.user_states: Dict[int, str] = {}

        # Track active polling tasks: user_id -> asyncio.Task
        self.polling_tasks: Dict[int, asyncio.Task] = {}

    async def transition_to(self, user_id: int, state_name: str,
                           flow_ctx: FlowContext) -> None:
        """
        Transition user to a new state and execute state actions.

        Args:
            user_id: Telegram user ID
            state_name: Target state name
            flow_ctx: Flow context
        """
        state = self.flow.get_state(state_name)
        if not state:
            print(f"❌ State '{state_name}' not found")
            return

        # Update user state
        self.user_states[user_id] = state_name
        print(f"🔄 User {user_id} -> {state_name}")

        # Execute on_enter action
        if state.on_enter:
            await state.on_enter(flow_ctx)

        # Execute sequential actions
        for action in state.actions:
            await action(flow_ctx)

        # Send message if defined
        if state.message:
            await self._send_message(state, flow_ctx)

        # Handle polling
        if state.polling:
            # Cancel previous polling task if exists
            if user_id in self.polling_tasks:
                self.polling_tasks[user_id].cancel()

            # Start new polling task
            task = asyncio.create_task(
                self._poll_state(user_id, state, flow_ctx)
            )
            self.polling_tasks[user_id] = task

        # Handle auto transition
        elif state.auto_transition:
            await self.transition_to(user_id, state.auto_transition, flow_ctx)

    async def _send_message(self, state: StateNode, flow_ctx: FlowContext) -> None:
        """Send state message with optional inline keyboard"""
        chat_id = flow_ctx.chat.id
        message_text = flow_ctx.format_message(state.message)

        # Build inline keyboard if buttons exist
        reply_markup = None
        if state.buttons:
            keyboard = [
                [InlineKeyboardButton(btn.text, callback_data=btn.callback_data)]
                for btn in state.buttons
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

        await self.application.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=reply_markup,
            **state.message_kwargs
        )

    async def _poll_state(self, user_id: int, state: StateNode,
                         flow_ctx: FlowContext) -> None:
        """
        Poll state condition at regular intervals.

        Used for async checks like payment confirmation.
        """
        polling = state.polling
        attempts = 0

        while self.user_states.get(user_id) == state.name:
            await asyncio.sleep(polling.interval)

            # Check max attempts
            if polling.max_attempts and attempts >= polling.max_attempts:
                if polling.on_false_goto:
                    await self.transition_to(user_id, polling.on_false_goto, flow_ctx)
                break

            # Execute check function
            try:
                result = await polling.check_function(flow_ctx)
                flow_ctx.poll_result = result

                if result and polling.on_true_goto:
                    await self.transition_to(user_id, polling.on_true_goto, flow_ctx)
                    break
                elif not result and polling.on_false_goto:
                    await self.transition_to(user_id, polling.on_false_goto, flow_ctx)
                    break

            except Exception as e:
                print(f"❌ Polling error in state '{state.name}': {e}")

            attempts += 1

    async def _handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                             state_name: str) -> None:
        """Handle command trigger"""
        user_id = update.effective_user.id
        flow_ctx = FlowContext(update, context, self.flow)
        await self.transition_to(user_id, state_name, flow_ctx)

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback query"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        callback_data = query.data

        # Find state with matching transition
        current_state_name = self.user_states.get(user_id)
        if current_state_name:
            current_state = self.flow.get_state(current_state_name)
            if current_state and callback_data in current_state.transitions:
                target_state = current_state.transitions[callback_data]
                flow_ctx = FlowContext(update, context, self.flow)
                await self.transition_to(user_id, target_state, flow_ctx)
                return

        print(f"⚠️ No transition found for callback '{callback_data}' in state '{current_state_name}'")

    def _register_handlers(self) -> None:
        """Register telegram handlers based on flow states"""
        for state_name, state in self.flow.states.items():
            if state.trigger_type == TriggerType.COMMAND and state.trigger_value:
                # Register command handler
                handler = CommandHandler(
                    state.trigger_value.lstrip('/'),
                    lambda u, c, s=state_name: self._handle_command(u, c, s)
                )
                self.application.add_handler(handler)
                print(f"✅ Registered command handler: {state.trigger_value} -> {state_name}")

        # Register callback query handler (handles all callbacks)
        callback_handler = CallbackQueryHandler(self._handle_callback)
        self.application.add_handler(callback_handler)
        print(f"✅ Registered callback query handler")

    def run(self) -> None:
        """
        Run the bot with the defined flow.

        This is a blocking call that starts the bot polling loop.
        """
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is required")

        print(f"🤖 Starting bot with flow: {self.flow.name}")
        print(f"📊 States: {len(self.flow.states)}")
        print(f"🎯 Initial state: {self.flow.initial_state}")

        # Create application
        self.application = Application.builder().token(self.bot_token).build()

        # Register handlers
        self._register_handlers()

        # Start polling
        print("🚀 Bot is running...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def run_async(self) -> None:
        """
        Async version of run() for integration with existing async code.
        """
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is required")

        print(f"🤖 Starting bot with flow: {self.flow.name}")

        # Create application
        self.application = Application.builder().token(self.bot_token).build()

        # Register handlers
        self._register_handlers()

        # Initialize and start
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        print("🚀 Bot is running (async mode)...")
