from sqlalchemy import BigInteger, String, Column
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql+asyncpg://dbuser:my_secure_password_123@database:5432/dbname"

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Отражаем существующую таблицу Django

class CustomUser(Base):
    __tablename__ = 'subscriptions_customuser'

    id = Column(BigInteger, primary_key=True)
    phone = Column(String(13))
    telegram_id = Column(BigInteger)
    chat_id = Column(BigInteger)

    def __repr__(self):
        return f"<User(id={self.id}, phone='{self.phone}')>"