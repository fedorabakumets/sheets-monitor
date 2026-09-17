#!/usr/bin/env python3
"""One-shot: delete specific forum topics, then exit so telegram-mcp can start."""
import asyncio
import os
import sys

from telethon import TelegramClient, functions
from telethon.sessions import StringSession

CHAT_ID = -1003960409977
TOPIC_IDS = (8, 56)  # Webofsar, ProfitLine


async def main() -> int:
    print("delete_topics_start", flush=True)
    session = os.environ.get("TELEGRAM_SESSION_STRING")
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    if not session or not api_id or not api_hash:
        print("delete_topics_skip missing_env", flush=True)
        return 0

    client = TelegramClient(StringSession(session), int(api_id), api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        print("delete_topics_skip not_authorized", flush=True)
        await client.disconnect()
        return 0

    peer = await client.get_input_entity(CHAT_ID)
    for topic_id in TOPIC_IDS:
        try:
            await client(
                functions.messages.DeleteTopicHistoryRequest(
                    peer=peer, top_msg_id=topic_id
                )
            )
            print("deleted_topic", topic_id, flush=True)
        except Exception as exc:
            print("fail_delete", topic_id, type(exc).__name__, str(exc)[:200], flush=True)
            try:
                await client(
                    functions.messages.EditForumTopicRequest(
                        peer=peer, topic_id=topic_id, hidden=True
                    )
                )
                print("hidden_topic", topic_id, flush=True)
            except Exception as hide_exc:
                print(
                    "fail_hide",
                    topic_id,
                    type(hide_exc).__name__,
                    str(hide_exc)[:200],
                    flush=True,
                )

    try:
        topics = await client(
            functions.messages.GetForumTopicsRequest(
                peer=peer,
                offset_date=None,
                offset_id=0,
                offset_topic=0,
                limit=100,
            )
        )
        leftover = [
            (t.id, t.title)
            for t in topics.topics
            if t.id in TOPIC_IDS
            or "Webofsar" in (t.title or "")
            or "ProfitLine" in (t.title or "")
        ]
        print("leftover_topics", leftover, flush=True)
    except Exception as exc:
        print("fail_list", type(exc).__name__, str(exc)[:200], flush=True)

    await client.disconnect()
    print("delete_topics_done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
