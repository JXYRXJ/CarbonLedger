import os
from typing import List, Union
from pydantic import AnyHttpUrl, BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated


def parse_cors_origins(v: Union[str, List[str]]) -> List[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "CarbonLedger API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/carbonledger",
        env="DATABASE_URL",
    )

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # URLs
    BACKEND_URL: str = Field(default="http://localhost:8000", env="BACKEND_URL")
    FRONTEND_URL: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    RENDER_EXTERNAL_URL: str = Field(default="", env="RENDER_EXTERNAL_URL")

    # CORS origins
    # Parsed list of URLs allowed to connect
    BACKEND_CORS_ORIGINS: Annotated[
        List[str], BeforeValidator(parse_cors_origins)
    ] = [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:3000",
    ]

    # Blockchain configuration
    BLOCKCHAIN_ENABLED: bool = Field(default=True, env="BLOCKCHAIN_ENABLED")
    WEB3_PROVIDER_URL: str = Field(default="http://localhost:8545", env="WEB3_PROVIDER_URL")
    CHAIN_ID: int = Field(default=1337, env="CHAIN_ID")
    PRIVATE_KEY: str = Field(default="", env="PRIVATE_KEY")
    WALLET_ADDRESS: str = Field(default="", env="WALLET_ADDRESS")
    CONTRACT_ADDRESS: str = Field(default="", env="CONTRACT_ADDRESS")
    BLOCK_CONFIRMATIONS: int = Field(default=1, env="BLOCK_CONFIRMATIONS")
    GAS_LIMIT: int = Field(default=3000000, env="GAS_LIMIT")
    MAX_GAS_PRICE: int = Field(default=100000000000, env="MAX_GAS_PRICE")

    # Caching and Performance
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    MAX_CONTENT_LENGTH: int = Field(default=10485760, env="MAX_CONTENT_LENGTH")  # 10MB

    @property
    def cors_origins(self) -> List[str]:
        origins = list(self.BACKEND_CORS_ORIGINS)
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        if self.RENDER_EXTERNAL_URL and self.RENDER_EXTERNAL_URL not in origins:
            origins.append(self.RENDER_EXTERNAL_URL)
        # Add Vercel subdomains dynamically in cors check or explicitly add them here if static
        return origins

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() == "testing"


# Create settings instance
# In testing mode, we can override settings or load from separate test env files
settings = Settings()
