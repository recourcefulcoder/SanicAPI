import uuid
from typing import Any, Dict, List, Optional

import bcrypt

from sqlalchemy import Column, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    full_name: Mapped[Optional[str]]
    password: Mapped[str]
    is_admin: Mapped[bool] = mapped_column(default=False)

    accounts: Mapped[List["Account"]] = relationship(
        back_populates="user",
        cascade="all, delete, delete-orphan",
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="receiver"
    )

    def __str__(self):
        str_repr = (
            f"id: {self.id}\n"
            f"Email: {self.email}\nFull name: {self.full_name}\n"
        )
        return str_repr

    def set_password(self, password: str):
        pwhash = bcrypt.hashpw(
            password.encode(encoding="utf-8"), bcrypt.gensalt()
        )
        self.password = pwhash.decode(encoding="utf-8")

    def verify_password(self, password: str) -> bool:
        bpass = password.encode("utf-8")
        return bcrypt.checkpw(bpass, self.password.encode(encoding="utf-8"))

    def serialize(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_admin": self.is_admin,
        }


class Account(Base):
    __tablename__ = "account"
    id: Mapped[int] = mapped_column(primary_key=True)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(
        back_populates="accounts", foreign_keys=[user_id]
    )

    transactions: Mapped[List["Transaction"]] = relationship(
        back_populates="account"
    )

    def serialize(self) -> Dict[str, Any]:
        return {"id": self.id, "balance": self.balance}


class Transaction(Base):
    __tablename__ = "transaction"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))

    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    account: Mapped["Account"] = relationship(back_populates="transactions")

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    receiver: Mapped["User"] = relationship(back_populates="transactions")

    def serialize(self):
        return {
            "id": str(self.id),
            "amount": self.amount,
            "account_id": self.account_id,
        }


async def create_user(
    bind,
    email: str = "default@example.com",
    full_name: str = "John Doe",
    password: str = "123456",
    is_admin: bool = False,
):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async with async_sessionmaker(bind=bind)() as session:
        user = User(email=email, full_name=full_name, is_admin=is_admin)
        user.set_password(password)
        session.add(user)
        await session.commit()


async def create_superuser(
    bind,
    email: str = "admin@example.com",
    full_name: str = "admin",
    password: str = "admin",
):
    return await create_user(bind, email, full_name, password, is_admin=True)


if __name__ == "__main__":
    import asyncio
    from pathlib import Path
    import sys

    path = Path(__file__).resolve().parent.parent
    sys.path.append(str(path))
    # in order to let application see the config.py,
    # required in database.engine module

    from engine import engine

    asyncio.run(create_superuser(engine))
