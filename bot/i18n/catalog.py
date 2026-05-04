from __future__ import annotations

# ru: current product copy. en: UI translation.
STRINGS: dict[str, dict[str, str]] = {
    "inline.main.open_app": {
        "ru": "Открыть .sound",
        "en": "Open .sound",
    },
    "inline.main.player": {
        "ru": "Плеер",
        "en": "Player",
    },
    "inline.main.profile": {
        "ru": "Профиль",
        "en": "Profile",
    },
    "inline.main.about": {
        "ru": "О проекте .sound",
        "en": "About .sound",
    },
    "inline.main.login_history": {
        "ru": "История входов",
        "en": "Sign-in history",
    },
    "inline.about.features": {
        "ru": "Возможности",
        "en": "Features",
    },
    "inline.about.tech": {
        "ru": "Технологии",
        "en": "Tech",
    },
    "inline.about.upload": {
        "ru": "Загрузка музыки",
        "en": "Upload",
    },
    "inline.about.import": {
        "ru": "Импорт из TG",
        "en": "Import from TG",
    },
    "inline.about.opensource": {
        "ru": "Открытый код",
        "en": "Open source",
    },
    "inline.about.roadmap": {
        "ru": "Планы",
        "en": "Roadmap",
    },
    "inline.back.about": {
        "ru": "← Назад к разделам",
        "en": "← Back to topics",
    },
    "inline.back.menu": {
        "ru": "← Назад в меню",
        "en": "← Back to menu",
    },
    "inline.profile.open": {
        "ru": "Открыть профиль",
        "en": "Open profile",
    },
    "inline.open_sound": {
        "ru": "Открыть .sound",
        "en": "Open .sound",
    },
    "inline.listen": {
        "ru": "Слушать",
        "en": "Listen",
    },
    "inline.create_playlist": {
        "ru": "＋ Создать плейлист",
        "en": "＋ New playlist",
    },
    "inline.player.my": {
        "ru": "Мои треки",
        "en": "My tracks",
    },
    "inline.player.liked": {
        "ru": "Лайки",
        "en": "Likes",
    },
    "inline.player.feed": {
        "ru": "Лента",
        "en": "Feed",
    },
    "inline.player.follows": {
        "ru": "Подписки",
        "en": "Subscriptions",
    },
    "inline.player.more3": {
        "ru": "Ещё 3 →",
        "en": "3 more →",
    },
    "inline.player.back_main": {
        "ru": "← Главное меню",
        "en": "← Main menu",
    },
    "inline.help.search": {
        "ru": "Поиск",
        "en": "Search",
    },
    "inline.help.stats": {
        "ru": "Моя статистика",
        "en": "My stats",
    },
    "base.friend": {
        "ru": "друг",
        "en": "friend",
    },
    "base.welcome": {
        "ru": (
            "Привет, <b>{name}</b>!\n\n"
            "Добро пожаловать в <b>.sound</b> — "
            "музыка без рекламы.\n"
            "Слушай. Делись. Открывай."
        ),
        "en": (
            "Hi, <b>{name}</b>!\n\n"
            "Welcome to <b>.sound</b> — "
            "music without ads.\n"
            "Listen. Share. Discover."
        ),
    },
    "base.about.title": {
        "ru": (
            " <b>О проекте .sound</b>\n\n"
            "Музыкальная платформа без рекламы "
            "в Telegram.\n"
            "Выбери раздел:"
        ),
        "en": (
            " <b>About .sound</b>\n\n"
            "A music platform without ads "
            "in Telegram.\n"
            "Choose a section:"
        ),
    },
    "base.section_missing": {
        "ru": "Раздел не найден",
        "en": "Section not found",
    },
    "base.profile.load_error": {
        "ru": "Не удалось загрузить профиль. Попробуй позже.",
        "en": "Could not load profile. Try again later.",
    },
    "base.login.load_error": {
        "ru": "Не удалось загрузить историю. Попробуй позже.",
        "en": "Could not load history. Try again later.",
    },
    "base.login.empty": {
        "ru": " <b>История входов</b>\n\nНет записей о входах.",
        "en": " <b>Sign-in history</b>\n\nNo sign-in events yet.",
    },
    "base.login.header": {
        "ru": " <b>История входов</b>\n",
        "en": " <b>Sign-in history</b>\n",
    },
    "base.login.footer": {
        "ru": "\n<i>Последние 10 входов</i>",
        "en": "\n<i>Last 10 sign-ins</i>",
    },
    "base.help": {
        "ru": (
            "Что умеет .sound:\n\n"
            " <b>Плеер</b> — слушай прямо в Telegram\n"
            " <b>Поиск</b> — введи название\n"
            "▤ <b>Плейлисты</b> — создавай подборки\n"
            " <b>Лайки</b> — сохраняй треки\n"
            " <b>Профиль</b> — статистика\n"
            "/mystats — статистика в чате"
        ),
        "en": (
            "What .sound can do:\n\n"
            " <b>Player</b> — listen in Telegram\n"
            " <b>Search</b> — type a name\n"
            "▤ <b>Playlists</b> — your collections\n"
            " <b>Likes</b> — save tracks\n"
            " <b>Profile</b> — stats\n"
            "/mystats — stats in chat"
        ),
    },
    "base.playlists.empty": {
        "ru": (
            "У тебя пока нет плейлистов.\n"
            "Открой плеер и создай первый!"
        ),
        "en": (
            "You have no playlists yet.\n"
            "Open the player and create one!"
        ),
    },
    "base.playlists.error": {
        "ru": "Не удалось загрузить плейлисты.",
        "en": "Could not load playlists.",
    },
    "base.cmd_profile.error": {
        "ru": "Не удалось загрузить профиль.",
        "en": "Could not load profile.",
    },
    "fmt.label.my": {
        "ru": "Мои треки",
        "en": "My tracks",
    },
    "fmt.label.liked": {
        "ru": "Лайки",
        "en": "Likes",
    },
    "fmt.label.feed": {
        "ru": "Лента",
        "en": "Feed",
    },
    "fmt.label.follows": {
        "ru": "Подписки",
        "en": "Subscriptions",
    },
    "fmt.header": {
        "ru": " <b>Плеер — {label}</b>\n",
        "en": " <b>Player — {label}</b>\n",
    },
    "fmt.tracks_range": {
        "ru": "Треки {start}–{end} из {total}\n",
        "en": "Tracks {start}–{end} of {total}\n",
    },
    "fmt.untitled": {
        "ru": "Без названия",
        "en": "Untitled",
    },
    "fmt.empty": {
        "ru": "Нет треков.",
        "en": "No tracks.",
    },
    "base.about.features": {
        "ru": (
            " <b>Возможности .sound</b>\n\n"
            ".sound — музыкальная платформа нового "
            "поколения прямо в Telegram. "
            "Без рекламы, без подписок.\n\n"
            "— Загружай свои треки\n"
            "— Слушай в Mini App\n"
            "— HLS, адаптация под сеть\n"
            "— Обложки, лайки, плейлисты, поиск\n"
            "— Текст песен, профиль автора, лента"
        ),
        "en": (
            " <b>.sound features</b>\n\n"
            "A new-generation music platform in Telegram. "
            "No ads, no paywalls.\n\n"
            "— Upload your tracks\n"
            "— Listen in the Mini App\n"
            "— Adaptive HLS streaming\n"
            "— Artwork, likes, playlists, search\n"
            "— Lyrics, artist profile, feed"
        ),
    },
    "base.about.tech": {
        "ru": (
            " <b>Технологии</b>\n\n"
            "Backend: Python, FastAPI, PostgreSQL\n"
            "Storage: MinIO (S3)\n"
            "Queues: Taskiq + Redis\n"
            "Bot: aiogram 3\n"
            "Frontend: React, TypeScript, Vite"
        ),
        "en": (
            " <b>Stack</b>\n\n"
            "Backend: Python, FastAPI, PostgreSQL\n"
            "Storage: MinIO (S3)\n"
            "Queues: Taskiq + Redis\n"
            "Bot: aiogram 3\n"
            "Frontend: React, TypeScript, Vite"
        ),
    },
    "base.about.upload": {
        "ru": (
            " <b>Как загрузить музыку</b>\n\n"
            "Через бот: пришли аудиофайл в чат.\n"
            "Через Mini App: плеер → «Загрузить»."
        ),
        "en": (
            " <b>Uploading music</b>\n\n"
            "Via bot: send an audio file here.\n"
            "Via Mini App: player → Upload."
        ),
    },
    "base.about.import": {
        "ru": (
            " <b>Импорт из Telegram</b>\n\n"
            "Плеер → Профиль → Импорт → Telegram. "
            "Треки помечаются как TG."
        ),
        "en": (
            " <b>Import from Telegram</b>\n\n"
            "Player → Profile → Import → Telegram. "
            "Tracks are tagged as TG."
        ),
    },
    "base.about.opensource": {
        "ru": (
            " <b>Открытый код</b>\n\n"
            "Репозитории: DotSoundBackend, DotSoundBot. "
            "PR приветствуются."
        ),
        "en": (
            " <b>Open source</b>\n\n"
            "Repositories: DotSoundBackend, DotSoundBot. "
            "Pull requests welcome."
        ),
    },
    "base.about.roadmap": {
        "ru": (
            " <b>Планы</b>\n\n"
            "— Импорт с внешних сервисов\n"
            "— Рекомендации, совместные плейлисты\n"
            "— Оффлайн и другое"
        ),
        "en": (
            " <b>Roadmap</b>\n\n"
            "— More import sources\n"
            "— Recommendations, collab playlists\n"
            "— Offline and more"
        ),
    },
    "base.stats.tracks": {
        "ru": "Треков:",
        "en": "Tracks:",
    },
    "base.stats.plays": {
        "ru": "Прослушиваний:",
        "en": "Plays:",
    },
    "base.stats.likes": {
        "ru": "Лайков:",
        "en": "Likes:",
    },
    "base.stats.followers": {
        "ru": "Подписчиков:",
        "en": "Followers:",
    },
    "base.playlists.caption": {
        "ru": "Твои плейлисты ({n}):\n\n{names}",
        "en": "Your playlists ({n}):\n\n{names}",
    },
    "app.fallback_error": {
        "ru": (
            "Что-то пошло не так. "
            "Попробуй ещё раз чуть позже."
        ),
        "en": "Something went wrong. Please try again shortly.",
    },
    "throttle.hint": {
        "ru": "Слишком быстро. Подожди секунду.",
        "en": "Too fast. Wait a second.",
    },
    "player.title_prompt": {
        "ru": (
            " <b>Плеер</b>\n\n"
            "Выбери источник треков:"
        ),
        "en": " <b>Player</b>\n\nChoose a track source:",
    },
    "player.loading": {
        "ru": "Загрузка...",
        "en": "Loading...",
    },
    "player.auth_failed": {
        "ru": (
            "Не удалось авторизоваться. "
            "Попробуй позже."
        ),
        "en": "Could not authorize. Try again later.",
    },
    "player.tracks_error": {
        "ru": (
            "Не удалось загрузить треки. "
            "Попробуй позже."
        ),
        "en": "Could not load tracks. Try again later.",
    },
    "player.no_tracks": {
        "ru": "Треков не найдено.",
        "en": "No tracks found.",
    },
    "player.session_expired": {
        "ru": "Сессия истекла. Открой плеер заново.",
        "en": "Session expired. Open the player again.",
    },
    "player.load_page_error": {
        "ru": "Ошибка загрузки.",
        "en": "Load error.",
    },
    "player.no_more": {
        "ru": "Больше треков нет.",
        "en": "No more tracks.",
    },
    "player.like_on": {
        "ru": "Лайк добавлен",
        "en": "Like added",
    },
    "player.like_off": {
        "ru": "Лайк убран",
        "en": "Like removed",
    },
    "player.like_error": {
        "ru": "Ошибка. Попробуй позже.",
        "en": "Error. Try again later.",
    },
    "player.session_short": {
        "ru": "Сессия истекла.",
        "en": "Session expired.",
    },
    "player.track_missing": {
        "ru": "Трек не найден.",
        "en": "Track not found.",
    },
    "stats.error": {
        "ru": (
            "Не удалось получить статистику. "
            "Попробуй позже."
        ),
        "en": "Could not get stats. Try again later.",
    },
    "stats.opening": {
        "ru": " <b>Твоя статистика, {name}</b>\n",
        "en": " <b>Your stats, {name}</b>\n",
    },
    "stats.tracks_line": {
        "ru": "Загружено треков: <b>{n}</b>",
        "en": "Tracks uploaded: <b>{n}</b>",
    },
    "stats.plays_line": {
        "ru": "Всего прослушиваний: <b>{n}</b>",
        "en": "Total plays: <b>{n}</b>",
    },
    "stats.top_header": {
        "ru": "\n <b>Топ треков:</b>",
        "en": "\n <b>Top tracks:</b>",
    },
    "stats.unknown_artist": {
        "ru": "Неизвестный исполнитель",
        "en": "Unknown artist",
    },
    "stats.plays_suffix": {
        "ru": "прослушиваний",
        "en": "plays",
    },
    "playlists.ask_name": {
        "ru": "Введи название нового плейлиста:",
        "en": "Enter a name for the new playlist:",
    },
    "playlists.name_empty": {
        "ru": (
            "Название не может быть пустым. "
            "Попробуй ещё раз:"
        ),
        "en": "The name cannot be empty. Try again:",
    },
    "playlists.created": {
        "ru": (
            "Плейлист <b>{name}</b> создан!\n\n"
            "Открой плеер, чтобы добавить треки."
        ),
        "en": (
            "Playlist <b>{name}</b> created.\n\n"
            "Open the player to add tracks."
        ),
    },
    "playlists.create_error": {
        "ru": (
            "Не удалось создать плейлист. "
            "Попробуй позже."
        ),
        "en": "Could not create a playlist. Try again later.",
    },
    "playlists.no_tracks": {
        "ru": "Треков пока нет",
        "en": "No tracks yet",
    },
    "playlists.view_error": {
        "ru": "Не удалось загрузить плейлист",
        "en": "Could not load the playlist",
    },
    "audio.download_failed": {
        "ru": "Не удалось скачать файл. Попробуй ещё раз.",
        "en": "Download failed. Try again.",
    },
    "audio.uploaded": {
        "ru": "Трек загружен!\n\n",
        "en": "Track uploaded.\n\n",
    },
    "audio.uploaded_doc": {
        "ru": "Трек загружен!\n <b>",
        "en": "Track uploaded.\n <b>",
    },
    "audio.upload_error": {
        "ru": (
            "Ошибка при загрузке трека. "
            "Поддерживаемые форматы: "
            "MP3, OGG, WAV, FLAC, M4A."
        ),
        "en": (
            "Upload error. "
            "Supported: MP3, OGG, WAV, FLAC, M4A."
        ),
    },
    "audio.reply_download": {
        "ru": "Не удалось скачать файл.",
        "en": "Could not download the file.",
    },
    "audio.format_error": {
        "ru": (
            "Ошибка при загрузке. Убедись, что файл "
            "является аудио в поддерживаемом формате."
        ),
        "en": (
            "Upload error. Make sure the file is audio in "
            "a supported format."
        ),
    },
    "likes.auth_failed": {
        "ru": "Авторизация не удалась.",
        "en": "Authorization failed.",
    },
    "likes.added": {
        "ru": "Добавлено в лайки",
        "en": "Added to likes",
    },
    "likes.removed": {
        "ru": "Убрано из лайков",
        "en": "Removed from likes",
    },
    "likes.error": {
        "ru": "Ошибка. Попробуй ещё раз.",
        "en": "Error. Please try again.",
    },
    "likes.dislike_on": {
        "ru": "Дизлайк поставлен",
        "en": "Dislike set",
    },
    "likes.dislike_off": {
        "ru": "Дизлайк убран",
        "en": "Dislike removed",
    },
    "recs.daily_error": {
        "ru": (
            "Не удалось загрузить плейлист дня. "
            "Попробуй позже."
        ),
        "en": "Could not load the daily mix. Try again later.",
    },
    "recs.weekly_error": {
        "ru": (
            "Не удалось загрузить плейлист недели. "
            "Попробуй позже."
        ),
        "en": "Could not load the weekly mix. Try again later.",
    },
    "recs.daily_header": {
        "ru": " <b>Плейлист дня</b>\n",
        "en": " <b>Daily mix</b>\n",
    },
    "recs.weekly_header": {
        "ru": " <b>Плейлист недели</b>\n",
        "en": " <b>Weekly mix</b>\n",
    },
    "recs.empty": {
        "ru": "<i>Треки ещё не подобраны</i>",
        "en": "<i>Tracks are not ready yet</i>",
    },
    "recs.external": {
        "ru": "\n <b>Открытия</b>",
        "en": "\n <b>Discoveries</b>",
    },
    "recs.top": {
        "ru": "\n <b>Топ платформы</b>",
        "en": "\n <b>Top on the platform</b>",
    },
    "recs.external_week": {
        "ru": "\n <b>Открытия недели</b>",
        "en": "\n <b>Week discoveries</b>",
    },
    "recs.refreshed": {
        "ru": "Плейлист обновлён",
        "en": "Playlist updated",
    },
    "recs.admin_only": {
        "ru": "Только для администраторов",
        "en": "Admins only",
    },
    "recs.refresh_error": {
        "ru": "Ошибка обновления",
        "en": "Update failed",
    },
    "inline_mode.pm_hint": {
        "ru": "Введите название трека или исполнителя",
        "en": "Type a track or artist name",
    },
    "inline_mode.like": {
        "ru": "Лайк",
        "en": "Like",
    },
    "inline_mode.dislike": {
        "ru": "Дизлайк",
        "en": "Dislike",
    },
    "inline_mode.listen": {
        "ru": "Слушать",
        "en": "Listen",
    },
    "inline_mode.plays": {
        "ru": "прослушиваний",
        "en": "plays",
    },
    "webauth.code_error": {
        "ru": (
            "Не удалось сгенерировать код. "
            "Попробуйте позже."
        ),
        "en": "Could not generate a code. Try again later.",
    },
    "webauth.open_site": {
        "ru": "Ввести код на сайте",
        "en": "Enter code on the site",
    },
    "webauth.message": {
        "ru": (
            " <b>Код входа в .sound</b>\n\n"
            "<code>{code}</code>\n\n"
            "Действует <b>5 минут</b>\n\n"
            "<i>Введите этот код на сайте</i>"
        ),
        "en": (
            " <b>.sound sign-in code</b>\n\n"
            "<code>{code}</code>\n\n"
            "Valid for <b>5 minutes</b>\n\n"
            "<i>Enter this code on the site</i>"
        ),
    },
    "recs.daily_back": {
        "ru": "← Меню",
        "en": "← Menu",
    },
    "recs.weekly_back": {
        "ru": "← Меню",
        "en": "← Menu",
    },
    "recs.refresh": {
        "ru": "Обновить",
        "en": "Refresh",
    },
    "internal.code_message": {
        "ru": (
            " <b>Код входа в .sound</b>\n\n"
            "<code>{code}</code>\n\n"
            "Действует 5 минут. "
            "Никому не сообщайте этот код."
        ),
        "en": (
            " <b>.sound sign-in code</b>\n\n"
            "<code>{code}</code>\n\n"
            "Valid for 5 minutes. "
            "Do not share this code."
        ),
    },
    "internal.open_player": {
        "ru": "Плеер",
        "en": "Player",
    },
    "internal.login_notice": {
        "ru": (
            " <b>Выполнен вход в .sound web</b>\n\n"
            "Время: {time}\n"
            "IP: {ip}\n"
            "Устройство: {device}\n\n"
            "<i>Если это были не вы, "
            "немедленно смените пароль "
            "или свяжитесь с поддержкой.</i>"
        ),
        "en": (
            " <b>.sound web sign-in</b>\n\n"
            "Time: {time}\n"
            "IP: {ip}\n"
            "Device: {device}\n\n"
            "<i>If this was not you, change your password "
            "or contact support right away.</i>"
        ),
    },
}
