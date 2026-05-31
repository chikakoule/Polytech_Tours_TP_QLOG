"""Configuration de l'application, chargée depuis l'environnement (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de données
    database_url: str = "sqlite:///./padel_corpo.db"

    # Sécurité
    secret_key: str = "dev-secret-key-change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 heures

    # CORS
    allowed_origins: str = "http://localhost:5173"

    # Upload
    upload_dir: str = "./uploads"
    max_upload_size: int = 2_097_152  # 2 Mo

    # Anti-brute force
    max_login_attempts: int = 5
    lockout_minutes: int = 30

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
