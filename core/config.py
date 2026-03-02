import os


class Settings:
    # Environment
    ENV = os.getenv("ENV", "development")
    DEBUG = ENV != "production"

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autoforge.db")

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")


settings = Settings()
