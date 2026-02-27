from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_keyboard(active: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if active:
        builder.add(InlineKeyboardButton(text="Остановить диалог 🛑", callback_data="dialog:stop"))
    else:
        builder.add(InlineKeyboardButton(text="Отправить 📩", callback_data="dialog:start"))
    return builder.as_markup()


def admin_message_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Ответить 💬", callback_data=f"adm:reply:{user_id}"),
        InlineKeyboardButton(text="Бан 🚫", callback_data=f"adm:ban:{user_id}"),
        InlineKeyboardButton(text="Удалить 🗑️", callback_data=f"adm:del:{user_id}"),
    )
    return builder.as_markup()


def user_reply_keyboard(admin_id: int | None = None) -> InlineKeyboardMarkup:
    suffix = admin_id if admin_id is not None else 0
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Ответить 💬", callback_data=f"usr:reply:{suffix}"))
    return builder.as_markup()


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Бан 🚫", callback_data="panel:ban"),
        InlineKeyboardButton(text="Разбан ✅", callback_data="panel:unban"),
    )
    builder.row(
        InlineKeyboardButton(text="Рассылка 📣", callback_data="panel:broadcast"),
        InlineKeyboardButton(text="Статистика 📊", callback_data="panel:stats"),
    )
    builder.row(InlineKeyboardButton(text="Пользователи 👥", callback_data="panel:users:0"))
    return builder.as_markup()


def users_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.add(InlineKeyboardButton(text="Назад ◀️", callback_data=f"panel:users:{page - 1}"))
    if page < total_pages - 1:
        builder.add(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"panel:users:{page + 1}"))
    if builder.buttons:
        return builder.as_markup()
    return InlineKeyboardMarkup(inline_keyboard=[])


def yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да ✅", callback_data=f"{prefix}:yes"))
    builder.add(InlineKeyboardButton(text="Нет ❌", callback_data=f"{prefix}:no"))
    return builder.as_markup()


def broadcast_button_keyboard(text: str, url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=text, url=url))
    return builder.as_markup()
