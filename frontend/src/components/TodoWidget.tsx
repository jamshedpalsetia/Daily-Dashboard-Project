import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import { shortDate, todayISO } from "../lib/format";
import type { Priority, Todo } from "../lib/types";
import { Widget } from "./Widget";

const PRIORITIES: Priority[] = ["low", "medium", "high"];

function dueClass(todo: Todo, today: string): string {
  if (!todo.due_date || todo.done) return "";
  if (todo.due_date < today) return "due overdue";
  if (todo.due_date === today) return "due today";
  return "due";
}

export function TodoWidget() {
  const queryClient = useQueryClient();
  const today = todayISO();

  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState<Priority>("medium");
  const [dueDate, setDueDate] = useState("");

  const query = useQuery({ queryKey: ["todos"], queryFn: api.todos });
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["todos"] });

  const add = useMutation({
    mutationFn: api.addTodo,
    onSuccess: () => {
      setTitle("");
      setDueDate("");
      setPriority("medium");
      invalidate();
    },
  });

  const toggle = useMutation({
    mutationFn: ({ id, done }: { id: number; done: boolean }) => api.updateTodo(id, { done }),
    onMutate: async ({ id, done }) => {
      await queryClient.cancelQueries({ queryKey: ["todos"] });
      const previous = queryClient.getQueryData<Todo[]>(["todos"]);
      queryClient.setQueryData<Todo[]>(["todos"], (old) =>
        (old ?? []).map((t) => (t.id === id ? { ...t, done } : t)),
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) queryClient.setQueryData(["todos"], context.previous);
    },
    onSettled: invalidate,
  });

  const remove = useMutation({ mutationFn: api.deleteTodo, onSuccess: invalidate });

  const todos = query.data ?? [];
  const open = todos.filter((t) => !t.done);
  const done = todos.filter((t) => t.done);
  const overdue = open.filter((t) => t.due_date && t.due_date < today).length;

  return (
    <Widget
      title="To-do"
      subtitle={`${open.length} open${overdue ? ` · ${overdue} overdue` : ""}`}
      isLoading={query.isLoading}
      error={query.error as Error | null}
      rows={5}
    >
      <form
        className="row-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!title.trim()) return;
          add.mutate({ title: title.trim(), priority, due_date: dueDate || null });
        }}
      >
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Add a task…"
          className="input input-grow"
          aria-label="Task title"
        />
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value as Priority)}
          className="input input-select"
          aria-label="Priority"
        >
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          className="input input-date"
          aria-label="Due date"
        />
        <button className="btn" type="submit" disabled={add.isPending}>
          Add
        </button>
      </form>

      {todos.length === 0 ? (
        <p className="empty">Nothing on the list. Enjoy the day.</p>
      ) : (
        <ul className="todos">
          {[...open, ...done].map((todo) => (
            <li key={todo.id} className={todo.done ? "todo done" : "todo"}>
              <label>
                <input
                  type="checkbox"
                  checked={todo.done}
                  onChange={(e) => toggle.mutate({ id: todo.id, done: e.target.checked })}
                />
                <span className={`dot dot-${todo.priority}`} title={`${todo.priority} priority`} />
                <span className="todo-title">{todo.title}</span>
              </label>
              <span className="todo-right">
                {todo.due_date && (
                  <span className={dueClass(todo, today)}>{shortDate(todo.due_date)}</span>
                )}
                <button
                  className="icon-btn"
                  aria-label={`Delete ${todo.title}`}
                  onClick={() => remove.mutate(todo.id)}
                >
                  ×
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}

      {done.length > 0 && (
        <p className="hint">Completed items disappear three days after you check them.</p>
      )}
    </Widget>
  );
}
