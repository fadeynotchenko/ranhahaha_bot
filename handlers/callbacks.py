import logging

from aiogram import types
from aiogram.dispatcher import router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from db import async_session_maker, User


# Callback_query_handler - это функция, которая позволяет обрабатывать коллбек-запросы от пользователей.
# Коллбэк-запрос - это запрос, который отправляется боту, когда пользователь нажимает кнопку в его чате.
# Обработчик для callback с F.data для aiogram3
# https://ru.stackoverflow.com/questions/1565436/%D0%9A%D0%B0%D0%BA-%D1%81%D0%B4%D0%B5%D0%BB%D0%B0%D1%82%D1%8C-%D0%BE%D0%B1%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D1%87%D0%B8%D0%BA-%D0%BA%D0%BE%D0%BB%D0%B1%D0%B5%D0%BA%D0%BE%D0%B2-%D0%B2-aiogram-3


async def callback_start(callback: CallbackQuery):
    await callback.answer()
    role = callback.data.split("_")[1]  # Извлекаем роль из данных коллбека

    async with async_session_maker() as session:
        session: AsyncSession

        if role == "teacher":
            new_user = User(id=callback.from_user.id, tg_username=callback.from_user.username)
            session.add(new_user)
            await session.commit()
            await callback.message.answer(f"Вы зарегистрировались как преподаватель. Ваш ID для приглашения слушателей {new_user.id}")
        else:
            await callback.message.answer("Пожалуйста, введите ID вашего преподавателя:")
        logging.info(f"user {callback.from_user.id} selected role: {role}")

