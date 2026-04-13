import io
from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch,
)

import pytest

from bot.api.client import BackendError

pytestmark = pytest.mark.anyio


def _make_message(
    audio=None,
    document=None,
    user_id: int = 1,
) -> MagicMock:
    msg = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.audio = audio
    msg.document = document
    msg.reply = AsyncMock()
    return msg


def _make_audio() -> MagicMock:
    audio = MagicMock()
    audio.file_id = "fid"
    audio.file_name = "track.mp3"
    audio.mime_type = "audio/mpeg"
    audio.title = "Test Song"
    audio.performer = "Test Artist"
    audio.duration = 180
    return audio


def _make_document() -> MagicMock:
    doc = MagicMock()
    doc.file_id = "dfid"
    doc.file_name = "doc.mp3"
    doc.mime_type = "audio/mpeg"
    return doc


# ------------------------------------------------------------------
# handle_audio
# ------------------------------------------------------------------


@patch("bot.handlers.audio.BackendClient")
@patch("bot.handlers.audio.settings")
async def test_handle_audio_success(
    mock_settings: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.audio import handle_audio

    mock_settings.backend_base_url = "http://test"
    client = AsyncMock()
    client.upload_audio = AsyncMock(
        return_value={"id": 1, "title": "Song"}
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    bot = AsyncMock()
    file_info = MagicMock()
    file_info.file_path = "music/track.mp3"
    bot.get_file = AsyncMock(return_value=file_info)
    bot.download_file = AsyncMock(
        return_value=io.BytesIO(b"audio-data")
    )

    audio = _make_audio()
    msg = _make_message(audio=audio)

    await handle_audio(msg, bot)

    client.upload_audio.assert_awaited_once()
    msg.reply.assert_awaited_once()
    call_text = msg.reply.call_args[0][0]
    assert "загружен" in call_text


@patch("bot.handlers.audio.BackendClient")
@patch("bot.handlers.audio.settings")
async def test_handle_audio_without_artist(
    mock_settings: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.audio import handle_audio

    mock_settings.backend_base_url = "http://test"
    client = AsyncMock()
    client.upload_audio = AsyncMock(
        return_value={"id": 2, "title": "Song"}
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    bot = AsyncMock()
    file_info = MagicMock()
    file_info.file_path = "music/track.mp3"
    bot.get_file = AsyncMock(return_value=file_info)
    bot.download_file = AsyncMock(
        return_value=io.BytesIO(b"data")
    )

    audio = _make_audio()
    audio.performer = None
    msg = _make_message(audio=audio)

    await handle_audio(msg, bot)

    text = msg.reply.call_args[0][0]
    assert "загружен" in text
    assert "👤" not in text


@patch("bot.handlers.audio.BackendClient")
@patch("bot.handlers.audio.settings")
async def test_handle_audio_upload_error(
    mock_settings: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.audio import handle_audio

    mock_settings.backend_base_url = "http://test"
    client = AsyncMock()
    client.upload_audio = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    bot = AsyncMock()
    file_info = MagicMock()
    file_info.file_path = "music/track.mp3"
    bot.get_file = AsyncMock(return_value=file_info)
    bot.download_file = AsyncMock(
        return_value=io.BytesIO(b"data")
    )

    audio = _make_audio()
    msg = _make_message(audio=audio)

    await handle_audio(msg, bot)

    text = msg.reply.call_args[0][0]
    assert "Ошибка" in text


async def test_handle_audio_download_failure(
) -> None:
    from bot.handlers.audio import handle_audio

    bot = AsyncMock()
    file_info = MagicMock()
    file_info.file_path = "music/track.mp3"
    bot.get_file = AsyncMock(return_value=file_info)
    bot.download_file = AsyncMock(return_value=None)

    audio = _make_audio()
    msg = _make_message(audio=audio)

    await handle_audio(msg, bot)

    msg.reply.assert_awaited_once()
    call_text = msg.reply.call_args[0][0]
    assert "скачать" in call_text


async def test_handle_audio_no_user() -> None:
    from bot.handlers.audio import handle_audio

    bot = AsyncMock()
    msg = AsyncMock()
    msg.from_user = None
    msg.audio = _make_audio()

    await handle_audio(msg, bot)

    msg.reply.assert_not_awaited()


async def test_handle_audio_no_audio() -> None:
    from bot.handlers.audio import handle_audio

    bot = AsyncMock()
    msg = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 1
    msg.audio = None
    msg.reply = AsyncMock()

    await handle_audio(msg, bot)

    msg.reply.assert_not_awaited()


@patch("bot.handlers.audio.BackendClient")
@patch("bot.handlers.audio.settings")
async def test_handle_audio_no_title_fallback(
    mock_settings: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.audio import handle_audio

    mock_settings.backend_base_url = "http://test"
    client = AsyncMock()
    client.upload_audio = AsyncMock(
        return_value={"id": 3, "title": "Unknown"}
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    bot = AsyncMock()
    file_info = MagicMock()
    file_info.file_path = "music/track.mp3"
    bot.get_file = AsyncMock(return_value=file_info)
    bot.download_file = AsyncMock(
        return_value=io.BytesIO(b"data")
    )

    audio = _make_audio()
    audio.title = None
    audio.file_name = None
    msg = _make_message(audio=audio)

    await handle_audio(msg, bot)

    call_kwargs = (
        client.upload_audio.call_args
    )
    assert call_kwargs[1]["title"] == "Unknown Track"


# ------------------------------------------------------------------
# handle_audio_document
# ------------------------------------------------------------------


@patch("bot.handlers.audio.BackendClient")
@patch("bot.handlers.audio.settings")
async def test_handle_audio_document_success(
    mock_settings: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.audio import (
        handle_audio_document,
    )

    mock_settings.backend_base_url = "http://test"
    client = AsyncMock()
    client.upload_audio = AsyncMock(
        return_value={"id": 5, "title": "DocSong"}
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    bot = AsyncMock()
    file_info = MagicMock()
    file_info.file_path = "music/doc.mp3"
    bot.get_file = AsyncMock(return_value=file_info)
    bot.download_file = AsyncMock(
        return_value=io.BytesIO(b"data")
    )

    doc = _make_document()
    msg = _make_message(document=doc)

    await handle_audio_document(msg, bot)

    client.upload_audio.assert_awaited_once()
    text = msg.reply.call_args[0][0]
    assert "загружен" in text


@patch("bot.handlers.audio.BackendClient")
@patch("bot.handlers.audio.settings")
async def test_handle_audio_document_upload_error(
    mock_settings: MagicMock,
    mock_client_cls: MagicMock,
) -> None:
    from bot.handlers.audio import (
        handle_audio_document,
    )

    mock_settings.backend_base_url = "http://test"
    client = AsyncMock()
    client.upload_audio = AsyncMock(
        side_effect=BackendError(500, "fail")
    )
    mock_client_cls.return_value.__aenter__ = (
        AsyncMock(return_value=client)
    )
    mock_client_cls.return_value.__aexit__ = (
        AsyncMock(return_value=False)
    )

    bot = AsyncMock()
    file_info = MagicMock()
    file_info.file_path = "music/doc.mp3"
    bot.get_file = AsyncMock(return_value=file_info)
    bot.download_file = AsyncMock(
        return_value=io.BytesIO(b"data")
    )

    doc = _make_document()
    msg = _make_message(document=doc)

    await handle_audio_document(msg, bot)

    msg.reply.assert_awaited_once()
    call_text = msg.reply.call_args[0][0]
    assert "Ошибка" in call_text


async def test_handle_audio_document_download_fail(
) -> None:
    from bot.handlers.audio import (
        handle_audio_document,
    )

    bot = AsyncMock()
    file_info = MagicMock()
    file_info.file_path = "music/doc.mp3"
    bot.get_file = AsyncMock(return_value=file_info)
    bot.download_file = AsyncMock(return_value=None)

    doc = _make_document()
    msg = _make_message(document=doc)

    await handle_audio_document(msg, bot)

    msg.reply.assert_awaited_once()
    text = msg.reply.call_args[0][0]
    assert "скачать" in text.lower()


async def test_handle_audio_document_no_user(
) -> None:
    from bot.handlers.audio import (
        handle_audio_document,
    )

    bot = AsyncMock()
    msg = AsyncMock()
    msg.from_user = None
    msg.document = _make_document()
    msg.reply = AsyncMock()

    await handle_audio_document(msg, bot)

    msg.reply.assert_not_awaited()


async def test_handle_audio_document_no_doc(
) -> None:
    from bot.handlers.audio import (
        handle_audio_document,
    )

    bot = AsyncMock()
    msg = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 1
    msg.document = None
    msg.reply = AsyncMock()

    await handle_audio_document(msg, bot)

    msg.reply.assert_not_awaited()


# ------------------------------------------------------------------
# _is_audio_document
# ------------------------------------------------------------------


def test_is_audio_document_valid() -> None:
    from bot.handlers.audio import (
        _is_audio_document,
    )

    doc = MagicMock()
    doc.mime_type = "audio/mpeg"

    assert _is_audio_document(doc) is True


def test_is_audio_document_non_audio() -> None:
    from bot.handlers.audio import (
        _is_audio_document,
    )

    doc = MagicMock()
    doc.mime_type = "image/png"

    assert _is_audio_document(doc) is False


def test_is_audio_document_none() -> None:
    from bot.handlers.audio import (
        _is_audio_document,
    )

    assert _is_audio_document(None) is False


def test_is_audio_document_no_mime() -> None:
    from bot.handlers.audio import (
        _is_audio_document,
    )

    doc = MagicMock()
    doc.mime_type = None

    assert _is_audio_document(doc) is False
