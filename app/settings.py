from functools import lru_cache
from typing import Dict

from cryptography.fernet import Fernet
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core settings
    cors_origins: str = "*"
    secret_key: str = "change me in .env"
    access_token_expire_minutes: int = 120

    # Database variables (Overwrite in .env file)
    db_user: str = "<USER>"
    db_password: str = "<PASSWORD>"
    db_address: str = "localhost"
    db_port: str = "5432"
    db_name: str = "<DATABASE>"

    # Test database variables
    test_db_user: str = "<USER-TEST>"
    test_db_password: str = "<PASSWORD-TEST>"
    test_db_address: str = "localhost"
    test_db_port: str = "5432"
    test_db_name: str = "<DATABASE-TEST>"

    admin_pages_enabled: bool = False
    admin_pages_route: str = "/admin"
    admin_pages_title: str = "API Administration"
    admin_pages_encryption_key: str = Field(
        default_factory=lambda: Fernet.generate_key().decode(),
        description="Encryption key for admin session tokens",
    )
    admin_pages_timeout: int = 86400

    # Metadata variables
    title: str = "API Template"
    description: str = "This is a simple api template for simple projects"
    version: str = "v1"
    repository: str = "https://github.com/abdurasuloff/fastapi-template"
    license_info: Dict[str, str] = {"name": "MIT", "url": "https://opensource.org/licenses/MIT"}
    contact: Dict[str, str] = {"name": "Arabov Muhammadjon", "url": "https://www.arabov.uz"}
    email: str = "arabovmuhammadjon13@gmail.com"
    year: str = "2025"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


@lru_cache
def get_settings() -> Settings:
    return Settings()
