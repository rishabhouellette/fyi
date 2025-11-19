"""
Custom exceptions for FYI Uploader
"""

class FYIUploaderException(Exception):
    """Base exception for FYI Uploader"""
    pass

class ConfigurationError(FYIUploaderException):
    """Raised when configuration is invalid"""
    pass

class AuthenticationError(FYIUploaderException):
    """Raised when authentication fails"""
    pass

class AccountNotLinkedError(AuthenticationError):
    """Raised when trying to use an unlinked account"""
    pass

class TokenExpiredError(AuthenticationError):
    """Raised when access token has expired"""
    pass

class UploadError(FYIUploaderException):
    """Raised when upload fails"""
    def __init__(self, message: str, platform: str = None, video_path: str = None):
        self.platform = platform
        self.video_path = video_path
        super().__init__(message)

class RateLimitError(UploadError):
    """Raised when rate limit is hit"""
    def __init__(self, message: str, retry_after: int = None, platform: str = None):
        self.retry_after = retry_after
        super().__init__(message, platform=platform)

class VideoProcessingError(FYIUploaderException):
    """Raised when video processing fails"""
    pass

class VideoValidationError(FYIUploaderException):
    """Raised when video validation fails"""
    pass

class NetworkError(FYIUploaderException):
    """Raised when network request fails"""
    pass