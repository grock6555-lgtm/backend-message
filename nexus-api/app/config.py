from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_USER: str = "nexus_app"
    DB_PASSWORD: str = "app_secure_password_456"
    DB_NAME: str = "nexus_chat"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_secure_password_789"
    JWT_SECRET: str = "your_jwt_secret_change_me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    TOTP_SERVICE_URL: str = "http://totp-service:8001"
    BLACKLIST_SERVICE_URL: str = "http://blacklist-service:8002"
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minio_secure_password_123"
    MINIO_BUCKET: str = "attachments"
    KAFKA_HOST: str = "kafka:9092"
    ELASTICSEARCH_HOST: str = "http://elasticsearch:9200"
    LOG_SALT: str = "default_salt"

settings = Settings()