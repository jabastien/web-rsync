from pydantic import computed_field
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    data_dir: Path = Path("./data")
    max_concurrent_jobs: int = 3
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env"}

    @computed_field
    @property
    def db_path(self) -> str:
        return str(self.data_dir / "web_rsync.db")

    @computed_field
    @property
    def log_dir(self) -> Path:
        return self.data_dir / "logs"

    @computed_field
    @property
    def ssh_dir(self) -> Path:
        return self.data_dir / "ssh"


settings = Settings()
