from sqlalchemy import ForeignKey, String, create_engine, URL, Table, Column, Integer
from sqlalchemy.orm import DeclarativeBase, relationship, mapped_column, Mapped, sessionmaker

url_object = URL.create(
    "postgresql",
    username="example",
    password="example",  # plain (unescaped) text
    host="10.0.0.103",
    database="example",
)

engine = create_engine(url_object, echo=True)
Session = sessionmaker(bind=engine)

# declarative base class
class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)
    lastlogin: Mapped[int] = mapped_column(int)