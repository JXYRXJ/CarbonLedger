import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("app.services.notification")


class NotificationService:
    """
    Core notification router. Routes transactional notifications, alerts,
    and security triggers to structured log streams (preparing for SMTP/SNS/SendGrid provider bindings).
    """
    def send_notification(self, recipient: str, message_type: str, context: Dict[str, Any]) -> None:
        """
        Generic notification dispatcher.
        """
        logger.info(
            f"[Notification] Dispatched message. Type={message_type}, Recipient={recipient}, Keys={list(context.keys())}"
        )

    def send_email(self, recipient_email: str, subject: str, template_name: str, context: Dict[str, Any]) -> None:
        """
        Mails a formatted HTML body template. STUB.
        """
        logger.info(f"[Email Dispatch] Sending '{subject}' to {recipient_email} using template '{template_name}'")

    def send_system_alert(self, subject: str, message: str) -> None:
        """
        Sends administrative warnings regarding server resource depletion or sync bugs.
        """
        logger.warning(f"[SYSTEM ALERT] {subject}: {message}")

    def send_security_alert(self, event_name: str, user_id: Optional[str], details: str) -> None:
        """
        Fires alarm notifications on account security locks, session hijacking, or RTR compromises.
        """
        logger.critical(f"[SECURITY ALERT] Event={event_name}, User={user_id or 'anonymous'}. Details: {details}")

    # Event helpers
    def notify_registration(self, email: str, company_name: str) -> None:
        self.send_email(
            recipient_email=email,
            subject="Welcome to CarbonLedger!",
            template_name="registration_welcome",
            context={"company_name": company_name}
        )

    def notify_login(self, email: str, ip_address: str) -> None:
        self.send_email(
            recipient_email=email,
            subject="New Sign-in Detected",
            template_name="security_login",
            context={"ip": ip_address}
        )

    def notify_password_change(self, email: str) -> None:
        self.send_email(
            recipient_email=email,
            subject="Security Alert: Password Changed",
            template_name="security_password_changed",
            context={}
        )

    def notify_listing_approved(self, email: str, listing_id: str) -> None:
        self.send_email(
            recipient_email=email,
            subject="Marketplace Listing Approved",
            template_name="listing_approved",
            context={"listing_id": listing_id}
        )

    def notify_listing_rejected(self, email: str, listing_id: str, reason: str) -> None:
        self.send_email(
            recipient_email=email,
            subject="Marketplace Listing Action Required: Rejected",
            template_name="listing_rejected",
            context={"listing_id": listing_id, "reason": reason}
        )

    def notify_purchase_completed(self, email: str, order_id: str, credits: float, total_price: float) -> None:
        self.send_email(
            recipient_email=email,
            subject="Purchase Invoice Completed",
            template_name="transaction_invoice",
            context={"order_id": order_id, "credits": credits, "total_price": total_price}
        )

    def notify_credits_retired(self, email: str, certificate_number: str, quantity: float) -> None:
        self.send_email(
            recipient_email=email,
            subject="Retirement Certificate Issued",
            template_name="retirement_issued",
            context={"cert_number": certificate_number, "quantity": quantity}
        )

    def notify_admin_action(self, email: str, action: str, target: str) -> None:
        self.send_email(
            recipient_email=email,
            subject="Administrative System Log Notice",
            template_name="admin_action",
            context={"action": action, "target": target}
        )
