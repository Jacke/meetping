"""
Global Payment Tracker - Centralized payment status checking.

Instead of polling NocoDB for each user individually, this module maintains
a global cache of payment statuses that is updated periodically with a single
batch query.

Benefits:
- 300 users = 1 API request instead of 300 requests
- 95% reduction in API load
- All users get updates simultaneously
"""
import asyncio
import time
from typing import Dict, Set, Optional
from bot_flow.flows.nocodb_utils import nocodb_request_with_retry


class GlobalPaymentTracker:
    """
    Singleton tracker that maintains payment statuses for all users.

    Usage:
        tracker = GlobalPaymentTracker.get_instance()

        # Add user to tracking
        tracker.track_user(user_id, record_id)

        # Check if paid (reads from cache, no API call)
        is_paid = tracker.is_paid(user_id)

        # Start periodic updates
        await tracker.start(interval=20)
    """

    _instance: Optional['GlobalPaymentTracker'] = None

    def __init__(self):
        # Payment statuses: {user_id: is_paid}
        self.payment_statuses: Dict[int, bool] = {}

        # User to record mapping: {user_id: record_id}
        self.user_records: Dict[int, str] = {}

        # NocoDB config (will be set on first use)
        self.nocodb_api_url: Optional[str] = None
        self.nocodb_api_token: Optional[str] = None
        self.nocodb_table_id: Optional[str] = None

        # Background task
        self.update_task: Optional[asyncio.Task] = None
        self.running = False
        self.update_interval = 20  # seconds

        # Stats
        self.stats = {
            'total_updates': 0,
            'last_update_time': 0,
            'users_updated': 0,
            'payments_confirmed': 0
        }

    @classmethod
    def get_instance(cls) -> 'GlobalPaymentTracker':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def configure(self, nocodb_api_url: str, nocodb_api_token: str, nocodb_table_id: str):
        """Configure NocoDB credentials"""
        self.nocodb_api_url = nocodb_api_url
        self.nocodb_api_token = nocodb_api_token
        self.nocodb_table_id = nocodb_table_id

    def track_user(self, user_id: int, record_id: str):
        """
        Add user to tracking.

        Args:
            user_id: Telegram user ID
            record_id: NocoDB record ID
        """
        self.user_records[user_id] = record_id
        self.payment_statuses[user_id] = False  # Default to unpaid
        print(f"📍 Tracking payment for user {user_id} (record: {record_id})")

    def untrack_user(self, user_id: int):
        """Remove user from tracking (after payment confirmed)"""
        if user_id in self.user_records:
            del self.user_records[user_id]
        if user_id in self.payment_statuses:
            del self.payment_statuses[user_id]
        print(f"🔕 Stopped tracking user {user_id}")

    def is_paid(self, user_id: int) -> bool:
        """
        Check if user has paid (reads from cache, no API call).

        Args:
            user_id: Telegram user ID

        Returns:
            True if paid, False otherwise
        """
        return self.payment_statuses.get(user_id, False)

    def get_tracked_count(self) -> int:
        """Get number of users being tracked"""
        return len(self.user_records)

    async def start(self, interval: int = 20):
        """
        Start periodic payment status updates.

        Args:
            interval: Update interval in seconds (default: 20)
        """
        if self.running:
            print("⚠️  Global payment tracker already running")
            return

        self.update_interval = interval
        self.running = True
        self.update_task = asyncio.create_task(self._update_loop())
        print(f"🚀 Global payment tracker started (interval: {interval}s)")

    async def stop(self):
        """Stop periodic updates"""
        self.running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        print("🛑 Global payment tracker stopped")

    async def _update_loop(self):
        """Main update loop - runs every interval"""
        while self.running:
            try:
                await asyncio.sleep(self.update_interval)

                if not self.user_records:
                    continue  # No users to check

                await self._update_all_statuses()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in global payment tracker: {e}")

    async def _update_all_statuses(self):
        """
        Update payment statuses for all tracked users with a single batch query.

        This is the magic - one API call for ALL users!
        """
        if not self.nocodb_api_token or not self.nocodb_table_id:
            print("⚠️  NocoDB not configured, skipping update")
            return

        record_ids = list(self.user_records.values())
        user_by_record = {record_id: user_id for user_id, record_id in self.user_records.items()}

        print(f"\n🔍 Global Tracker: Checking {len(record_ids)} payment records...")

        try:
            # Build WHERE clause: (Id,in,id1,id2,id3,...)
            ids_str = ",".join(str(rid) for rid in record_ids)
            where_clause = f"(Id,in,{ids_str})"

            headers = {"xc-token": self.nocodb_api_token}

            # ONE API CALL FOR ALL USERS!
            response = await nocodb_request_with_retry(
                "GET",
                f"{self.nocodb_api_url}/api/v2/tables/{self.nocodb_table_id}/records",
                headers=headers,
                params={
                    "where": where_clause,
                    "limit": len(record_ids),
                    "fields": "Id,Paid"  # Only fetch necessary fields
                },
                timeout=15.0
            )
            response.raise_for_status()
            data = response.json()

            # Update statuses from response
            records = data.get("list", [])
            paid_count = 0
            newly_paid = []

            for record in records:
                record_id = str(record.get("Id") or record.get("id"))
                is_paid = record.get("Paid", False) is True
                user_id = user_by_record.get(record_id)

                if user_id:
                    old_status = self.payment_statuses.get(user_id, False)
                    self.payment_statuses[user_id] = is_paid

                    if is_paid:
                        paid_count += 1

                        # Detect newly paid users
                        if not old_status and is_paid:
                            newly_paid.append(user_id)

            # Update stats
            self.stats['total_updates'] += 1
            self.stats['last_update_time'] = time.time()
            self.stats['users_updated'] = len(records)
            self.stats['payments_confirmed'] += len(newly_paid)

            print(f"✅ Global Tracker: {paid_count}/{len(records)} paid, {len(records) - paid_count} pending")

            if newly_paid:
                print(f"   💰 Newly confirmed payments: {len(newly_paid)} users")
                for user_id in newly_paid:
                    print(f"      • User {user_id}")

            print(f"   📊 Next update in {self.update_interval}s\n")

        except Exception as e:
            print(f"❌ Error updating global payment statuses: {e}")

    async def force_update(self):
        """Force immediate update (useful for testing)"""
        print("🔄 Force updating payment statuses...")
        await self._update_all_statuses()

    def get_stats(self) -> dict:
        """Get tracker statistics"""
        uptime = time.time() - self.stats['last_update_time'] if self.stats['last_update_time'] > 0 else 0

        return {
            'tracked_users': len(self.user_records),
            'total_updates': self.stats['total_updates'],
            'last_update': f"{uptime:.0f}s ago" if uptime > 0 else "Never",
            'users_updated': self.stats['users_updated'],
            'payments_confirmed': self.stats['payments_confirmed'],
            'update_interval': f"{self.update_interval}s"
        }

    def print_stats(self):
        """Print formatted statistics"""
        stats = self.get_stats()

        print("\n" + "="*60)
        print("📊 Global Payment Tracker Stats")
        print("="*60)
        print(f"Tracked Users: {stats['tracked_users']}")
        print(f"Update Interval: {stats['update_interval']}")
        print(f"Total Updates: {stats['total_updates']}")
        print(f"Last Update: {stats['last_update']}")
        print(f"Users Updated: {stats['users_updated']}")
        print(f"Payments Confirmed: {stats['payments_confirmed']}")
        print("="*60 + "\n")


# Global instance (for easy access)
_global_tracker: Optional[GlobalPaymentTracker] = None


def get_global_tracker() -> GlobalPaymentTracker:
    """Get global tracker instance (convenience function)"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = GlobalPaymentTracker.get_instance()
    return _global_tracker
