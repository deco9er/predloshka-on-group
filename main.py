import asyncio
import html
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ContentType, ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.client.default import DefaultBotProperties

from config import Config, load_config
from db import Database
from keyboards import (
    admin_message_keyboard,
    admin_panel_keyboard,
    broadcast_button_keyboard,
    start_keyboard,
    user_reply_keyboard,
    users_pagination_keyboard,
    yes_no_keyboard,
)
from states import AdminStates, UserStates

START_TEXT = (
    "Привет {name} 👋, этот бот пересылает твои сообщения @deco9er\n"
    "Hello {name} 👋, this bot reply you messages to @deco9er"
)

PAGE_SIZE = 50
CAPTIONABLE_TYPES = {
    ContentType.PHOTO,
    ContentType.VIDEO,
    ContentType.ANIMATION,
    ContentType.DOCUMENT,
    ContentType.AUDIO,
    ContentType.VOICE,
}

router = Router()


def is_admin(user_id: int, config: Config) -> bool:
    return user_id in config.admin_ids


def safe_user_link(user_id: int, full_name: str, username: Optional[str]) -> str:
    name = html.escape(full_name or "Пользователь")
    link = f"<a href=\"tg://user?id={user_id}\">{name}</a>"
    if username:
        uname = html.escape(username)
        return f"{link} (@{uname})"
    return link


def user_info_line(user) -> str:
    full_name = user.full_name if user else "Пользователь"
    username = user.username if user else None
    return safe_user_link(user.id, full_name, username)


def is_cancel_message(message: Message) -> bool:
    text = (message.text or "").strip().lower()
    return text == "/cancel"


async def cancel_flow(message: Message, state: FSMContext) -> bool:
    if await state.get_state() is None:
        return False
    await clear_state_keep_dialog(state)
    await message.answer("Отменено ✅")
    return True


async def get_dialog_active(state: FSMContext) -> bool:
    data = await state.get_data()
    return bool(data.get("dialog_active"))


async def set_dialog_active(state: FSMContext, active: bool) -> None:
    await state.update_data(dialog_active=active)


async def clear_state_keep_dialog(state: FSMContext) -> None:
    data = await state.get_data()
    dialog_active = bool(data.get("dialog_active"))
    await state.clear()
    if dialog_active:
        await state.update_data(dialog_active=True)


async def send_to_admin_group(
    message: Message,
    config: Config,
    db: Database,
    note: Optional[str] = None,
) -> None:
    user = message.from_user
    if not user:
        return

    db.add_or_update_user(user.id, user.username, user.full_name)
    if db.is_banned(user.id):
        await message.answer("⛔ Вы заблокированы.")
        return

    header = f"📨 Сообщение от {user_info_line(user)} (ID: {user.id})"
    if note:
        header = f"{header}\n{note}"

    if message.content_type == ContentType.TEXT:
        body = html.escape(message.text or "")
        text = f"{header}\n\n{body}"
        sent = await message.bot.send_message(
            config.admin_group_id,
            text,
            reply_markup=admin_message_keyboard(user.id),
        )
        db.add_link(sent.message_id, user.id)
        return

    caption_text = None
    if message.content_type in CAPTIONABLE_TYPES:
        caption_text = header
        if message.caption:
            caption_text = f"{caption_text}\n\n{html.escape(message.caption)}"

    if caption_text is not None:
        sent = await message.bot.copy_message(
            config.admin_group_id,
            message.chat.id,
            message.message_id,
            caption=caption_text,
            parse_mode=ParseMode.HTML,
            reply_markup=admin_message_keyboard(user.id),
        )
        db.add_link(sent.message_id, user.id)
        return

    info_text = header
    info_message = await message.bot.send_message(
        config.admin_group_id,
        info_text,
    )
    try:
        sent = await message.bot.copy_message(
            config.admin_group_id,
            message.chat.id,
            message.message_id,
            reply_to_message_id=info_message.message_id,
            reply_markup=admin_message_keyboard(user.id),
        )
        db.add_link(sent.message_id, user.id)
    except TelegramBadRequest:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=config.admin_group_id,
                message_id=info_message.message_id,
                reply_markup=admin_message_keyboard(user.id),
            )
        except TelegramBadRequest:
            pass
        db.add_link(info_message.message_id, user.id)


async def send_admin_reply_to_user(
    message: Message,
    target_user_id: int,
    admin_id: int,
) -> None:
    if message.content_type == ContentType.TEXT:
        text = html.escape(message.text or "")
        await message.bot.send_message(
            target_user_id,
            text,
            reply_markup=user_reply_keyboard(admin_id),
        )
    else:
        caption = html.escape(message.caption) if message.caption else None
        await message.bot.copy_message(
            target_user_id,
            message.chat.id,
            message.message_id,
            caption=caption,
            reply_markup=user_reply_keyboard(admin_id),
        )


@router.message(CommandStart(), F.chat.type == "private")
async def handle_start(message: Message, db: Database, state: FSMContext) -> None:
    user = message.from_user
    if user:
        db.add_or_update_user(user.id, user.username, user.full_name)
    name = html.escape(user.first_name) if user else "друг"
    dialog_active = await get_dialog_active(state)
    await message.answer(
        START_TEXT.format(name=name),
        reply_markup=start_keyboard(active=dialog_active),
    )


@router.callback_query(F.data == "dialog:start")
async def handle_dialog_start(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    user = callback.from_user
    if user and db.is_banned(user.id):
        await callback.answer("⛔ Вы заблокированы.", show_alert=True)
        return
    await set_dialog_active(state, True)
    await callback.answer("Диалог начат ✅")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=start_keyboard(active=True))
    await callback.message.answer("Диалог начат ✅ Пишите сообщение, я всё перешлю 📩")


@router.callback_query(F.data == "dialog:stop")
async def handle_dialog_stop(callback: CallbackQuery, state: FSMContext) -> None:
    await set_dialog_active(state, False)
    await callback.answer("Диалог остановлен 🛑")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=start_keyboard(active=False))
    await callback.message.answer("Диалог остановлен 🛑")


@router.callback_query(F.data.startswith("usr:reply:"))
async def handle_user_reply_callback(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database,
) -> None:
    user = callback.from_user
    if user and db.is_banned(user.id):
        await callback.answer("⛔ Вы заблокированы.", show_alert=True)
        return

    parts = callback.data.split(":")
    admin_id = int(parts[2]) if len(parts) > 2 else 0
    await state.set_state(UserStates.waiting_reply)
    await state.update_data(reply_admin_id=admin_id)
    await callback.answer()
    await callback.message.answer("Напишите ваш ответ администратору 💬")


@router.message(UserStates.waiting_reply, F.chat.type == "private")
async def handle_user_reply_message(
    message: Message,
    state: FSMContext,
    config: Config,
    db: Database,
) -> None:
    if is_cancel_message(message):
        await cancel_flow(message, state)
        return
    data = await state.get_data()
    admin_id = data.get("reply_admin_id")
    admin_note = None
    if admin_id:
        admin_note = f"↩️ Ответ на сообщение администратора {safe_user_link(admin_id, 'Администратор', None)}"

    try:
        await send_to_admin_group(message, config, db, note=admin_note)
        await message.answer("Ответ отправлен ✅")
    except (TelegramForbiddenError, TelegramBadRequest):
        await message.answer(
            "Не могу отправить сообщение в админ‑группу ❌ "
            "Проверьте, что бот добавлен в группу и ID группы верный."
        )
    finally:
        await clear_state_keep_dialog(state)


@router.message(Command("admin"), F.chat.type == "private")
async def handle_admin_panel(message: Message, config: Config) -> None:
    if not message.from_user or not is_admin(message.from_user.id, config):
        return
    await message.answer("Админ‑панель ⚙️:", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data.startswith("adm:"))
async def handle_admin_actions(
    callback: CallbackQuery,
    state: FSMContext,
    config: Config,
    db: Database,
) -> None:
    if not callback.from_user or not is_admin(callback.from_user.id, config):
        await callback.answer("Недостаточно прав ❌", show_alert=True)
        return
    if callback.message and callback.message.chat.id != config.admin_group_id:
        await callback.answer("Команда доступна только в админ‑группе 👮", show_alert=True)
        return

    parts = callback.data.split(":")
    action = parts[1]
    target_user_id = int(parts[2])

    if action == "reply":
        await state.set_state(AdminStates.waiting_reply)
        await state.update_data(target_user_id=target_user_id, admin_id=callback.from_user.id)
        await callback.answer("Отправьте ответ пользователю 💬", show_alert=False)
    elif action == "ban":
        db.set_ban(target_user_id, True)
        await callback.answer("Пользователь забанен 🚫", show_alert=True)
        try:
            await callback.bot.send_message(target_user_id, "⛔ Вы заблокированы администратором.")
        except TelegramForbiddenError:
            pass
    elif action == "del":
        await callback.answer("Сообщение удалено 🗑️", show_alert=False)
        if callback.message:
            try:
                await callback.message.delete()
            except TelegramBadRequest:
                pass


@router.message(AdminStates.waiting_reply)
async def handle_admin_reply_message(
    message: Message,
    state: FSMContext,
    config: Config,
) -> None:
    if not message.from_user or not is_admin(message.from_user.id, config):
        return
    if is_cancel_message(message):
        await cancel_flow(message, state)
        return

    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    admin_id = data.get("admin_id", message.from_user.id)
    if not target_user_id:
        await clear_state_keep_dialog(state)
        await message.answer("Цель ответа не найдена ❌")
        return

    try:
        await send_admin_reply_to_user(message, target_user_id, admin_id)
        await message.answer("Ответ отправлен пользователю ✅")
    except TelegramForbiddenError:
        await message.answer("Не удалось отправить ответ ❌ Пользователь запретил сообщения.")
    finally:
        await clear_state_keep_dialog(state)


@router.callback_query(F.data.startswith("panel:"))
async def handle_admin_panel_actions(
    callback: CallbackQuery,
    state: FSMContext,
    config: Config,
    db: Database,
) -> None:
    if not callback.from_user or not is_admin(callback.from_user.id, config):
        await callback.answer("Недостаточно прав ❌", show_alert=True)
        return

    parts = callback.data.split(":")
    action = parts[1]

    if action == "ban":
        await state.set_state(AdminStates.waiting_ban_id)
        await callback.message.answer("Введите ID пользователя для бана 🚫")
        await callback.answer()
    elif action == "unban":
        await state.set_state(AdminStates.waiting_unban_id)
        await callback.message.answer("Введите ID пользователя для разбана ✅")
        await callback.answer()
    elif action == "stats":
        total = db.count_users()
        banned = db.count_banned()
        messages = db.count_messages()
        text = (
            f"📊 Статистика:\n"
            f"👥 Всего пользователей: {total}\n"
            f"🚫 Забанено: {banned}\n"
            f"✉️ Сообщений получено: {messages}"
        )
        await callback.message.answer(text)
        await callback.answer()
    elif action == "users":
        page = int(parts[2]) if len(parts) > 2 else 0
        await send_users_page(callback, db, page)
    elif action == "broadcast":
        await state.set_state(AdminStates.broadcast_content)
        await callback.message.answer("Отправьте сообщение для рассылки 📣 (любой тип файла).")
        await callback.answer()


async def send_users_page(callback: CallbackQuery, db: Database, page: int) -> None:
    total = db.count_users()
    if total == 0:
        await callback.message.answer("Пользователей пока нет 👥")
        await callback.answer()
        return

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))

    rows = db.get_users_page(page * PAGE_SIZE, PAGE_SIZE)
    lines = [
        f"{safe_user_link(row['id'], row['full_name'], row['username'])}"
        + (" (бан)" if row["is_banned"] else "")
        for row in rows
    ]

    text = f"👥 Пользователи {page + 1}/{total_pages} (всего {total}):\n" + "\n".join(lines)
    await callback.message.edit_text(
        text,
        reply_markup=users_pagination_keyboard(page, total_pages),
    )
    await callback.answer()


@router.message(AdminStates.waiting_ban_id)
async def handle_ban_id(message: Message, state: FSMContext, config: Config, db: Database) -> None:
    if not message.from_user or not is_admin(message.from_user.id, config):
        return
    if is_cancel_message(message):
        await cancel_flow(message, state)
        return
    try:
        user_id = int(message.text.strip())
    except (AttributeError, ValueError):
        await message.answer("Нужен числовой ID пользователя 🔢")
        return
    db.set_ban(user_id, True)
    await clear_state_keep_dialog(state)
    await message.answer(f"Пользователь {user_id} забанен 🚫")


@router.message(AdminStates.waiting_unban_id)
async def handle_unban_id(message: Message, state: FSMContext, config: Config, db: Database) -> None:
    if not message.from_user or not is_admin(message.from_user.id, config):
        return
    if is_cancel_message(message):
        await cancel_flow(message, state)
        return
    try:
        user_id = int(message.text.strip())
    except (AttributeError, ValueError):
        await message.answer("Нужен числовой ID пользователя 🔢")
        return
    db.set_ban(user_id, False)
    await clear_state_keep_dialog(state)
    await message.answer(f"Пользователь {user_id} разбанен ✅")


@router.message(AdminStates.broadcast_content)
async def handle_broadcast_content(message: Message, state: FSMContext, config: Config) -> None:
    if not message.from_user or not is_admin(message.from_user.id, config):
        return
    if is_cancel_message(message):
        await cancel_flow(message, state)
        return
    await state.update_data(broadcast_chat_id=message.chat.id, broadcast_message_id=message.message_id)
    await state.set_state(AdminStates.broadcast_wait_choice)
    await message.answer(
        "Добавить кнопку под сообщением рассылки? 🔘",
        reply_markup=yes_no_keyboard("broadcast"),
    )


@router.callback_query(F.data.startswith("broadcast:"))
async def handle_broadcast_button_choice(callback: CallbackQuery, state: FSMContext, config: Config, db: Database) -> None:
    if not callback.from_user or not is_admin(callback.from_user.id, config):
        await callback.answer("Недостаточно прав ❌", show_alert=True)
        return

    choice = callback.data.split(":")[1]
    if choice == "yes":
        await state.set_state(AdminStates.broadcast_button_text)
        await callback.message.answer("Введите текст кнопки 🔘")
        await callback.answer()
    else:
        await callback.answer()
        await run_broadcast(callback.message, state, config, db, reply_markup=None)


@router.message(AdminStates.broadcast_button_text)
async def handle_broadcast_button_text(message: Message, state: FSMContext, config: Config) -> None:
    if not message.from_user or not is_admin(message.from_user.id, config):
        return
    if is_cancel_message(message):
        await cancel_flow(message, state)
        return
    text = (message.text or "").strip()
    if not text:
        await message.answer("Текст кнопки не может быть пустым ❌")
        return
    await state.update_data(button_text=text)
    await state.set_state(AdminStates.broadcast_button_url)
    await message.answer("Введите URL для кнопки 🔗")


@router.message(AdminStates.broadcast_button_url)
async def handle_broadcast_button_url(message: Message, state: FSMContext, config: Config, db: Database) -> None:
    if not message.from_user or not is_admin(message.from_user.id, config):
        return
    if is_cancel_message(message):
        await cancel_flow(message, state)
        return
    url = (message.text or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer("URL должен начинаться с http:// или https:// 🔗")
        return
    data = await state.get_data()
    text = data.get("button_text", "Перейти")
    markup = broadcast_button_keyboard(text, url)
    await run_broadcast(message, state, config, db, reply_markup=markup)


async def run_broadcast(
    message: Message,
    state: FSMContext,
    config: Config,
    db: Database,
    reply_markup,
) -> None:
    data = await state.get_data()
    source_chat_id = data.get("broadcast_chat_id")
    source_message_id = data.get("broadcast_message_id")
    if not source_chat_id or not source_message_id:
        await message.answer("Не удалось найти сообщение для рассылки ❌")
        await clear_state_keep_dialog(state)
        return

    total = 0
    success = 0
    failed = 0

    async def try_copy(user_id: int) -> bool:
        try:
            await message.bot.copy_message(
                user_id,
                source_chat_id,
                source_message_id,
                reply_markup=reply_markup,
            )
            return True
        except TelegramBadRequest:
            if reply_markup is not None:
                try:
                    await message.bot.copy_message(
                        user_id,
                        source_chat_id,
                        source_message_id,
                    )
                    return True
                except (TelegramForbiddenError, TelegramBadRequest):
                    return False
            return False
        except TelegramForbiddenError:
            return False

    for user_id in db.iter_user_ids(only_active=True):
        total += 1
        try:
            if await try_copy(user_id):
                success += 1
            else:
                failed += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                if await try_copy(user_id):
                    success += 1
                else:
                    failed += 1
            except (TelegramForbiddenError, TelegramBadRequest):
                failed += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        await asyncio.sleep(0.05)

    await clear_state_keep_dialog(state)
    await message.answer(
        f"📣 Рассылка завершена. Отправлено: {success}. Ошибки: {failed}. Всего: {total}."
    )


@router.message(Command("cancel"))
async def handle_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        await message.answer("Нечего отменять 🤷")
        return
    await clear_state_keep_dialog(state)
    await message.answer("Отменено ✅")


@router.message(F.chat.type == "private")
async def handle_user_message(message: Message, config: Config, db: Database, state: FSMContext) -> None:
    if not message.from_user:
        return
    if await state.get_state() is not None:
        return
    text = (message.text or "").strip()
    if text.startswith("/"):
        command = text.split()[0].lower()
        if command in {"/start", "/admin", "/cancel"}:
            return
    dialog_active = await get_dialog_active(state)
    if not dialog_active:
        await message.answer(
            "Нажмите «Отправить 📩» чтобы начать диалог.",
            reply_markup=start_keyboard(active=False),
        )
        return
    try:
        await send_to_admin_group(message, config, db)
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        await message.answer(
            "Не могу отправить сообщение в админ‑группу ❌ "
            "Проверьте, что бот добавлен в группу и ID группы верный."
        )
        logging.exception("Failed to send to admin group: %s", exc)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    db = Database(config.db_path)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot, config=config, db=db)


if __name__ == "__main__":
    asyncio.run(main())
