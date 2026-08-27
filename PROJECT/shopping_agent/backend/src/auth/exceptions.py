class AuthError(Exception):
    status_code: int = 400
    error_code: str = "AUTH_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EmailDuplicateError(AuthError):
    status_code = 409
    error_code = "EMAIL_DUPLICATE"

    def __init__(self):
        super().__init__("이미 가입된 이메일입니다.")


class PhoneDuplicateError(AuthError):
    status_code = 409
    error_code = "PHONE_DUPLICATE"

    def __init__(self):
        super().__init__("이미 등록된 전화번호입니다.")


class VerifyCodeExpiredError(AuthError):
    status_code = 400
    error_code = "VERIFY_CODE_EXPIRED"

    def __init__(self):
        super().__init__("인증코드가 만료되었습니다. 재발송해주세요.")


class VerifyCodeMismatchError(AuthError):
    status_code = 400
    error_code = "VERIFY_CODE_MISMATCH"

    def __init__(self):
        super().__init__("인증코드가 일치하지 않습니다.")


class AlreadyVerifiedError(AuthError):
    status_code = 409
    error_code = "ALREADY_VERIFIED"

    def __init__(self):
        super().__init__("이미 인증이 완료된 계정입니다.")


class SignupNotFoundError(AuthError):
    status_code = 404
    error_code = "SIGNUP_NOT_FOUND"

    def __init__(self):
        super().__init__("가입 이력이 없는 이메일입니다.")


class TooManyRequestsError(AuthError):
    status_code = 429
    error_code = "TOO_MANY_REQUESTS"

    def __init__(self):
        super().__init__("잠시 후 다시 시도해주세요.")


class InvalidCredentialsError(AuthError):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"

    def __init__(self):
        super().__init__("이메일 또는 비밀번호가 올바르지 않습니다.")


class EmailNotVerifiedError(AuthError):
    status_code = 403
    error_code = "EMAIL_NOT_VERIFIED"

    def __init__(self):
        super().__init__("이메일 인증이 필요합니다.")


class AccountSuspendedError(AuthError):
    status_code = 403
    error_code = "ACCOUNT_SUSPENDED"

    def __init__(self):
        super().__init__("정지된 계정입니다.")


class AccountWithdrawnError(AuthError):
    status_code = 403
    error_code = "ACCOUNT_WITHDRAWN"

    def __init__(self):
        super().__init__("탈퇴한 계정입니다.")


class AccountLockedError(AuthError):
    status_code = 423
    error_code = "ACCOUNT_LOCKED"

    def __init__(self):
        super().__init__("로그인 실패 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.")


class InvalidAccessTokenError(AuthError):
    status_code = 401
    error_code = "INVALID_ACCESS_TOKEN"

    def __init__(self):
        super().__init__("유효하지 않은 access token입니다.")


class InvalidRefreshTokenError(AuthError):
    status_code = 401
    error_code = "INVALID_REFRESH_TOKEN"

    def __init__(self):
        super().__init__("유효하지 않은 refresh token입니다.")
