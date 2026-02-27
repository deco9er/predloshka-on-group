from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    waiting_reply = State()


class AdminStates(StatesGroup):
    waiting_reply = State()
    waiting_ban_id = State()
    waiting_unban_id = State()
    broadcast_content = State()
    broadcast_wait_choice = State()
    broadcast_button_text = State()
    broadcast_button_url = State()
