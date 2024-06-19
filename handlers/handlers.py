import logging

from aiogram import Router
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command

from sqlalchemy.ext.asyncio import AsyncSession

from client import YaDiskClient
from config import TOKEN_URL
from db import async_session_maker, User
from db.models import YandexDiskFolder
from .callbacks import callback_start
from .keyboards import keyboard_register
from sqlalchemy import select


async def help_command(message: types.Message):
    help_str = """Вас приветствует бот <b><i>RANEPA BOT</i></b>
    💬 Регистрация пользователя <b>/start</b>
    💬 Информацию о пользователе можно вывести с помощью команды <b>/status</b>"""

    logging.info(f"user {message.from_user.id} asked for help")
    await message.reply(text=help_str, parse_mode="HTML")


async def status_command(message: types.Message):
    """Информация о пользователе"""

    async with async_session_maker() as session:
        session: AsyncSession

        user = await session.get(User, message.from_user.id)

        if user is None:
            logging.info(f"user {message.from_user.id} requested status but is not registered")
            await message.reply(text="Создайте аккаунт с помощью /start")
            return

        text = f"<b>Ваше имя</b>: <i>{user.tg_username}</i>\n"

        if user.teacher_id is None:
            text += f"<b>ID приглашение для слушателей</b>: <i>{user.id}</i>\n"
        else:
            text += f"<b>Ваш ID</b>: <i>{user.id}</i>\n"

        if user.yadisk_token:
            text += f"<b>Ваш TOKEN Яндекс Диска</b>: <i>{user.yadisk_token}</i>\n"

        if user.teacher_id:
            text += f"<b>Вы закреплены за </b>: <i>@{user.teacher_id}</i>\n"

        logging.info(f"user {message.from_user.id} requested status")
        await message.reply(text=text, parse_mode="HTML")

        await session.close()


async def start_command(message: types.Message):
    async with async_session_maker() as session:
        session: AsyncSession

        user = await session.get(User, message.from_user.id)

        if user is None:
            logging.info(f"user {message.from_user.id} started the bot and is not registered")
            await message.reply("Выберите вашу роль:", reply_markup=keyboard_register)
            return

        if user.teacher_id is None:
            logging.info(f"user {message.from_user.id} is already registered as a teacher")
            await message.reply(f"Вы уже зарегестрированы как преподаватель, ID для приглашения слушателей - {user.id}")
        else:
            teacher = await session.get(User, user.teacher_id)
            logging.info(
                f"user {message.from_user.id} is already registered as a listener under @{teacher.tg_username}")
            await message.reply(f"Вы уже зарегестрированы как слушатель у @{teacher.tg_username}")

        await session.close()


async def callback_register_user(message: types.Message):
    teacher_id = int(message.text)  # Преобразуем текст в число

    async with async_session_maker() as session:
        session: AsyncSession

        teacher = await session.get(User, teacher_id)
        if teacher is None:
            logging.info(
                f"user {message.from_user.id} attempted to register with non-existing teacher ID: {teacher_id}")
            await message.answer("Преподаватель с таким ID не найден. Попробуйте снова.")
            return

        new_user = User(id=message.from_user.id, teacher_id=teacher_id, tg_username=message.from_user.username)
        session.add(new_user)
        await session.commit()
        await session.close()

        logging.info(f"user {message.from_user.id} registered as a student with teacher ID: {teacher_id}")
        await message.answer(f"Вы зарегистрированы как слушатель у @{teacher.tg_username}")


async def register_command(message: types.Message):
    instructions = (
        "Для регистрации API Яндекс Диска выполните следующие шаги:\n\n"
        f"1. Перейдите по [ссылке]({TOKEN_URL}):\n"
        "2. Авторизируйтесь:\n"
        "3. Cкопируйте ТОКЕН и вставьте его в /token ТОКЕН:\n"
    )

    logging.info(f"user {message.from_user.id} requested token registration instructions")
    await message.reply(instructions, parse_mode=ParseMode.MARKDOWN)


async def token_command(message: types.Message):
    async with async_session_maker() as session:
        session: AsyncSession

        user = await session.get(User, message.from_user.id)

        if user is None:
            logging.info(f"user {message.from_user.id} attempted to add token but is not registered as a teacher")
            await message.reply("Для добавления токена зарегистрируйтесь как преподаватель")
            return

        if user.teacher_id:
            logging.info(f"user {message.from_user.id} attempted to add token but is registered as a listener")
            await message.reply("Добавление токена доступно только преподавателю")
            return

        command_parts = message.text.split()

        if len(command_parts) < 2:
            if user.yadisk_token:
                logging.info(f"user {message.from_user.id} checked their current token (no token set)")
                await message.reply(f"Ваш текущий ТОКЕН = {user.yadisk_token}")
            else:
                logging.info(f"user {message.from_user.id} checked their current token")
                await message.reply("Для сохранения токена введите команду в формате `/token ВАШ_ТОКЕН`.")

            return

        token = command_parts[1].strip()

        client = YaDiskClient()
        result = await client.check_token_validity(token=token)

        if result:
            user.yadisk_token = token
            await session.commit()

            logging.info(f"user {message.from_user.id} set a new token: {token}")
            await message.reply(f"Ваш новый ТОКЕН = {token}")
        else:
            logging.info(f"user {message.from_user.id} attempted to add invalid token: {token}")
            await message.reply(f"Ошибка токена")


async def add_command(message: types.Message):
    async with async_session_maker() as session:
        session: AsyncSession

        text = message.text.split()

        if len(text) < 2:
            logging.info(f"user {message.from_user.id} attempted to add folder without path")
            await message.reply("Пожалуйста, укажите путь к папке на Яндекс Диске после команды /add ПУТЬ К ПАПКЕ")
            return

        folder_path = message.text.split()[1].strip()

        user = await session.get(User, message.from_user.id)

        if not user:
            logging.info(f"user {message.from_user.id} attempted to add folder but is not registered")
            await message.reply("Вы не зарегистрированы. Используйте команду /start для начала")
            return

        if user.teacher_id:
            logging.info(f"user {message.from_user.id} attempted to add folder but is registered as a listener")
            await message.reply("Команда доступна только преподавателю")
            return

        if not user.yadisk_token:
            logging.info(f"user {message.from_user.id} attempted to add folder without token")
            await message.reply("У Вас нет токена, используйте команду /token")
            return

        new_folder = YandexDiskFolder(teacher_id=user.id, path=folder_path)
        session.add(new_folder)
        await session.commit()

        logging.info(f"user {message.from_user.id} added a folder: {folder_path}")
        await message.reply(f"Папка с путём {folder_path} успешно добавлена в отслеживаемые")


async def delete_command(message: types.Message):
    async with async_session_maker() as session:
        session: AsyncSession

        text = message.text.split()

        if len(text) < 2:
            logging.info(f"user {message.from_user.id} attempted to delete folder without path")
            await message.reply("Пожалуйста, укажите путь к папке на Яндекс Диске после команды /delete ПУТЬ К ПАПКЕ")
            return

        folder_path = message.text.split()[1].strip()

        user = await session.get(User, message.from_user.id)

        if not user:
            logging.info(f"user {message.from_user.id} attempted to delete folder but is not registered")
            await message.reply("Вы не зарегистрированы. Используйте команду /start для начала")
            return

        if user.teacher_id:
            logging.info(f"user {message.from_user.id} attempted to delete folder but is registered as a listener")
            await message.reply("Команда доступна только преподавателю")
            return

        if not user.yadisk_token:
            logging.info(f"user {message.from_user.id} attempted to delete folder without token")

            await message.reply("У Вас нет токена, используйте команду /token")

            return

        stmt = select(YandexDiskFolder).filter(
            YandexDiskFolder.teacher_id == user.id,
            YandexDiskFolder.path == folder_path
        )
        result = await session.execute(stmt)
        folder = result.scalars().first()

        if not folder:
            logging.info(f"user {message.from_user.id} attempted to delete non-existent folder: {folder_path}")
            await message.reply("Папка с указанным путем не найдена")
            return

        await session.delete(folder)
        await session.commit()

        logging.info(f"user {message.from_user.id} deleted a folder: {folder_path}")
        await message.reply(f"Папка с путём {folder_path} успешно удалена из отслеживаемых")


def register_message_handler(router: Router):
    """Маршрутизация"""
    router.message.register(help_command, Command(commands=["help"]))
    router.message.register(status_command, Command(commands=["status"]))
    router.message.register(start_command, Command(commands=["start"]))
    router.message.register(register_command, Command(commands=["register"]))
    router.message.register(token_command, Command(commands=["token"]))
    router.message.register(add_command, Command(commands=["add"]))
    router.message.register(delete_command, Command(commands=["delete"]))
    router.message.register(callback_register_user)

    # callbacks
    router.callback_query.register(callback_start, lambda c: c.data.startswith('register_'))
