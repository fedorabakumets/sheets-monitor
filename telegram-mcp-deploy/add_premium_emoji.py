#!/usr/bin/env python3
"""Insert Premium custom emoji into forum service-topic intro messages."""
from __future__ import annotations

import asyncio
import os
import sys

from telethon import TelegramClient, functions, types
from telethon.errors import FloodWaitError, RPCError
from telethon.sessions import StringSession

FORUM = -1003960409977
WANTED = ["📌", "✅", "🚫", "✨", "🔗", "📊", "📋", "💬", "🛡"]


def log(msg: str) -> None:
    print(msg, flush=True)


async def tg_call(client: TelegramClient, request):
    while True:
        try:
            return await client(request)
        except FloodWaitError as exc:
            wait = int(exc.seconds) + 1
            log(f"flood_wait {wait}s")
            await asyncio.sleep(wait)


def doc_alt(doc) -> str | None:
    for attr in getattr(doc, "attributes", []) or []:
        alt = getattr(attr, "alt", None)
        if alt:
            return alt
    return None


async def collect_ids(client: TelegramClient) -> dict[str, int]:
    found: dict[str, int] = {}

    try:
        pack = await tg_call(
            client,
            functions.messages.GetStickerSetRequest(
                stickerset=types.InputStickerSetEmojiDefaultTopicIcons(),
                hash=0,
            ),
        )
        for doc in pack.documents:
            alt = doc_alt(doc)
            if alt:
                found.setdefault(alt, int(doc.id))
                log(f"topic_icon {alt} {doc.id}")
    except Exception as exc:  # noqa: BLE001
        log(f"topic_icons_fail {type(exc).__name__}: {exc}")

    for alt in WANTED:
        if alt in found:
            continue
        try:
            result = await tg_call(
                client,
                functions.messages.SearchCustomEmojiRequest(emoticon=alt, hash=0),
            )
            ids = list(getattr(result, "document_id", []) or [])[:12]
            if not ids:
                log(f"search_empty {alt}")
                continue
            docs = await tg_call(
                client,
                functions.messages.GetCustomEmojiDocumentsRequest(document_id=ids),
            )
            picked = None
            for doc in docs:
                if doc_alt(doc) == alt:
                    picked = int(doc.id)
                    break
            if picked is None and ids:
                picked = int(ids[0])
            if picked:
                found[alt] = picked
                log(f"search {alt} {picked}")
        except Exception as exc:  # noqa: BLE001
            log(f"search_fail {alt} {type(exc).__name__}: {exc}")
    return found


def e(ids: dict[str, int], alt: str) -> str:
    eid = ids.get(alt)
    if not eid:
        return alt
    return f'<tg-emoji emoji-id="{eid}">{alt}</tg-emoji>'


def rules_html(ids: dict[str, int]) -> str:
    return (
        f"{e(ids, '📌')} Правила сообщества\n\n"
        "Сообщество по сайту мониторинга буксов\n"
        '<a href="https://fedorabakumets.github.io/sheets-monitor/">Заработок на кликах</a>\n\n'
        f"{e(ids, '✨')} <b>Фишка сообщества</b> — оно независимо от владельцев буксов. "
        "Это не официальные группы проектов и не их реклама: сравниваем сайты как есть, без заказных рейтингов.\n\n"
        "Ищете лучшие сайты для заработка онлайн? На "
        '<a href="https://fedorabakumets.github.io/sheets-monitor/">странице мониторинга</a> — '
        "сравнение сайтов по минимальной сумме вывода, реферальным системам, сложности регистрации "
        "и доступным платежным системам. Используйте фильтры и сортировку, чтобы выбрать подходящий вариант.\n\n"
        f"{e(ids, '✅')} <b>Что можно</b>\n"
        "• обсуждать сайты с мониторинга\n"
        "• писать в топик нужного букса\n"
        "• делиться опытом: регистрация, задания, вывод\n"
        f"• {e(ids, '🔗')} пиарить свои реф-ссылки на буксы с мониторинга — без спама\n\n"
        f"{e(ids, '🚫')} <b>Нельзя</b>\n"
        "• спамить рефками: флуд, копипаста в каждый топик, одинаковые сообщения пачкой\n"
        "• реклама сторонних проектов, которых нет на мониторинге\n"
        "• оскорбления и оффтоп"
    )


def news_html(ids: dict[str, int]) -> str:
    return (
        f"{e(ids, '📌')} Новости\n\n"
        f'{e(ids, "📊")} <a href="https://fedorabakumets.github.io/sheets-monitor/">Таблица мониторинга</a>\n'
        f'{e(ids, "📋")} <a href="https://fedorabakumets.github.io/sheets-monitor/all-changes.html">Все изменения</a>\n\n'
        "Последние изменения\n"
        "30.11.2025\n\n"
        "• Socpublic.com\n"
        "платёжные системы → WebMoney, Volet, Payeer, Epayments, Perfect Money\n\n"
        "• Wmrfast.com\n"
        "платёжные системы → Perfect Money, Epayments, Volet\n"
        "типы работы → Расширение, Тесты, Бонусы"
    )


def questions_html(ids: dict[str, int]) -> str:
    return (
        f"{e(ids, '📌')} Вопросы и предложения\n\n"
        f"{e(ids, '💬')} Сюда — вопросы и идеи по сайту\n"
        '<a href="https://fedorabakumets.github.io/sheets-monitor/">Заработок на кликах</a>\n\n'
        "Фильтры, сортировка, данные в таблице, новые буксы, ошибки на сайте."
    )


async def main() -> int:
    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session = os.environ["TELEGRAM_SESSION_STRING"]
    client = TelegramClient(StringSession(session), api_id, api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            log("NOT_AUTHORIZED")
            return 1
        me = await client.get_me()
        log(f"authorized @{getattr(me, 'username', None)} premium={getattr(me, 'premium', None)}")
        ids = await collect_ids(client)
        log(f"resolved {ids}")

        edits = [
            (10, rules_html(ids)),
            (11, news_html(ids)),
            (12, questions_html(ids)),
        ]
        for msg_id, html in edits:
            try:
                await client.edit_message(FORUM, msg_id, html, parse_mode="html")
                log(f"edit_ok {msg_id}")
            except RPCError as exc:
                log(f"edit_fail {msg_id} {type(exc).__name__}: {exc}")
        log("premium_emoji_done")
        return 0
    finally:
        await client.disconnect()
        log("disconnected")


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except Exception as exc:  # noqa: BLE001
        log(f"fatal {type(exc).__name__}: {exc}")
        sys.exit(1)
