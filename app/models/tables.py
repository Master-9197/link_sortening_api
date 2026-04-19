from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy import ForeignKey


class Base(DeclarativeBase):
    pass


class Links(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    url: Mapped[str]
    hash: Mapped[str] = mapped_column(unique=True)

    # Relationships:
    user: Mapped["Users"] = relationship(back_populates="links", cascade="all, delete")


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    login: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]

    # Relationships:
    links: Mapped["Links"] = relationship(back_populates="user")
