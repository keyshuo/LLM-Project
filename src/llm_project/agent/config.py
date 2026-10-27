from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    openai_api_key: str | None = None
    openai_base_url: str | None = None

    @model_validator(mode="after")
    def _check_required(self):
        missing: list[str] = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if missing:
            raise SystemExit(
                "\n[配置错误] 缺少必要环境变量: "
                + ", ".join(missing)
                + "\n请检查项目根目录的 .env 文件，例如：\n"
                "  OPENAI_API_KEY=ollama\n"
                "  OPENAI_BASE_URL=http://localhost:11434/v1\n"
            )
        return self


settings = Settings()