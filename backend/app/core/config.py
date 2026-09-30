from datetime import time
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://booking:booking@localhost:5433/booking"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin12345"
    jwt_secret: str = "dev-secret-change-me-in-production-0123456789"
    cookie_secure: bool = False
    access_ttl_minutes: int = 15
    refresh_ttl_days: int = 7
    max_failed_attempts: int = 5
    lockout_minutes: int = 15
    org_timezone: str = "Europe/Moscow"
    work_start: time = time(8)
    work_end: time = time(20)

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.org_timezone)


settings = Settings()
