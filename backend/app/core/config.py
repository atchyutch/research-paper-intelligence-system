from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_V1_PREFIX: str = "/api/v1"
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DB: str

    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX_NAME: str = "rpis-index"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    EMBEDDINGS_MODEL:str = "intfloat/e5-large-v2"

    R2_ACCESS_TOKEN: str | None = None
    R2_SECRET_ACCESS_KEY: str | None = None
    R2_AWS_S3_ENDPOINT:str | None = None
    R2_BUCKET_NAME:str |None = None




settings = Settings()