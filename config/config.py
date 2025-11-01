from pathlib import Path
from pydantic_settings import BaseSettings

ENV_FILE = Path(__file__).parent.parent / ".env"

class Settings(BaseSettings):
    TOKEN: str
    APPLICATION_ID: int
    GUILD_ID: int
    TICKET_CHANNEL_ID: int
    TRANSCRIPT_CHANNEL_ID: int
    WELCOME_CHANNEL_ID: int
    LOGS_CHANNEL_WELCOME: int
    AUTO_ROLE_ID: int
    # Leemos como string y convertimos después
    SOPORTE_ROLES: str
    MODERATOR_ROLES: str
    ADMINISTRADOR_ROLES: str
    STAFF_ROLES: str

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"

    # Propiedades que devuelven listas de enteros
    @property
    def soporte_roles_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.SOPORTE_ROLES.split(",") if x.strip().isdigit()]

    @property
    def moderator_roles_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.MODERATOR_ROLES.split(",") if x.strip().isdigit()]

    @property
    def administrador_roles_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.ADMINISTRADOR_ROLES.split(",") if x.strip().isdigit()]

    @property
    def staff_roles_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.STAFF_ROLES.split(",") if x.strip().isdigit()]

Config = Settings()
