# Telegram MCP для мониторинга буксов

HTTP-обёртка над [telegram-mcp](https://github.com/chigwell/telegram-mcp) для Cursor Cloud Agent. Живёт на Railway, чтобы Linux-агент мог управлять форумом через MCP, не поднимая второй Telethon-клиент на той же сессии.

Сайт мониторинга: https://fedorabakumets.github.io/sheets-monitor/

## Что уже настроено

| Что | Значение |
|-----|----------|
| Форум | «Заработок на кликах — Мониторинг буксов и проектов» |
| Chat ID | `-1003960409977` |
| Инвайт | https://t.me/+P3cYOJvirHVmZWYy |
| Пак логотипов | https://t.me/addemoji/buxmonitor_logos |
| Railway MCP | `https://telegram-mcp-production-3889.up.railway.app/mcp` |

Топики буксов используют кастомные эмодзи из пака как иконки (те же фавиконки, что Google показывает на сайте).

## Файлы

| Файл | Зачем |
|------|--------|
| `Dockerfile` | Образ: клонирует telegram-mcp и запускает HTTP MCP |
| `railway.toml` | Команда старта на Railway |
| `group_avatar.jpg` | Аватарка форума (дашборд + клик + ₽) |
| `create_logo_pack.py` | Скачивает фавиконки, собирает emoji-пак, ставит иконки топиков |
| `set_group_photo.py` | Ставит `group_avatar.jpg` аватаркой группы |
| `add_premium_emoji.py` | Вставляет Premium-эмодзи в intro Правила / Новости / Вопросы |

Скрипты `*_pack.py` / `set_*.py` / `add_*.py` — **one-shot**. Их нельзя оставлять в `startCommand` навсегда: при каждом рестарте контейнера они снова полезут в Telegram API. После прогона startCommand возвращают к обычному MCP.

## Переменные Railway

Имена, без значений:

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SESSION_STRING` — StringSession, одна на аккаунт
- `MCP_TRANSPORT=http`
- `MCP_HOST=0.0.0.0`
- `MCP_ALLOWED_HOSTS`
- `DEPLOY_EPOCH` — технический флаг, чтобы форсировать новый деплой после смены startCommand

Сессию держит **только Railway**. Второй Telethon с тем же `SESSION_STRING` (локально или на VPS) ломает MCP ошибками вроде `AuthKeyDuplicated` / «146 bytes read».

## Как гонять one-shot

1. Закоммитить скрипт в эту папку и запушить ветку.
2. На сервисе telegram-mcp выставить `startCommand`: скачать скрипт с GitHub raw → `python3 /tmp/....py` → `exec telegram-mcp`.
3. Сменить `DEPLOY_EPOCH`, чтобы Railway реально взял новый startCommand (`redeploy` часто повторяет старый).
4. По логам дождаться `*_done` / `photo_ok` / `icon_ok`.
5. Вернуть startCommand на чистый MCP и снова сменить `DEPLOY_EPOCH`.

Пример чистого старта:

```sh
export MCP_TRANSPORT=http MCP_HOST=0.0.0.0 MCP_PORT=$PORT
exec telegram-mcp
```

## Cursor MCP

В настройках агента telegram-mcp должен смотреть на HTTP URL Railway, не на stdio Windows-клиент.

Google Sheets (официальный remote MCP): `https://sheetsmcp.googleapis.com/mcp/v1`. Таблица мониторинга: `1-_Qzi00wtezoZSnNiAhgvXJFhBE4x7LhyihTHtZgXv4`.
