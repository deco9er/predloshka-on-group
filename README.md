# Telegram Bot для обратной связи и поддержки

Этот проект представляет собой Telegram-бота для организации технической поддержки или обратной связи между пользователями и администрацией. Бот пересылает сообщения от пользователей в специальную админ-группу, где модераторы могут отвечать, банить пользователей или осуществлять рассылку.

## 🚀 Возможности

### Для пользователей
- **Анонимная связь**: Сообщения пересылаются в админ-группу без раскрытия лишней информации.
- **Управление диалогом**: Возможность начать или остановить диалог с поддержкой через кнопки.
- **Ответы**: Получение ответов от администрации с кнопкой для быстрого ответа.

### Для администрации
- **Админ-панель**: Доступ к управлению через команду `/admin` (только для указанных ID).
- **Обработка сообщений**: Сообщения пользователей поступают в назначенную группу с кнопками действий:
  - 💬 **Ответить**: Переход в режим ответа конкретному пользователю.
  - 🚫 **Бан**: Блокировка пользователя (сообщения перестают поступать).
  - 🗑️ **Удалить**: Удаление сообщения из админ-группы.
- **Рассылка**: Массовая рассылка сообщений всем активным пользователям (поддержка текста, медиа и кнопок с URL).
- **Статистика**: Просчет количества пользователей, забаненных аккаунтов и обработанных сообщений.
- **Список пользователей**: Пагинированный список всех пользователей с возможностью бана/разбана по ID.

## 🛠 Технологический стек

- **Язык**: Python 3.10+
- **Фреймворк**: [aiogram 3.x](https://docs.aiogram.dev/) (асинхронный)
- **База данных**: SQLite (локальный файл `bot.db`)
- **Конфигурация**: Переменные окружения (`.env`)

## 📦 Установка

1. **Клонируйте репозиторий**:
   ```bash
   git clone <ссылка_на_репозиторий>
   cd <имя_папки>
   ```

2. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Примечание: создайте файл requirements.txt с содержимым `aiogram`, `python-dotenv`)*

3. **Настройте окружение**:
   Создайте файл `.env` в корне проекта на основе `.env.example` (или просто `.env`):
   ```env
   BOT_TOKEN=ваш_токен_бота
   ADMIN_GROUP_ID=id_админ_группы
   ADMIN_IDS=12345678,87654321
   DB_PATH=bot.db
   ```

4. **Запустите бота**:
   ```bash
   python main.py
   ```

## ⚙️ Конфигурация

| Переменная | Описание | Обязательно |
| :--- | :--- | :--- |
| `BOT_TOKEN` | Токен бота, полученный от @BotFather | ✅ |
| `ADMIN_GROUP_ID` | ID группы, куда будут приходить сообщения (бот должен быть админом в группе) | ✅ |
| `ADMIN_IDS` | Список ID администраторов через запятую (доступ к панели и рассылке) | ✅ |
| `DB_PATH` | Путь к файлу базы данных SQLite | ❌ (по умолчанию `bot.db`) |

## 📖 Использование

### Настройка администратора
1. Создайте группу в Telegram и добавьте туда бота.
2. Назначьте бота администратором группы (для возможности отправки сообщений).
3. Узнайте ID группы (можно через бота @userinfobot или переслав сообщение из группы) и укажите в `ADMIN_GROUP_ID`.
4. Узнайте свой пользовательский ID и добавьте в `ADMIN_IDS`.
5. Запустите бота и напишите `/admin` в личные сообщения для проверки доступа.

### Работа с пользователями
1. Пользователь нажимает `/start`.
2. Для отправки сообщения необходимо нажать кнопку **"Отправить 📩"**.
3. Сообщения поступают в админ-группу.
4. Администратор нажимает **"Ответить 💬"** под сообщением и отправляет текст.
5. Пользователь получает ответ и может ответить обратно через кнопку.

## 📂 Структура проекта

```text
.
├── .env                # Файл конфигурации (токены, ID)
├── config.py           # Модуль загрузки и валидации конфигурации
├── db.py               # Работа с SQLite (пользователи, баны, ссылки на сообщения)
├── main.py             # Основная логика бота, хендлеры и FSM
├── keyboards.py        # Генерация инлайн-клавиатур
└── requirements.txt    # Зависимости Python
```

## ⚠️ Важные замечания

- **Приватность**: Бот хранит ID пользователей и имена в локальной базе данных.
- **Лимиты**: При массовой рассылке реализована задержка между сообщениями для избежания лимитов Telegram API.
- **Безопасность**: Доступ к админ-функциям строго ограничен списком `ADMIN_IDS`.

# Telegram Feedback and Support Bot

This project is a Telegram bot designed to organize technical support or feedback channels between users and administration. The bot forwards messages from users to a dedicated admin group, where moderators can reply, ban users, or perform broadcasts.

## 🚀 Features

### For Users
- **Anonymous Communication**: Messages are forwarded to the admin group without revealing unnecessary personal information.
- **Dialog Management**: Ability to start or stop a conversation with support via buttons.
- **Replies**: Receive responses from administration with a button for quick replies.

### For Administration
- **Admin Panel**: Access management via the `/admin` command (restricted to specific IDs).
- **Message Handling**: User messages arrive in the designated group with action buttons:
  - 💬 **Reply**: Enter reply mode for a specific user.
  - 🚫 **Ban**: Block the user (messages will stop arriving).
  - 🗑️ **Delete**: Remove the message from the admin group.
- **Broadcasting**: Mass messaging to all active users (supports text, media, and URL buttons).
- **Statistics**: Calculate the number of users, banned accounts, and processed messages.
- **User List**: Paginated list of all users with the ability to ban/unban by ID.

## 🛠 Tech Stack

- **Language**: Python 3.10+
- **Framework**: [aiogram 3.x](https://docs.aiogram.dev/) (asynchronous)
- **Database**: SQLite (local file `bot.db`)
- **Configuration**: Environment variables (`.env`)

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd <folder_name>
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Create a `requirements.txt` file containing `aiogram` and `python-dotenv`)*

3. **Configure the environment**:
   Create a `.env` file in the project root based on `.env.example` (or create a new `.env`):
   ```env
   BOT_TOKEN=your_bot_token
   ADMIN_GROUP_ID=your_admin_group_id
   ADMIN_IDS=12345678,87654321
   DB_PATH=bot.db
   ```

4. **Run the bot**:
   ```bash
   python main.py
   ```

## ⚙️ Configuration

| Variable | Description | Required |
| :--- | :--- | :--- |
| `BOT_TOKEN` | Bot token obtained from @BotFather | ✅ |
| `ADMIN_GROUP_ID` | ID of the group where messages will be sent (bot must be an admin in this group) | ✅ |
| `ADMIN_IDS` | Comma-separated list of administrator IDs (access to panel and broadcasting) | ✅ |
| `DB_PATH` | Path to the SQLite database file | ❌ (default: `bot.db`) |

## 📖 Usage

### Admin Setup
1. Create a group in Telegram and add the bot to it.
2. Promote the bot to an administrator in the group (to enable message sending capabilities).
3. Obtain the Group ID (using a bot like @userinfobot or by forwarding a message from the group) and set it in `ADMIN_GROUP_ID`.
4. Obtain your User ID and add it to `ADMIN_IDS`.
5. Start the bot and send `/admin` in a private chat to verify access.

### Working with Users
1. The user presses `/start`.
2. To send a message, they must press the **"Send 📩"** button.
3. Messages are forwarded to the admin group.
4. The administrator presses **"Reply 💬"** under the message and sends the text.
5. The user receives the response and can reply back via the button.

## 📂 Project Structure

```text
.
├── .env                # Configuration file (tokens, IDs)
├── config.py           # Module for loading and validating configuration
├── db.py               # SQLite operations (users, bans, message links)
├── main.py             # Main bot logic, handlers, and FSM
├── keyboards.py        # Inline keyboard generation
└── requirements.txt    # Python dependencies
```

## ⚠️ Important Notes

- **Privacy**: The bot stores user IDs and names in a local database.
- **Limits**: A delay is implemented between messages during mass broadcasting to avoid hitting Telegram API limits.
- **Security**: Access to admin functions is strictly restricted to the list of `ADMIN_IDS`.
