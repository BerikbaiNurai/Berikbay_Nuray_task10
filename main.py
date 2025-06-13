from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List, Optional

from database import engine, create_db_and_tables
from models import User, Note
from schemas import (
    UserCreate, UserLogin, UserResponse,
    NoteCreate, NoteUpdate, NoteOut
)
from security import get_password_hash, verify_password
from auth import (
    create_access_token,
    get_current_user,
    require_role
)

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    with Session(engine) as session:
        if session.exec(select(User).where(User.username == user.username)).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        hashed = get_password_hash(user.password)
        db_user = User(username=user.username, password=hashed)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return UserResponse(id=db_user.id, username=db_user.username, role=db_user.role)


@app.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, username=current_user.username, role=current_user.role)


@app.get("/admin/users", response_model=List[UserResponse])
def read_all_users(current_user: User = Depends(require_role("admin"))):
    with Session(engine) as session:
        users = session.exec(select(User)).all()
    return [UserResponse(id=u.id, username=u.username, role=u.role) for u in users]


@app.post("/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    note_in: NoteCreate,
    current_user: User = Depends(get_current_user)
):
    note = Note(
        title=note_in.title,
        content=note_in.content,
        owner_id=current_user.id
    )
    with Session(engine) as session:
        session.add(note)
        session.commit()
        session.refresh(note)
    return note


@app.get("/notes", response_model=List[NoteOut])
def read_notes(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    search: Optional[str] = Query(None)
):
    with Session(engine) as session:
        stmt = select(Note).where(Note.owner_id == current_user.id)
        if search:
            stmt = stmt.where(
                (Note.title.contains(search)) |
                (Note.content.contains(search))
            )
        notes = session.exec(stmt.offset(skip).limit(limit)).all()
    return notes


@app.get("/notes/{note_id}", response_model=NoteOut)
def read_note(note_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        note = session.get(Note, note_id)
    if not note or note.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@app.put("/notes/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    note_in: NoteUpdate,
    current_user: User = Depends(get_current_user)
):
    with Session(engine) as session:
        note = session.get(Note, note_id)
        if not note or note.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        for field, value in note_in.dict(exclude_unset=True).items():
            setattr(note, field, value)
        session.add(note)
        session.commit()
        session.refresh(note)
    return note


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        note = session.get(Note, note_id)
        if not note or note.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        session.delete(note)
        session.commit()
    return
