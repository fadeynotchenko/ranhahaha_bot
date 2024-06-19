# __all__ - публичный список объектов
# https://ru.stackoverflow.com/questions/27983/%D0%A7%D1%82%D0%BE-%D1%82%D0%B0%D0%BA%D0%BE%D0%B5-all-%D0%B2-python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


# Декларативная модель базы данных
# https://metanit.com/python/database/3.2.php
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, index=True, primary_key=True)

    teacher_id = Column(Integer, nullable=True)

    yadisk_token = Column(String, nullable=True)

    tg_username = Column(String)

class YandexDiskFolder(Base):
    __tablename__ = 'yandex_disk_folders'

    id = Column(Integer, index=True, primary_key=True)

    teacher_id = Column(Integer)

    path = Column(String)

    last_date_update = Column(String, nullable=True)
