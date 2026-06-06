from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from fluentogram import TranslatorHub, FluentTranslator
from fluent_compiler.bundle import FluentBundle

from database.requests import get_or_create_user

def create_translator_hub() -> TranslatorHub:
    """Загружает .ftl файлы и собирает их в хаб переводов"""
    return TranslatorHub(
        locales_map={
            "ru": ("ru", "en"),  # Если ключа нет в RU, бот возьмет его из EN
            "en": ("en",)
        },
        translators=[
            FluentTranslator(
                locale="ru",
                translator=FluentBundle.from_files(locale="ru-RU", filenames=["fluent_pages/ru/texts.ftl"])
            ),
            FluentTranslator(
                locale="en",
                translator=FluentBundle.from_files(locale="en-US", filenames=["fluent_pages/en/texts.ftl"])
            )
        ]
    )

class L10nMiddleware(BaseMiddleware):
    """Мидлварь для подтягивания языка и пользователя из БД"""
    def __init__(self, t_hub: TranslatorHub):
        self.t_hub = t_hub

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # 1. Получаем или создаем пользователя в базе
        db_user = await get_or_create_user(user.id, user.username)
        
        # 2. Достаем нужный словарь из хаба по коду языка (ru/en)
        translator = self.t_hub.get_translator_by_locale(db_user.language)

        # 3. Передаем объект перевода и объект юзера дальше в хэндлеры
        data["i18n"] = translator
        data["db_user"] = db_user 
        
        return await handler(event, data)