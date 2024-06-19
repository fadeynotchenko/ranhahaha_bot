import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from client import logger, YaDiskClient
from db import async_session_maker
from sqlalchemy import select

from db.models import YandexDiskFolder, User


async def notificate_users(users, folder, bot: Bot):
    for user in users:
        try:
            await bot.send_message(chat_id=user.id, text=f"Уведомление о добавлении файла в {folder}")
            logger.info(f"Message sent to user with ID {user.id}")
        except TelegramBadRequest as e:
            logger.error(f"Error sending message to user with ID {user.id}: {e}")


async def notificate_listeners(bot):
    sleep_time = 60 * 30

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
                date = await client.get_latest_modified_time(folder.path)

                logger.info(f"Last modified time for {folder.path} - {date}")

                if date and date != folder.last_date_update and date is not None:
                    folder.last_date_update = date
                    await session.commit()

                    stmt = select(User).filter(User.teacher_id is folder.teacher_id)
                    result = await session.execute(stmt)
                    listeners = result.scalars()

                    await notificate_users(listeners, folder.path, bot)

            await session.close()

        logger.info(f"Sleeping for {sleep_time} seconds")
        await asyncio.sleep(sleep_time)
