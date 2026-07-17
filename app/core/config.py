"""
Configuration module for the application.

This module defines the environment-based configuration settings for the system,
including database connectivity, JWT authentication secrets, mail configurations,
and general application environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.

    Attributes:
        DATABASE_URL (str): The connection string for the primary database.
        JWT_SECRET_KEY (str): The secret key used to sign JSON Web Tokens.
        ALGORITHM (str): The cryptographic algorithm used for JWTs.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Minutes until the access token expires.
        REFRESH_TOKEN_EXPIRE_DAYS (int): Days until the refresh token expires.
        POSTGRES_USER (str): The username for the PostgreSQL database.
        POSTGRES_PASSWORD (str): The password for the PostgreSQL database.
        POSTGRES_DB (str): The name of the PostgreSQL database.
        MAIL_USERNAME (str): Username for authenticating with the SMTP server.
        MAIL_PASSWORD (str): Password for authenticating with the SMTP server.
        MAIL_FROM (str): Default sender email address for outgoing emails.
        MAIL_PORT (int): The port number for the SMTP server.
        MAIL_SERVER (str): The SMTP server hostname.
        MAIL_STARTTLS (bool): Whether to use STARTTLS for email transmission.
        MAIL_SSL_TLS (bool): Whether to use SSL/TLS for email transmission.
        MAIL_FROM_NAME (str): Display name for the outgoing sender.
        ADMIN_EMAIL (str): Email address of the system administrator.
        ADMIN_PASSWORD (str): Password of the system administrator.
        ENV (str): Current execution environment (e.g., 'development', 'production').
        LOG_LEVEL (str): Global logging level (e.g., 'DEBUG', 'INFO').
        SQL_ECHO (bool): Whether SQLAlchemy should echo executed SQL queries.
    """

    DATABASE_URL: str
    JWT_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    MAIL_FROM_NAME: str
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ENV: str
    LOG_LEVEL: str
    SQL_ECHO: bool
    REDIS_URL: str
    PERMISSION_CACHE_TTL: int
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    Retrieve cached application settings.

    Uses `functools.lru_cache` to ensure the settings are only parsed from the
    environment variables once during application startup, preventing overhead.

    Returns:
        Settings: The loaded application configuration settings.
    """
    return Settings()
