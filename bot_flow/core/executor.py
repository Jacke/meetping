"""
Executor for running declarative bot flows with python-telegram-bot.
"""
import asyncio
import os
import signal
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
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

    def __init__(self, flow: Flow, bot_token: str, admin_chat_ids: Optional[list] = None,
                 nocodb_url: Optional[str] = None, nocodb_table_id: Optional[str] = None):
        self.flow = flow
        self.bot_token = bot_token
        self.application: Optional[Application] = None

        # Track user states: user_id -> current_state_name
        self.user_states: Dict[int, str] = {}

        # Track active polling tasks: user_id -> asyncio.Task
        self.polling_tasks: Dict[int, asyncio.Task] = {}

        # Shutdown flag
        self._shutdown_requested = False

        # Admin chat IDs for notifications
        self.admin_chat_ids = admin_chat_ids or []

        # NocoDB configuration for admin notifications
        self.nocodb_url = nocodb_url
        self.nocodb_table_id = nocodb_table_id

    async def _notify_admins(self, user_id: int, username: str, first_name: str,
                            from_state: Optional[str], to_state: str,
                            nocodb_url: Optional[str] = None,
                            nocodb_table_id: Optional[str] = None) -> None:
        """
        Send notification to admin users about state change.

        Args:
            user_id: Telegram user ID
            username: User's username
            first_name: User's first name
            from_state: Previous state (None if first interaction)
            to_state: New state
            nocodb_url: NocoDB base URL (optional)
            nocodb_table_id: NocoDB table ID (optional)
        """
        if not self.admin_chat_ids or not self.application:
            return

        # Format user info
        user_mention = f"@{username}" if username else first_name
        user_info = f"User: {user_mention} (ID: {user_id})"

        # Format state change
        if from_state:
            state_change = f"State: {from_state} → {to_state}"
        else:
            state_change = f"State: START → {to_state}"

        message = f"🔔 <b>State Change</b>\n\n{user_info}\n{state_change}"

        # Add NocoDB link for awaiting_payment state
        if to_state == "awaiting_payment" and nocodb_url and nocodb_table_id:
            nocodb_link = f"{nocodb_url}/#/nc/{nocodb_table_id}"
            message += f"\n\n🔗 <a href=\"{nocodb_link}\">Открыть NocoDB</a>"

        # Send to each admin by chat ID
        for chat_id in self.admin_chat_ids:
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"⚠️ Failed to notify chat_id {chat_id}: {e}")

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

        # Track previous state for notifications
        previous_state = self.user_states.get(user_id)

        # Update user state
        self.user_states[user_id] = state_name
        print(f"🔄 User {user_id} -> {state_name}")

        # Notify admins about state change (only for important states)
        important_states = ['awaiting_payment', 'success']
        if self.admin_chat_ids and state_name in important_states:
            user = flow_ctx.user
            await self._notify_admins(
                user_id=user_id,
                username=user.username or "",
                first_name=user.first_name or "",
                from_state=previous_state,
                to_state=state_name,
                nocodb_url=self.nocodb_url,
                nocodb_table_id=self.nocodb_table_id
            )

        # Execute on_enter action
        if state.on_enter:
            await state.on_enter(flow_ctx)

        # Execute sequential actions (skip if state expects MESSAGE, actions will run on message receipt)
        if state.trigger_type != TriggerType.MESSAGE:
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

        # Handle auto transition (skip if state expects MESSAGE - transition will happen on message receipt)
        elif state.auto_transition and state.trigger_type != TriggerType.MESSAGE:
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

            except ValueError as e:
                # Record not found (404) - remove user from polling
                print(f"🗑️  Removing user {user_id} from polling: {e}")
                del self.user_states[user_id]
                if user_id in self.polling_tasks:
                    self.polling_tasks[user_id].cancel()
                    del self.polling_tasks[user_id]
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

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text message"""
        user_id = update.effective_user.id
        message_text = update.message.text

        # Find current state and check if it expects a message
        current_state_name = self.user_states.get(user_id)
        if current_state_name:
            current_state = self.flow.get_state(current_state_name)
            if current_state and current_state.trigger_type == TriggerType.MESSAGE:
                # Create flow context with the message
                flow_ctx = FlowContext(update, context, self.flow)
                flow_ctx.set('message_text', message_text)

                # Execute actions first
                for action in current_state.actions:
                    await action(flow_ctx)

                # Then handle transition
                if current_state.auto_transition:
                    await self.transition_to(user_id, current_state.auto_transition, flow_ctx)
                    return

        print(f"⚠️ No message handler for user {user_id} in state '{current_state_name}'")

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

        # Register message handler (handles text messages)
        message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        self.application.add_handler(message_handler)
        print(f"✅ Registered message handler")

    async def _setup_bot_commands(self) -> None:
        """Setup bot commands menu in Telegram"""
        from telegram import BotCommandScopeChat

        # Command descriptions (можно кастомизировать для каждой команды)
        command_descriptions = {
            'start': 'Начать регистрацию на мероприятие',
            'stats': 'Статистика регистраций (только для админов)',
        }

        # Admin-only commands
        admin_commands = {'stats'}

        # Public commands (for all users)
        public_commands = []
        admin_only_commands = []

        # Collect all command triggers from flow states
        for state_name, state in self.flow.states.items():
            if state.trigger_type == TriggerType.COMMAND and state.trigger_value:
                command_name = state.trigger_value.lstrip('/')
                description = command_descriptions.get(command_name, f"Start {self.flow.name}")
                bot_command = BotCommand(command_name, description)

                if command_name in admin_commands:
                    admin_only_commands.append(bot_command)
                else:
                    public_commands.append(bot_command)

        # Set public commands for all users
        if public_commands:
            await self.application.bot.set_my_commands(public_commands)
            print(f"✅ Set {len(public_commands)} public commands in menu")

        # Set admin commands (public + admin) for each admin
        if admin_only_commands and self.admin_chat_ids:
            all_admin_commands = public_commands + admin_only_commands
            for admin_chat_id in self.admin_chat_ids:
                try:
                    await self.application.bot.set_my_commands(
                        all_admin_commands,
                        scope=BotCommandScopeChat(chat_id=admin_chat_id)
                    )
                    print(f"✅ Set {len(all_admin_commands)} commands for admin {admin_chat_id}")
                except Exception as e:
                    print(f"⚠️ Failed to set admin commands for {admin_chat_id}: {e}")

    async def restore_user_states(self, users_data: list, state_name: str = "awaiting_payment") -> None:
        """
        Restore user states and start polling for users from database.

        Args:
            users_data: List of dicts with user data [{tg_id, record_id, username, first_name}, ...]
            state_name: State to restore users to (default: awaiting_payment)
        """
        if not users_data:
            print("ℹ️  No users to restore")
            return

        state = self.flow.get_state(state_name)
        if not state:
            print(f"❌ State '{state_name}' not found, cannot restore users")
            return

        if not state.polling:
            print(f"⚠️ State '{state_name}' has no polling configured, skipping restoration")
            return

        print(f"\n🔄 Restoring {len(users_data)} users in state '{state_name}':")

        for user_data in users_data:
            user_id = user_data['tg_id']
            record_id = user_data['record_id']
            username = user_data.get('username', '')
            first_name = user_data.get('first_name', 'Unknown')

            # Set user state
            self.user_states[user_id] = state_name

            # Create a simple context holder for polling
            class MockContext:
                def __init__(self, user_id, record_id):
                    self._data = {
                        'record_id': record_id,
                        'already_registered': True,
                        'payment_confirmed': False
                    }
                    self.user_id = user_id

                def get(self, key, default=None):
                    return self._data.get(key, default)

                def set(self, key, value):
                    self._data[key] = value

                @property
                def poll_result(self):
                    return self._data.get('poll_result')

                @poll_result.setter
                def poll_result(self, value):
                    self._data['poll_result'] = value

            mock_ctx = MockContext(user_id, record_id)

            # Start polling task
            task = asyncio.create_task(
                self._poll_state_restored(user_id, state, mock_ctx)
            )
            self.polling_tasks[user_id] = task

            print(f"   ✓ User {user_id} (@{username or first_name}) - record {record_id}")

        print(f"✅ Started polling for {len(users_data)} users\n")

    async def _poll_state_restored(self, user_id: int, state: StateNode, mock_ctx) -> None:
        """
        Poll state for restored users (simplified version without full FlowContext).
        """
        polling = state.polling
        attempts = 0

        while self.user_states.get(user_id) == state.name:
            await asyncio.sleep(polling.interval)

            # Check max attempts
            if polling.max_attempts and attempts >= polling.max_attempts:
                break

            # Execute check function
            try:
                # For restored users, we use check_payment_status directly
                result = await self._check_payment_status_for_restored(mock_ctx)
                mock_ctx.poll_result = result

                if result and polling.on_true_goto:
                    # Payment confirmed!
                    print(f"✅ Payment confirmed for user {user_id}")
                    # We can't transition without full context, so just remove from polling
                    self.user_states[user_id] = "success"
                    break

            except ValueError as e:
                # Record not found (404) - remove user from polling
                print(f"🗑️  Removing user {user_id} from polling: {e}")
                del self.user_states[user_id]
                if user_id in self.polling_tasks:
                    self.polling_tasks[user_id].cancel()
                    del self.polling_tasks[user_id]
                break

            except Exception as e:
                print(f"❌ Polling error for user {user_id}: {e}")

            attempts += 1

    async def _check_payment_status_for_restored(self, mock_ctx) -> bool:
        """Check payment status in NocoDB for restored users"""
        record_id = mock_ctx.get('record_id')
        if not record_id:
            return False

        # Import NocoDB credentials
        import os
        nocodb_api_url = os.getenv("NOCODB_API_URL", "https://app.nocodb.com")
        nocodb_api_token = os.getenv("NOCODB_API_TOKEN")
        nocodb_table_id = os.getenv("NOCODB_TABLE_ID")

        if not nocodb_api_token or not nocodb_table_id:
            return False

        headers = {"xc-token": nocodb_api_token}

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{nocodb_api_url}/api/v2/tables/{nocodb_table_id}/records/{record_id}",
                    headers=headers,
                    timeout=10.0
                )

                # Check for 404 - record not found (deleted from NocoDB)
                if response.status_code == 404:
                    print(f"⚠️  Record {record_id} not found in NocoDB (deleted?)")
                    raise ValueError(f"Record {record_id} not found")

                response.raise_for_status()
                record = response.json()
                is_paid = record.get("Paid", False) is True
                return is_paid

        except ValueError:
            # Re-raise ValueError for 404 handling
            raise
        except Exception as e:
            print(f"❌ Error checking payment for record {record_id}: {e}")
            return False

    async def _cleanup(self) -> None:
        """Cleanup resources on shutdown"""
        print("\n🛑 Shutting down gracefully...")

        # Cancel all active polling tasks
        if self.polling_tasks:
            print(f"⏹️  Cancelling {len(self.polling_tasks)} polling tasks...")
            for task in self.polling_tasks.values():
                if not task.done():
                    task.cancel()

            # Wait for all tasks to complete
            try:
                await asyncio.gather(*self.polling_tasks.values(), return_exceptions=True)
                print("✅ All polling tasks cancelled")
            except Exception as e:
                print(f"⚠️ Error during task cleanup: {e}")

        print("👋 Goodbye!")

    def _signal_handler(self, signum, _frame):
        """Handle termination signals"""
        self._shutdown_requested = True
        print(f"\n⚠️  Received signal {signum}, initiating shutdown...")

    def run(self) -> None:
        """
        Run the bot with the defined flow.

        This is a blocking call that starts the bot polling loop.
        Supports graceful shutdown on SIGINT (Ctrl+C) and SIGTERM.
        """
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is required")

        print(f"🤖 Starting bot with flow: {self.flow.name}")
        print(f"📊 States: {len(self.flow.states)}")
        print(f"🎯 Initial state: {self.flow.initial_state}")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Create application
        self.application = Application.builder().token(self.bot_token).build()

        # Register handlers
        self._register_handlers()

        # Setup bot commands menu and cleanup hooks
        async def post_init(_application: Application) -> None:
            await self._setup_bot_commands()

            # Restore user states if any were loaded
            if hasattr(self, '_awaiting_users') and self._awaiting_users:
                await self.restore_user_states(self._awaiting_users)

        async def post_shutdown(_application: Application) -> None:
            await self._cleanup()

        self.application.post_init = post_init
        self.application.post_shutdown = post_shutdown

        # Start polling
        print("🚀 Bot is running... (Press Ctrl+C to stop)")
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
