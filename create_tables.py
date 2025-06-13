from sqlmodel import SQLModel, create_engine
from database import DATABASE_URL
from models import User
engine = create_engine(DATABASE_URL, echo=True)

if __name__ == "__main__":
    SQLModel.metadata.create_all(engine)
    print("✅ Таблицы созданы")
