import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Todo
from app.schemas import TodoIn, TodoOut, TodoUpdate
from app.services import widgets

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("", response_model=list[TodoOut])
def list_todos(include_all: bool = False, db: Session = Depends(get_db)) -> list[Todo]:
    if include_all:
        return list(db.scalars(select(Todo).order_by(Todo.created_at.desc())))
    return widgets.visible_todos(db)


@router.post("", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoIn, db: Session = Depends(get_db)) -> Todo:
    todo = Todo(**payload.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.patch("/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)) -> Todo:
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="not found")

    fields = payload.model_dump(exclude_unset=True)
    if "done" in fields and fields["done"] != todo.done:
        # completed_at drives the three-day visibility window.
        todo.completed_at = dt.datetime.now(dt.timezone.utc) if fields["done"] else None

    for field, value in fields.items():
        setattr(todo, field, value)

    db.commit()
    db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)) -> Response:
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(todo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
