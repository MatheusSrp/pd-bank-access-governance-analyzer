from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    database_url: str = "sqlite:///pd_bank_analyzer.db"
    max_upload_mb: int = 50
    cors_origins: tuple = ()          # ("*",) ou lista de origens; vazio = CORS desligado
    api_key: str | None = None        # se definido, exige o cabeçalho X-API-Key em /api/* (exceto /api/health)
    timezone: str = "America/Sao_Paulo"

    @classmethod
    def from_env(cls, env=os.environ) -> "Settings":
        origins = tuple(o.strip() for o in env.get("CORS_ORIGINS", "").split(",") if o.strip())
        return cls(database_url=env.get("DATABASE_URL", cls.database_url),
                   max_upload_mb=int(env.get("MAX_UPLOAD_MB", cls.max_upload_mb)),
                   cors_origins=origins, api_key=env.get("API_KEY") or None,
                   timezone=env.get("APP_TIMEZONE", cls.timezone))
