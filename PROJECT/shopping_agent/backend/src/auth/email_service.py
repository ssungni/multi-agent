import logging

logger = logging.getLogger(__name__)


class EmailService:
    def send_verification_code(self, email: str, code: str) -> None:
        # ponytail: 실제 SMTP/SES 연동 대신 로그로 대체. 실제 발송 필요해지면 이 메서드만 교체.
        logger.info("[mock email] 인증코드 발송 → %s : %s", email, code)
