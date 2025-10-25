"""
Centralized Batch Polling Manager for NocoDB payment status checks.

This manager aggregates polling requests from multiple users and batches them
into efficient group queries, dramatically reducing API load.

Problem:
    - 300 users with individual polling = 300 HTTP requests every 60s = ~5 RPS
    - NocoDB limit: 5 RPS per API token
    - Bursts can exceed limit → HTTP 429 → 30s lockout

Solution:
    - Centralized batch polling: 300 users / 20 per batch = 15 requests
    - 15 requests / 60s = 0.25 RPS (95% reduction!)
    - Works even with 1000+ users
"""
import asyncio
from typing import Dict, Set, Callable, Optional, Any
from dataclasses import dataclass
import time


@dataclass
class PollingSubscription:
    """Subscription for a user waiting for batch polling results"""
    user_id: int
    record_id: str
    callback: Callable[[bool], Any]  # Called with payment status result
    subscribed_at: float


class BatchPollingManager:
    """
    Centralized manager for batching payment status checks.

    Instead of each user having their own polling task, all users subscribe
    to a centralized manager that batches checks efficiently.

    Usage:
        manager = BatchPollingManager(
            batch_check_fn=batch_check_payment_status,
            interval=60,
            batch_size=20
        )

        # User subscribes to polling
        await manager.subscribe(
            user_id=12345,
            record_id="rec_abc123",
            callback=lambda is_paid: handle_payment(is_paid)
        )

        # Start centralized polling loop
        await manager.start()
    """

    def __init__(
        self,
        batch_check_fn: Callable[[list], Dict[str, bool]],
        interval: int = 60,
        batch_size: int = 20
    ):
        """
        Initialize batch polling manager.

        Args:
            batch_check_fn: Async function(record_ids: list) -> dict{record_id: is_paid}
            interval: Polling interval in seconds (default: 60)
            batch_size: Number of records to check per batch (default: 20)
        """
        self.batch_check_fn = batch_check_fn
        self.interval = interval
        self.batch_size = batch_size

        # Active subscriptions: {user_id: PollingSubscription}
        self.subscriptions: Dict[int, PollingSubscription] = {}

        # Background polling task
        self.polling_task: Optional[asyncio.Task] = None
        self.running = False

        # Stats
        self.stats = {
            'total_polls': 0,
            'total_batches': 0,
            'total_api_requests': 0,
            'active_subscriptions': 0
        }

    async def subscribe(
        self,
        user_id: int,
        record_id: str,
        callback: Callable[[bool], Any]
    ) -> None:
        """
        Subscribe user to centralized batch polling.

        Args:
            user_id: Telegram user ID
            record_id: NocoDB record ID to monitor
            callback: Async function to call when payment status changes
        """
        subscription = PollingSubscription(
            user_id=user_id,
            record_id=record_id,
            callback=callback,
            subscribed_at=time.time()
        )

        self.subscriptions[user_id] = subscription
        self.stats['active_subscriptions'] = len(self.subscriptions)

        print(f"✅ User {user_id} subscribed to batch polling (record: {record_id})")
        print(f"📊 Active subscriptions: {len(self.subscriptions)}")

    def unsubscribe(self, user_id: int) -> None:
        """
        Unsubscribe user from batch polling.

        Args:
            user_id: Telegram user ID
        """
        if user_id in self.subscriptions:
            del self.subscriptions[user_id]
            self.stats['active_subscriptions'] = len(self.subscriptions)
            print(f"🔕 User {user_id} unsubscribed from batch polling")

    async def start(self) -> None:
        """Start centralized batch polling loop"""
        if self.running:
            print("⚠️  Batch polling already running")
            return

        self.running = True
        self.polling_task = asyncio.create_task(self._polling_loop())
        print(f"🚀 Centralized batch polling started (interval: {self.interval}s, batch_size: {self.batch_size})")

    async def stop(self) -> None:
        """Stop centralized batch polling loop"""
        self.running = False
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
        print("🛑 Centralized batch polling stopped")

    async def _polling_loop(self) -> None:
        """Main polling loop - runs continuously"""
        while self.running:
            try:
                await asyncio.sleep(self.interval)

                if not self.subscriptions:
                    continue  # No users to check

                self.stats['total_polls'] += 1
                await self._check_all_subscriptions()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in batch polling loop: {e}")

    async def _check_all_subscriptions(self) -> None:
        """Check all active subscriptions in batches"""
        if not self.subscriptions:
            return

        # Collect all record IDs
        record_ids = [sub.record_id for sub in self.subscriptions.values()]
        user_id_by_record = {sub.record_id: sub.user_id for sub in self.subscriptions.values()}

        print(f"\n🔍 Checking {len(record_ids)} payment records in batches of {self.batch_size}...")

        # Split into batches
        batches = [
            record_ids[i:i + self.batch_size]
            for i in range(0, len(record_ids), self.batch_size)
        ]

        self.stats['total_batches'] += len(batches)
        self.stats['total_api_requests'] += len(batches)

        print(f"📦 Processing {len(batches)} batches...")

        # Process batches in parallel (rate limiter will throttle)
        tasks = [
            self._check_batch(batch, batch_idx, len(batches), user_id_by_record)
            for batch_idx, batch in enumerate(batches, 1)
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        print(f"✅ Batch polling completed. Next check in {self.interval}s\n")

    async def _check_batch(
        self,
        record_ids: list,
        batch_idx: int,
        total_batches: int,
        user_id_by_record: Dict[str, int]
    ) -> None:
        """Check one batch of records"""
        try:
            print(f"   Batch {batch_idx}/{total_batches}: checking {len(record_ids)} records...")

            # Call batch check function (goes through rate limiter)
            results = await self.batch_check_fn(record_ids)

            # Process results
            paid_count = 0
            for record_id, is_paid in results.items():
                if is_paid:
                    paid_count += 1
                    user_id = user_id_by_record.get(record_id)
                    if user_id and user_id in self.subscriptions:
                        subscription = self.subscriptions[user_id]

                        # Call callback
                        try:
                            await subscription.callback(True)
                        except Exception as e:
                            print(f"❌ Error in callback for user {user_id}: {e}")

                        # Unsubscribe after payment confirmed
                        self.unsubscribe(user_id)

            print(f"   ✅ Batch {batch_idx}/{total_batches}: {paid_count} paid, {len(record_ids) - paid_count} pending")

        except Exception as e:
            print(f"❌ Error checking batch {batch_idx}: {e}")

    def get_stats(self) -> dict:
        """Get batch polling statistics"""
        avg_batch_size = (
            self.stats['active_subscriptions'] / self.stats['total_batches']
            if self.stats['total_batches'] > 0 else 0
        )

        # Calculate reduction compared to per-user polling
        per_user_requests = self.stats['total_polls'] * self.stats['active_subscriptions']
        actual_requests = self.stats['total_api_requests']
        reduction = (
            (1 - actual_requests / per_user_requests) * 100
            if per_user_requests > 0 else 0
        )

        return {
            'active_subscriptions': self.stats['active_subscriptions'],
            'total_polls': self.stats['total_polls'],
            'total_batches': self.stats['total_batches'],
            'total_api_requests': self.stats['total_api_requests'],
            'avg_batch_size': f"{avg_batch_size:.1f}",
            'api_reduction': f"{reduction:.1f}%",
            'per_user_requests_avoided': per_user_requests - actual_requests
        }

    def print_stats(self) -> None:
        """Print formatted statistics"""
        stats = self.get_stats()

        print("\n" + "="*60)
        print("📊 Batch Polling Manager Stats")
        print("="*60)
        print(f"Active Subscriptions: {stats['active_subscriptions']}")
        print(f"Total Poll Cycles: {stats['total_polls']}")
        print(f"Total Batches Processed: {stats['total_batches']}")
        print(f"Total API Requests: {stats['total_api_requests']}")
        print(f"Average Batch Size: {stats['avg_batch_size']}")
        print(f"\n💡 Efficiency:")
        print(f"   API Request Reduction: {stats['api_reduction']}")
        print(f"   Requests Avoided: {stats['per_user_requests_avoided']}")
        print("="*60 + "\n")
