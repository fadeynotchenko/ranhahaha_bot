import asyncio
import json

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from client import logger, YaDiskClient
from db import async_session_maker
from sqlalchemy import select

from db.models import YandexDiskFolder, User


async def check_dates(lhs, rhs):
    if lhs is None and rhs is None:
        return True

    if lhs is None or rhs is None:
        return False

    try:
        lhs_json = json.loads(lhs)
        rhs_json = json.loads(rhs)
    except json.JSONDecodeError:
        return False

    return lhs_json == rhs_json


async def notificate_users(users, folder, bot: Bot):
    for user in users:
        try:
            await bot.send_message(chat_id=user.id, text=f"Уведомление о добавлении файла в {folder}")
            logger.info(f"Message sent to user with ID {user.id}")
        except TelegramBadRequest as e:
            logger.error(f"Error sending message to user with ID {user.id}: {e}")


async def notificate_listeners(bot):
    sleep_time = 20

    while True:
        logger.info("Waking up to check for updates")

        async with async_session_maker() as session:
            # Fetch all folders
            stmt = select(YandexDiskFolder)
            result = await session.execute(stmt)
            folders = result.scalars()

            for folder in folders:
                teacher = await session.get(User, folder.teacher_id)

                client = YaDiskClient(token=teacher.yadisk_token)
                new_dates = await client.get_json_of_items_dates_from_yandex_disk(folder.path)

                if not await check_dates(new_dates, folder.dates):
                    folder.dates = new_dates

                    await session.commit()

                    stmt = select(User).filter(
                        User.teacher_id == folder.teacher_id
                    )

                    result = await session.execute(stmt)
                    users = result.scalars().all()

                    await notificate_users(users, folder.path, bot)

            await session.close()

        logger.info(f"Sleeping for {sleep_time} seconds")
        await asyncio.sleep(sleep_time)
