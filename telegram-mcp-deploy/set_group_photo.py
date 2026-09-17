#!/usr/bin/env python3
"""Set the monitoring forum avatar from the committed JPEG."""
from __future__ import annotations

import asyncio
import os
import sys
from urllib.request import urlretrieve

from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession

FORUM = -1003960409977
PHOTO_URL = os.environ.get(
    "GROUP_AVATAR_URL",
    "https://raw.githubusercontent.com/fedorabakumets/sheets-monitor/cursor/telegram-mcp-railway-cfe5/telegram-mcp-deploy/group_avatar.jpg",
)
PHOTO_PATH = "/tmp/group_avatar.jpg"


def log(msg: str) -> None:
    print(msg, flush=True)


async def main() -> int:
    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session = os.environ["TELEGRAM_SESSION_STRING"]
    log(f"download {PHOTO_URL}")
    urlretrieve(PHOTO_URL, PHOTO_PATH)
    log(f"saved {PHOTO_PATH} bytes={os.path.getsize(PHOTO_PATH)}")

    client = TelegramClient(StringSession(session), api_id, api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            log("NOT_AUTHORIZED")
            return 1
        me = await client.get_me()
        log(f"authorized @{getattr(me, 'username', None)}")
        uploaded = await client.upload_file(PHOTO_PATH, file_name="group_avatar.jpg")
        await client(
            functions.channels.EditPhotoRequest(
                channel=FORUM,
                photo=types.InputChatUploadedPhoto(file=uploaded),
            )
        )
        log("photo_ok")
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
