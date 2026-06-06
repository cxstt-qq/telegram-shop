from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str
    admin_ids: str
    database_url: str = "sqlite+aiosqlite:///shop_database.db"
    crypto_bot_token: str
    
    # Новые переменные для Bybit
    bybit_api_key: str
    bybit_api_secret: str
    bybit_uid: str

    @property
    def admins(self) -> list[int]:
        return [int(admin_id.strip()) for admin_id in self.admin_ids.split(',')]

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

config = Settings()