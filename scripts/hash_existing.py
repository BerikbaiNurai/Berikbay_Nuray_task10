from sqlmodel import Session, select
from database import engine
from models import User
from security import get_password_hash

def migrate():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for u in users:
            # пропускаем уже хешированные пароли
            if u.password.count("$") < 2:
                u.password = get_password_hash(u.password)
        session.commit()

if __name__ == "__main__":
    migrate()