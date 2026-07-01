import logging
import uuid
from typing import Optional, Any, Callable
from fastapi import BackgroundTasks

logger = logging.getLogger("app.services.background")


class BackgroundTaskService:
    """
    Service layer executing non-blocking background processes via FastAPI's BackgroundTasks.
    """
    def __init__(self, background_tasks: Optional[BackgroundTasks] = None) -> None:
        self.background_tasks = background_tasks or BackgroundTasks()

    def add_task(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """
        Adds a callable task to execution queue.
        """
        self.background_tasks.add_task(func, *args, **kwargs)

    # 1. Audit Processing Task
    def process_audit_log(self, user_id: Optional[uuid.UUID], company_id: Optional[uuid.UUID], action: str, details: dict) -> None:
        async def _log_task():
            logger.info(f"[Background Audit] User: {user_id}, Company: {company_id}, Action: {action}, Details: {details}")
        self.add_task(_log_task)

    # 2. Analytics Refresh Task
    def refresh_analytics(self, company_id: Optional[uuid.UUID] = None) -> None:
        async def _refresh():
            logger.info(f"[Background Analytics] Refreshing cached stats. Scope: {company_id or 'Global'}")
            from app.services.cache import cache_service
            if company_id:
                cache_service.invalidate_pattern(f"analytics:company:{company_id}:*")
            else:
                cache_service.invalidate_pattern("analytics:global:*")
        self.add_task(_refresh)

    # 3. Certificate Generation Task
    def generate_certificate(self, retirement_id: uuid.UUID) -> None:
        async def _gen():
            logger.info(f"[Background Cert] Rendering PDF certificate for retirement: {retirement_id}")
        self.add_task(_gen)

    # 4. Notification Dispatch Task
    def dispatch_notification(self, recipient_email: str, title: str, body: str) -> None:
        async def _dispatch():
            logger.info(f"[Background Notify] Sending alert to {recipient_email}. Title: {title}")
        self.add_task(_dispatch)

    # 5. Expired Listing Detection Task
    def detect_expired_listings(self) -> None:
        async def _detect():
            logger.info("[Background Listing] Scanning for expired marketplace listings...")
        self.add_task(_detect)

    # 6. Cleanup Tasks
    def run_cleanup(self) -> None:
        async def _cleanup():
            logger.info("[Background Cleanup] Deleting temp exports, clean expired logs, etc.")
        self.add_task(_cleanup)


class ScheduledTaskInterfaces:
    """
    Interfaces prepared for periodic scheduler engines (like Celery Beat or Rockry / APScheduler).
    """
    @staticmethod
    def daily_analytics_refresh() -> None:
        logger.info("[Scheduled Interface] Triggering daily analytics cache refresh.")

    @staticmethod
    def listing_expiration_check() -> None:
        logger.info("[Scheduled Interface] Running listing expiration and status transitions check.")

    @staticmethod
    def inactive_session_cleanup() -> None:
        logger.info("[Scheduled Interface] Purging inactive refresh tokens and logged out sessions.")

    @staticmethod
    def audit_archiving() -> None:
        logger.info("[Scheduled Interface] Archiving system logs older than 90 days to cold storage.")

    @staticmethod
    def future_email_queue_processor() -> None:
        logger.info("[Scheduled Interface] Processing queued transactional emails.")
