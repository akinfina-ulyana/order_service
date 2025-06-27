# from aiogram import Router, F
# from aiogram.types import Message
# from aiogram import Router, types
# from aiogram.filters import Command
# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
# from sqlalchemy import text
# from .models import engine
#
# router = Router()
#
#
# @router.message(Command("start"))
# async def cmd_start(message: types.Message):
#     # Создаем кнопку
#     button = KeyboardButton(
#         text="📱 Поделиться номером",
#         request_contact=True
#     )
#
#     # Создаем клавиатуру
#     keyboard = ReplyKeyboardMarkup(
#         keyboard=[[button]],
#         resize_keyboard=True,
#         one_time_keyboard=True
#     )
#
#     await message.answer(
#         "Нажмите кнопку ниже, чтобы поделиться номером",
#         reply_markup=keyboard
#     )
#
#
# @router.message(F.contact)
# async def handle_contact(message: types.Message):
#     contact = message.contact
#     user = message.from_user
#
#
#     if not contact.phone_number:
#         await message.answer("Не удалось получить номер телефона")
#         return
#
#     try:
#         phone = contact.phone_number
#
#         with engine.connect() as conn:
#             # Проверяем существование пользователя
#             user_exists = conn.execute(
#                 text("SELECT 1 FROM subscriptions_customuser WHERE phone = :phone"),
#                 {"phone": phone}
#             ).fetchone()
#
#             if not user_exists:
#                 await message.answer("Ваш номер не найден в системе")
#                 return
#
#             # Обновляем telegram_id
#             conn.execute(
#                 text("""
#                     UPDATE subscriptions_customuser
#                     SET telegram_id = :tg_id
#                     WHERE phone = :phone
#                 """),
#                 {"tg_id": user.id, "phone": phone}
#             )
#             conn.commit()
#
#         await message.answer(
#             "✅ Вы успешно зарегистрированы в системе!",
#             reply_markup=types.ReplyKeyboardRemove()
#         )
#
#     except Exception as e:
#         await message.answer("Произошла ошибка, попробуйте позже")
#         print(f"Error: {e}")
#


from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from .models import engine, CustomUser, async_session
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    button = KeyboardButton(text="📱 Поделиться номером", request_contact=True)
    keyboard = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True, one_time_keyboard=True)
    await message.answer("Нажмите кнопку ниже, чтобы поделиться номером", reply_markup=keyboard)

@router.message(Command("test_db"))
async def test_db_connection(message: types.Message):
    print("Команда /test_db получена!")
    try:
        async with async_session() as session:
            result = await session.execute(select(1))
            test_value = result.scalar()
            logger.info(f"DB test successful. Result: {test_value}")
            await message.answer("✅ Подключение к БД работает!")
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        await message.answer("❌ Ошибка подключения к БД")


@router.message(F.contact)
async def handle_contact(message: types.Message):
    if not message.contact:
        await message.answer("Не удалось получить контакт", reply_markup=ReplyKeyboardRemove())
        return

    contact = message.contact
    user = message.from_user
    chat_id = message.chat.id

    logger.info(f"User {user.id} shared phone: {contact.phone_number}, {chat_id}")

    if not contact.phone_number:
        await message.answer("Не удалось получить номер телефона", reply_markup=ReplyKeyboardRemove())
        return

    try:
        phone = contact.phone_number

        async with async_session() as session:
            db_user = await session.execute(select(CustomUser).where(CustomUser.phone == phone))
            db_user = db_user.scalar_one_or_none()

            if not db_user:
                await message.answer(
                    "Ваш номер не найден в системе, пройдите для регистрации (сайт)",
                    reply_markup=ReplyKeyboardRemove()
                )
                return

            db_user.telegram_id = user.id
            db_user.chat_id = chat_id
            session.add(db_user)
            await session.commit()

        await message.answer(
            "✅ Вы успешно зарегистрированы в системе!",
            reply_markup=ReplyKeyboardRemove()
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        await message.answer("Ошибка базы данных", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await message.answer("Произошла ошибка, попробуйте позже", reply_markup=ReplyKeyboardRemove())