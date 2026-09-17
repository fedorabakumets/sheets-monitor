#!/usr/bin/env python3
"""Create a custom emoji pack from bux favicons and set them as forum topic icons."""
from __future__ import annotations

import asyncio
import io
import os
import sys
from urllib.request import Request, urlopen

from PIL import Image
from telethon import TelegramClient, functions, types
from telethon.errors import FloodWaitError, RPCError
from telethon.sessions import StringSession

FORUM = -1003960409977
PACK_TITLE = "Буксы — логотипы"
PACK_SHORT = os.environ.get("LOGO_PACK_SHORT", "buxmonitor_logos")
USER_AGENT = "Mozilla/5.0 (compatible; BuxMonitor/1.0)"

# (domain, topic_id, title) — current monitoring forum, ProfitLine/Webofsar already removed.
SITES = [
    ("socpublic.com", 5, "Socpublic"),
    ("wmrfast.com", 6, "WMRFast"),
    ("profitcentr.com", 7, "Profitcentr"),
    ("fomoearn.com", 29, "FomoEarn"),
    ("apex-click.pro", 30, "Apex-Click"),
    ("web-ip.ru", 31, "Web-Ip"),
    ("buxora.ru", 32, "Buxora"),
    ("serfearn.com", 33, "SerfEarn"),
    ("ipweb.ru", 34, "IpWeb"),
    ("webprofi.site", 35, "WebProfi"),
    ("seo-fast.ru", 36, "Seo-Fast"),
    ("seo-springs.ru", 37, "Seo-Springs"),
    ("dimbux.best", 38, "DimBux"),
    ("seotime.biz", 39, "SeoTime"),
    ("coinli.net", 40, "Coinli"),
    ("asmos.top", 41, "Asmos"),
    ("doxodcenter.ru", 42, "DoxodCenter"),
    ("legacash.com", 43, "LegaCash"),
    ("broserf.ru", 44, "BroSerf"),
    ("yu.su", 45, "Yu.Su"),
    ("seo-task.com", 47, "Seo-Task"),
    ("makeyoutask.com", 48, "MakeYouTask"),
    ("d-umpz.ru", 49, "D-Umpz"),
    ("euroads.biz", 50, "EuroAds"),
    ("adsrek.com", 51, "AdsRek"),
    ("adseopro.com", 52, "AdSeoPro"),
    ("heedyou.com", 53, "HeedYou"),
    ("clickora.tokyo", 54, "Clickora"),
    ("toniabux.com", 55, "ToniaBux"),
    ("adsvision.ru", 57, "AdsVision"),
    ("buxnova.net", 58, "BuxNova"),
    ("sobux.ru", 59, "SoBux"),
    ("adbtc.top", 60, "Adbtc"),
    ("profithub.place", 61, "ProfitHub"),
    ("vboost.ru", 62, "Vboost"),
    ("seotarget.su", 63, "SeoTarget"),
    ("buxseo.ru", 64, "BuxSeo"),
    ("buxfor.ru", 65, "Buxfor"),
    ("advbux.ru", 66, "AdvBux"),
    ("profitserfing.ru", 67, "ProfitSerfing"),
    ("bonus-serf.in", 68, "Bonus-Serf"),
    ("paymer.fun", 69, "Paymer"),
    ("rubprofit.ru", 70, "RubProfit"),
    ("mnmix.ru", 71, "Mnmix"),
    ("prodvisots.ru", 72, "ProdVisots"),
    ("inves-next.ru", 73, "Inves-Next"),
    ("exellent.site", 74, "Exellent"),
    ("seo-24.ru", 75, "Seo-24"),
    ("buxo.monster", 76, "BuxoMonster"),
    ("mjpublic.com", 77, "MjPublic"),
    ("biq1.ru", 78, "Biq1"),
    ("rewardjoy.com", 79, "RewardJoy"),
    ("wmzona.com", 80, "WmZona"),
    ("aviso.bz", 81, "Aviso"),
    ("delionix.com", 82, "Delionix"),
    ("ads.uap.company", 83, "AdsByUap"),
    ("neobux.com", 84, "NeoBux"),
    ("wmmail.ru", 85, "Wmmail"),
    ("seosprint.net", 86, "SEOsprint"),
]


def log(msg: str) -> None:
    print(msg, flush=True)


def http_get(url: str, timeout: int = 12) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def icon_urls(host: str) -> list[str]:
    return [
        f"https://www.google.com/s2/favicons?sz=128&domain={host}",
        f"https://www.google.com/s2/favicons?sz=64&domain={host}",
        f"https://icons.duckduckgo.com/ip3/{host}.ico",
        f"https://www.google.com/s2/favicons?sz=32&domain={host}",
        f"https://{host}/apple-touch-icon.png",
        f"https://{host}/favicon.ico",
        f"https://{host}/favicon.png",
    ]


def largest_frame(im: Image.Image) -> Image.Image:
    best = im.copy()
    idx = 0
    while True:
        try:
            im.seek(idx)
        except EOFError:
            break
        if max(im.size) >= max(best.size):
            best = im.copy()
        idx += 1
    return best


def to_emoji_png(data: bytes) -> bytes:
    im = Image.open(io.BytesIO(data))
    im = largest_frame(im).convert("RGBA")
    box = 88
    w, h = im.size
    scale = box / max(w, h)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    resample = Image.Resampling.NEAREST if max(w, h) <= 48 else Image.Resampling.LANCZOS
    im = im.resize((nw, nh), resample)
    canvas = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    canvas.paste(im, ((100 - nw) // 2, (100 - nh) // 2), im)
    out = io.BytesIO()
    canvas.save(out, format="PNG", optimize=True)
    return out.getvalue()


def fetch_icon(host: str) -> bytes:
    best: tuple[int, bytes] | None = None
    last_err = "no sources"
    for url in icon_urls(host):
        try:
            raw = http_get(url)
            if not raw or len(raw) < 40:
                continue
            im = Image.open(io.BytesIO(raw))
            im = largest_frame(im)
            score = min(im.size) * 100 + min(len(raw), 20000) / 50
            if best is None or score > best[0]:
                best = (int(score), raw)
            if min(im.size) >= 64:
                break
        except Exception as exc:  # noqa: BLE001 — probe many URLs
            last_err = f"{type(exc).__name__}: {exc}"
    if best is None:
        raise RuntimeError(f"no favicon for {host}: {last_err}")
    return to_emoji_png(best[1])


async def tg_call(client: TelegramClient, request):
    while True:
        try:
            return await client(request)
        except FloodWaitError as exc:
            wait = int(exc.seconds) + 1
            log(f"flood_wait {wait}s")
            await asyncio.sleep(wait)


def edit_forum_topic_cls():
    if hasattr(functions.messages, "EditForumTopicRequest"):
        return functions.messages.EditForumTopicRequest
    return functions.channels.EditForumTopicRequest


def keyword_map(sticker_set) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for item in getattr(sticker_set, "keywords", []) or []:
        words = list(getattr(item, "keyword", []) or [])
        if words:
            mapping[words[0]] = int(item.document_id)
    return mapping


async def upload_png(client: TelegramClient, png: bytes, filename: str) -> types.InputDocument:
    uploaded = await client.upload_file(png, file_name=filename)
    media = await tg_call(
        client,
        functions.messages.UploadMediaRequest(
            peer="me",
            media=types.InputMediaUploadedDocument(
                file=uploaded,
                mime_type="image/png",
                attributes=[
                    types.DocumentAttributeFilename(file_name=filename),
                    types.DocumentAttributeImageSize(w=100, h=100),
                ],
            ),
        ),
    )
    doc = media.document
    return types.InputDocument(
        id=doc.id,
        access_hash=doc.access_hash,
        file_reference=doc.file_reference,
    )


async def get_pack(client: TelegramClient, short_name: str):
    try:
        return await tg_call(
            client,
            functions.messages.GetStickerSetRequest(
                stickerset=types.InputStickerSetShortName(short_name=short_name),
                hash=0,
            ),
        )
    except RPCError:
        return None


async def create_or_fill_pack(client: TelegramClient, items: list[types.InputStickerSetItem], me) -> object:
    existing = await get_pack(client, PACK_SHORT)
    if existing is not None:
        have = keyword_map(existing)
        log(f"pack_exists {PACK_SHORT} docs={len(existing.documents)} keywords={len(have)}")
        missing = []
        have_hosts = set(have)
        for it in items:
            host = (it.keywords or "").split(",")[0].strip()
            if host and host not in have_hosts:
                missing.append(it)
        for it in missing:
            existing = await tg_call(
                client,
                functions.stickers.AddStickerToSetRequest(
                    stickerset=types.InputStickerSetShortName(short_name=PACK_SHORT),
                    sticker=it,
                ),
            )
            log(f"added_sticker {it.keywords}")
            await asyncio.sleep(0.4)
        return existing

    log(f"creating_pack {PACK_SHORT} stickers={len(items)}")
    try:
        return await tg_call(
            client,
            functions.stickers.CreateStickerSetRequest(
                user_id=me,
                title=PACK_TITLE,
                short_name=PACK_SHORT,
                stickers=items,
                emojis=True,
            ),
        )
    except RPCError as exc:
        log(f"create_batch_fail {type(exc).__name__}: {exc}")
        first, rest = items[0], items[1:]
        created = await tg_call(
            client,
            functions.stickers.CreateStickerSetRequest(
                user_id=me,
                title=PACK_TITLE,
                short_name=PACK_SHORT,
                stickers=[first],
                emojis=True,
            ),
        )
        log("created_pack_first")
        for it in rest:
            created = await tg_call(
                client,
                functions.stickers.AddStickerToSetRequest(
                    stickerset=types.InputStickerSetShortName(short_name=PACK_SHORT),
                    sticker=it,
                ),
            )
            log(f"added_sticker {it.keywords}")
            await asyncio.sleep(0.35)
        return created


async def apply_topic_icons(client: TelegramClient, host_to_emoji_id: dict[str, int]) -> None:
    edit = edit_forum_topic_cls()
    for host, topic_id, name in SITES:
        emoji_id = host_to_emoji_id.get(host)
        if not emoji_id:
            log(f"icon_skip {name} {host} no_emoji_id")
            continue
        try:
            await tg_call(
                client,
                edit(peer=FORUM, topic_id=topic_id, icon_emoji_id=emoji_id),
            )
            log(f"icon_ok {name} topic={topic_id} emoji_id={emoji_id}")
        except RPCError as exc:
            if "TOPIC_NOT_MODIFIED" in str(exc):
                log(f"icon_same {name} topic={topic_id}")
            else:
                log(f"icon_fail {name} topic={topic_id} {type(exc).__name__}: {exc}")
        await asyncio.sleep(0.25)


async def main() -> int:
    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session = os.environ["TELEGRAM_SESSION_STRING"]
    log(f"logo_pack_start sites={len(SITES)} short={PACK_SHORT}")

    pngs: list[tuple[str, int, str, bytes]] = []
    for host, topic_id, name in SITES:
        try:
            png = fetch_icon(host)
            pngs.append((host, topic_id, name, png))
            log(f"favicon_ok {name} {host} bytes={len(png)}")
        except Exception as exc:  # noqa: BLE001
            log(f"favicon_fail {name} {host} {type(exc).__name__}: {exc}")

    if not pngs:
        log("no_favicons")
        return 1

    client = TelegramClient(StringSession(session), api_id, api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            log("NOT_AUTHORIZED")
            return 1
        me = await client.get_me()
        log(f"authorized @{getattr(me, 'username', None)} premium={getattr(me, 'premium', None)}")

        items: list[types.InputStickerSetItem] = []
        for host, topic_id, name, png in pngs:
            input_doc = await upload_png(client, png, f"{host}.png")
            items.append(
                types.InputStickerSetItem(
                    document=input_doc,
                    emoji="💰",
                    keywords=host,
                )
            )
            log(f"uploaded {name} {host}")
            await asyncio.sleep(0.25)

        sticker_set = await create_or_fill_pack(client, items, me)
        host_to_id = keyword_map(sticker_set)
        if len(host_to_id) < len(pngs):
            # fallback: documents are in insertion order
            log(f"keyword_map_partial {len(host_to_id)}/{len(pngs)} — using document order")
            for (host, _tid, _name, _png), doc in zip(pngs, sticker_set.documents):
                host_to_id.setdefault(host, int(doc.id))

        log(f"pack_ready https://t.me/addemoji/{PACK_SHORT} mapped={len(host_to_id)}")
        await apply_topic_icons(client, host_to_id)
        log("logo_pack_done")
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
