"""Live kanban board for the markdown backlog in docs/backlog.

The markdown files stay the single source of truth. This module parses the
EPIC-*.md task blocks on every change and serves the board at
http://127.0.0.1:8765, pushing updates to the browser over SSE. Nothing is
generated on disk: the HTML is served from this file.

Usage:
    python tools/tablero_backlog.py              # read-only board
    python tools/tablero_backlog.py --write      # drag and drop rewrites the markdown
    python tools/tablero_backlog.py --open       # open the default browser
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

BACKLOG_DIR = Path(__file__).resolve().parents[1] / "docs" / "backlog"
EPIC_GLOB = "EPIC-*.md"
INDEX_FILE = "README.md"

# Column order follows the workflow documented in docs/backlog/README.md.
COLUMN_ORDER = ["propuesta", "en grill", "lista", "en curso", "bloqueada", "hecha"]
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

TASK_HEADING = re.compile(r"^## (T-\d+)\s+·\s+(.+?)\s*$")
STATE_LINE = re.compile(
    r"^- \*\*Estado:\*\*\s*(?P<estado>.+?)\s+·\s+"
    r"\*\*Prioridad:\*\*\s*(?P<prioridad>.+?)\s+·\s+"
    r"\*\*Épica:\*\*\s*(?P<epica>\S+)\s*$"
)
STATE_INLINE = re.compile(r"(\*\*Estado:\*\*)(\s*)([^·\n]*?)(\s*)·")
DEPS_LINE = re.compile(r"^- \*\*Depende de:\*\*\s*(?P<deps>.+?)\s*$")
INDEX_ROW = re.compile(r"^\|\s*(?P<id>T-\d+)\s*\|")

VERSION = None  # type: ignore[assignment]
WRITE_ENABLED = False


class Version:
    """Monotonic counter that lets SSE handlers wait for the next change."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._value = 0

    def value(self) -> int:
        with self._condition:
            return self._value

    def bump(self) -> int:
        with self._condition:
            self._value += 1
            self._condition.notify_all()
            return self._value

    def wait(self, last_seen: int, timeout: float) -> int:
        with self._condition:
            if self._value == last_seen:
                self._condition.wait(timeout)
            return self._value


def read_text(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path: Path, text: str) -> None:
    """Write through a temporary file so a crash never truncates the source."""
    temp = path.with_name(path.name + ".tmp")
    with open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    temp.replace(path)


def parse_epic(path: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    lines = read_text(path).splitlines()

    def close() -> None:
        nonlocal current
        if current is not None:
            tasks.append(current)
            current = None

    for index, line in enumerate(lines):
        heading = TASK_HEADING.match(line)
        if heading:
            close()
            current = {
                "id": heading.group(1),
                "titulo": heading.group(2),
                "archivo": path.name,
                "linea_estado": None,
                "estado": "propuesta",
                "prioridad": "P3",
                "epica": "",
                "ac_hechos": 0,
                "ac_total": 0,
                "depende_de": "",
            }
            continue

        if current is None:
            continue

        if line.startswith("## ") or line.startswith("# "):
            close()
            continue

        state = STATE_LINE.match(line)
        if state and current["linea_estado"] is None:
            current["estado"] = state.group("estado").strip()
            current["prioridad"] = state.group("prioridad").strip()
            current["epica"] = state.group("epica").strip()
            current["linea_estado"] = index + 1
            continue

        stripped = line.strip()
        if stripped.startswith("- [x]") or stripped.startswith("- [X]"):
            current["ac_hechos"] += 1
            current["ac_total"] += 1
        elif stripped.startswith("- [ ]"):
            current["ac_total"] += 1
        else:
            deps = DEPS_LINE.match(stripped)
            if deps:
                current["depende_de"] = deps.group("deps").strip()

    close()
    return tasks


def parse_index() -> dict[str, str]:
    """Read the README index table so the board can flag a desynced status."""
    path = BACKLOG_DIR / INDEX_FILE
    if not path.exists():
        return {}

    states: dict[str, str] = {}
    for line in read_text(path).splitlines():
        if not INDEX_ROW.match(line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 5:
            states[cells[0]] = cells[4]
    return states


def collect() -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    for path in sorted(BACKLOG_DIR.glob(EPIC_GLOB)):
        tasks.extend(parse_epic(path))

    index = parse_index()
    for task in tasks:
        listed = index.get(task["id"])
        task["index_estado"] = listed or ""
        task["desincronizada"] = bool(listed) and listed != task["estado"]

    by_state: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        by_state.setdefault(task["estado"], []).append(task)

    columns = []
    for state in COLUMN_ORDER:
        columns.append({"estado": state, "tareas": by_state.pop(state, [])})
    for state in sorted(by_state):
        columns.append({"estado": state, "tareas": by_state[state]})

    for column in columns:
        column["tareas"].sort(
            key=lambda task: (PRIORITY_ORDER.get(task["prioridad"], 9), task["id"])
        )

    hechas = sum(1 for task in tasks if task["estado"] == "hecha")
    ac_hechos = sum(task["ac_hechos"] for task in tasks)
    ac_total = sum(task["ac_total"] for task in tasks)

    return {
        "version": VERSION.value(),
        "write": WRITE_ENABLED,
        "total": len(tasks),
        "desincronizadas": sum(1 for task in tasks if task["desincronizada"]),
        "resumen": {
            "total": len(tasks),
            "hechas": hechas,
            "porcentaje": round(hechas * 100 / len(tasks)) if tasks else 0,
            "ac_hechos": ac_hechos,
            "ac_total": ac_total,
            "ac_porcentaje": round(ac_hechos * 100 / ac_total) if ac_total else 0,
        },
        "columns": columns,
    }


def update_state(task_id: str, new_state: str) -> dict[str, Any]:
    """Rewrite the state in the epic file and in the README index."""
    new_state = new_state.strip()
    if not new_state or "·" in new_state or "\n" in new_state:
        raise ValueError(f"estado invalido: {new_state!r}")

    task = next((item for item in collect_tasks() if item["id"] == task_id), None)
    if task is None:
        raise KeyError(task_id)
    if task["linea_estado"] is None:
        raise ValueError(f"{task_id} no tiene linea de estado")

    touched: list[str] = []

    epic_path = BACKLOG_DIR / task["archivo"]
    epic_text = read_text(epic_path)
    lines = epic_text.splitlines(keepends=True)
    index = task["linea_estado"] - 1
    patched, count = STATE_INLINE.subn(
        lambda match: f"{match.group(1)}{match.group(2)}{new_state}{match.group(4)}·",
        lines[index],
        count=1,
    )
    if count == 0:
        raise ValueError(f"no se pudo reescribir el estado de {task_id}")
    if patched != lines[index]:
        lines[index] = patched
        write_text(epic_path, "".join(lines))
        touched.append(str(epic_path.name))

    index_path = BACKLOG_DIR / INDEX_FILE
    if index_path.exists():
        index_lines = read_text(index_path).splitlines(keepends=True)
        for position, line in enumerate(index_lines):
            if not INDEX_ROW.match(line):
                continue
            cells = line.strip().strip("|").split("|")
            if cells[0].strip() != task_id or len(cells) < 5:
                continue
            if cells[4].strip() == new_state:
                break
            cells[4] = f" {new_state} "
            ending = "\n" if line.endswith("\n") else ""
            index_lines[position] = "|" + "|".join(cells) + "|" + ending
            write_text(index_path, "".join(index_lines))
            touched.append(str(index_path.name))
            break

    return {"id": task_id, "estado": new_state, "archivos": touched}


def collect_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for path in sorted(BACKLOG_DIR.glob(EPIC_GLOB)):
        tasks.extend(parse_epic(path))
    return tasks


def fingerprint() -> tuple[tuple[str, int, int], ...]:
    entries = []
    for path in sorted(BACKLOG_DIR.glob("*.md")):
        try:
            stat = path.stat()
        except OSError:
            continue
        entries.append((path.name, stat.st_mtime_ns, stat.st_size))
    return tuple(entries)


def watch_changes() -> None:
    previous = fingerprint()
    while True:
        time.sleep(0.6)
        current = fingerprint()
        if current != previous:
            previous = current
            VERSION.bump()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "BacklogBoard/1.0"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass

    def send_payload(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        route = self.path.split("?", 1)[0]
        if route == "/":
            body = PAGE.replace("__WRITE__", "true" if WRITE_ENABLED else "false").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if route == "/api/tablero":
            self.send_payload(collect())
            return
        if route == "/eventos":
            self.stream_events()
            return
        self.send_payload({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        route = self.path.split("?", 1)[0]
        if route != "/api/estado":
            self.send_payload({"error": "not found"}, status=404)
            return
        if not WRITE_ENABLED:
            self.send_payload({"error": "el tablero esta en solo lectura"}, status=403)
            return

        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            result = update_state(str(payload.get("id", "")), str(payload.get("estado", "")))
        except (ValueError, KeyError) as error:
            self.send_payload({"error": str(error)}, status=400)
            return

        VERSION.bump()
        self.send_payload(result)

    def stream_events(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        self.close_connection = True

        last = VERSION.value()
        try:
            self.wfile.write(b"retry: 1000\n\n")
            self.wfile.write(f"data: {json.dumps({'version': last})}\n\n".encode())
            self.wfile.flush()
            while True:
                current = VERSION.wait(last, timeout=15.0)
                if current != last:
                    last = current
                    message = f"data: {json.dumps({'version': last})}\n\n"
                else:
                    message = ": ping\n\n"
                self.wfile.write(message.encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return


PAGE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Backlog · Tablero</title>
<style>
  :root {
    --page: #F7F7F5;
    --card: #FFFFFF;
    --border: #E5E5E5;
    --text: #111111;
    --muted: #6B6B6B;
    --danger: #B42318;
    --success: #067647;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0;
    background: var(--page);
    color: var(--text);
    font: 14px/1.45 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    flex-direction: column;
  }
  .bar {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px 16px;
    padding: 12px 20px;
    background: var(--card);
    border-bottom: 1px solid var(--border);
  }
  .brand { display: flex; align-items: baseline; gap: 10px; flex: none; }
  .brand h1 { font-size: 15px; margin: 0; letter-spacing: -0.01em; }
  .total { color: var(--muted); font-size: 12px; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .summary { display: flex; align-items: center; gap: 10px; flex: none; }
  .pct { font-size: 16px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .meter {
    width: 100px;
    height: 6px;
    background: var(--page);
    border: 1px solid var(--border);
    border-radius: 999px;
    overflow: hidden;
    flex: none;
  }
  .meter i { display: block; height: 100%; background: var(--text); transition: width 0.25s ease; }
  .meter i[data-full="true"] { background: var(--success); }
  .live {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    white-space: nowrap;
  }
  .live::before {
    content: "";
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--success);
  }
  .live[data-state="off"]::before { background: var(--muted); }
  .live[data-state="on"]::before { animation: pulse 2s ease-in-out infinite; }
  @keyframes pulse { 50% { opacity: 0.35; } }
  .drift { font-size: 12px; color: var(--danger); }
  .drift[hidden] { display: none; }
  #q {
    margin-left: auto;
    flex: 1 1 200px;
    min-width: 160px;
    max-width: 320px;
    padding: 7px 10px;
    font: inherit;
    color: var(--text);
    background: var(--page);
    border: 1px solid var(--border);
    border-radius: 6px;
  }
  #q:focus { outline: 2px solid var(--text); outline-offset: -1px; }
  .error {
    margin: 12px 20px 0;
    padding: 10px 12px;
    border: 1px solid var(--danger);
    border-radius: 6px;
    color: var(--danger);
    background: var(--card);
    font-size: 13px;
  }
  .board {
    flex: 1;
    display: grid;
    grid-auto-flow: column;
    grid-auto-columns: minmax(250px, 1fr);
    gap: 14px;
    padding: 18px 20px 24px;
    overflow-x: auto;
    align-items: start;
  }
  .column {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    min-height: 120px;
    max-height: 100%;
  }
  .column[data-over="true"] { border-color: var(--text); }
  .column header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
  }
  .column h2 {
    margin: 0;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--muted);
  }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); flex: none; }
  .dot[data-state="lista"] { background: var(--text); }
  .dot[data-state="en curso"] { background: var(--text); }
  .dot[data-state="bloqueada"] { background: var(--danger); }
  .dot[data-state="hecha"] { background: var(--success); }
  .count { margin-left: auto; font-size: 11px; color: var(--muted); font-variant-numeric: tabular-nums; }
  .cards { display: flex; flex-direction: column; gap: 8px; padding: 10px; overflow-y: auto; }
  .card {
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px;
    background: var(--card);
    cursor: default;
  }
  .card[draggable="true"] { cursor: grab; }
  .card.dragging { opacity: 0.4; }
  .card.done h3 { color: var(--muted); }
  .card-top { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
  .id { font-size: 11px; font-weight: 600; letter-spacing: 0.02em; color: var(--muted); }
  .prio {
    font-size: 10px;
    font-weight: 600;
    padding: 1px 5px;
    border-radius: 4px;
    border: 1px solid var(--border);
    color: var(--muted);
  }
  .prio[data-p="P0"] { background: var(--text); color: #FFFFFF; border-color: var(--text); }
  .prio[data-p="P1"] { color: var(--text); border-color: var(--muted); }
  .card h3 {
    margin: 0 0 6px;
    font-size: 13px;
    font-weight: 500;
    line-height: 1.35;
  }
  .meta { display: flex; flex-wrap: wrap; gap: 8px; font-size: 11px; color: var(--muted); }
  .drift-flag { color: var(--danger); }
  .progress { height: 3px; margin-top: 8px; background: var(--page); border-radius: 2px; overflow: hidden; }
  .progress i { display: block; height: 100%; background: var(--text); }
  .progress i[data-full="true"] { background: var(--success); }
  .empty { margin: 0; padding: 6px 2px; font-size: 12px; color: var(--muted); }
  @media (max-width: 820px) {
    .board {
      grid-auto-flow: row;
      grid-auto-columns: auto;
      grid-template-columns: minmax(0, 1fr);
      overflow-x: visible;
    }
    .column { max-height: none; min-height: 0; }
    .cards { overflow-y: visible; }
  }
</style>
</head>
<body>
<header class="bar">
  <div class="brand">
    <span class="live" id="live" data-state="off">en vivo</span>
    <h1>Backlog</h1>
  </div>
  <div class="summary">
    <span class="pct" id="pct">0%</span>
    <div class="meter"><i id="pct-bar" style="width: 0%"></i></div>
    <span class="total" id="total"></span>
    <span class="total" id="ac-total"></span>
  </div>
  <span class="drift" id="drift" hidden></span>
  <input id="q" type="search" placeholder="Filtrar por ID, titulo o epica" autocomplete="off">
</header>
<div class="error" id="error" hidden>No se pudo leer el backlog. Revisa la consola del servidor.</div>
<main class="board" id="board"></main>
<script>
const WRITE = __WRITE__;
const board = document.getElementById('board');
const live = document.getElementById('live');
const total = document.getElementById('total');
const drift = document.getElementById('drift');
const errorBox = document.getElementById('error');
const search = document.getElementById('q');
let cache = null;

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function card(task) {
  const element = node('article', 'card');
  element.dataset.id = task.id;
  element.dataset.search = (task.id + ' ' + task.titulo + ' ' + task.epica + ' ' + task.estado).toLowerCase();
  if (task.estado === 'hecha') element.classList.add('done');

  if (WRITE) {
    element.draggable = true;
    element.addEventListener('dragstart', (event) => {
      event.dataTransfer.setData('text/plain', task.id);
      event.dataTransfer.effectAllowed = 'move';
      element.classList.add('dragging');
    });
    element.addEventListener('dragend', () => element.classList.remove('dragging'));
  }

  const top = node('div', 'card-top');
  top.append(node('span', 'id', task.id));
  const prio = node('span', 'prio', task.prioridad);
  prio.dataset.p = task.prioridad;
  top.append(prio);
  element.append(top, node('h3', null, task.titulo));

  const meta = node('div', 'meta');
  meta.append(node('span', null, 'epica ' + (task.epica || '-'))); 
  if (task.ac_total > 0) meta.append(node('span', null, 'AC ' + task.ac_hechos + '/' + task.ac_total));
  if (task.depende_de) meta.append(node('span', null, 'deps ' + task.depende_de));
  if (task.desincronizada) {
    const flag = node('span', 'drift-flag', 'README: ' + task.index_estado);
    flag.title = 'El indice README dice "' + task.index_estado + '" y la epica dice "' + task.estado + '"';
    meta.append(flag);
  }
  element.append(meta);

  if (task.ac_total > 0) {
    const bar = node('div', 'progress');
    const fill = node('i');
    fill.style.width = Math.round((task.ac_hechos / task.ac_total) * 100) + '%';
    if (task.ac_hechos === task.ac_total) fill.dataset.full = 'true';
    bar.append(fill);
    element.append(bar);
  }
  return element;
}

function column(entry) {
  const section = node('section', 'column');
  section.dataset.estado = entry.estado;

  const header = node('header');
  const dot = node('span', 'dot');
  dot.dataset.state = entry.estado;
  header.append(dot, node('h2', null, entry.estado), node('span', 'count', String(entry.tareas.length)));
  section.append(header);

  const cards = node('div', 'cards');
  if (entry.tareas.length === 0) cards.append(node('p', 'empty', 'Sin tareas'));
  entry.tareas.forEach((task) => cards.append(card(task)));
  section.append(cards);

  if (WRITE) {
    section.addEventListener('dragover', (event) => {
      event.preventDefault();
      section.dataset.over = 'true';
    });
    section.addEventListener('dragleave', () => delete section.dataset.over);
    section.addEventListener('drop', async (event) => {
      event.preventDefault();
      delete section.dataset.over;
      const id = event.dataTransfer.getData('text/plain');
      if (!id) return;
      await move(id, entry.estado);
    });
  }
  return section;
}

function applyFilter() {
  const needle = search.value.trim().toLowerCase();
  board.querySelectorAll('.card').forEach((element) => {
    element.hidden = needle !== '' && !element.dataset.search.includes(needle);
  });
  board.querySelectorAll('.column').forEach((section) => {
    const visible = section.querySelectorAll('.card:not([hidden])').length;
    section.querySelector('.count').textContent = String(visible);
  });
}

function render(data) {
  cache = data;
  const scroll = board.scrollLeft;
  board.replaceChildren(...data.columns.map(column));
  board.scrollLeft = scroll;

  const resumen = data.resumen;
  document.getElementById('pct').textContent = resumen.porcentaje + '%';
  const meter = document.getElementById('pct-bar');
  meter.style.width = resumen.porcentaje + '%';
  if (resumen.porcentaje === 100) meter.dataset.full = 'true';
  else delete meter.dataset.full;

  total.textContent = resumen.hechas + '/' + resumen.total + ' tareas hechas' + (data.write ? ' · arrastrable' : '');
  document.getElementById('ac-total').textContent = resumen.ac_total
    ? 'AC ' + resumen.ac_hechos + '/' + resumen.ac_total + ' · ' + resumen.ac_porcentaje + '%'
    : '';

  if (data.desincronizadas > 0) {
    drift.hidden = false;
    drift.textContent = data.desincronizadas + ' con estado distinto en README';
  } else {
    drift.hidden = true;
  }
  applyFilter();
}

async function load() {
  try {
    const response = await fetch('/api/tablero', { cache: 'no-store' });
    if (!response.ok) throw new Error('HTTP ' + response.status);
    render(await response.json());
    errorBox.hidden = true;
  } catch (error) {
    errorBox.hidden = false;
    live.dataset.state = 'off';
  }
}

async function move(id, estado) {
  if (!WRITE) return;
  const response = await fetch('/api/estado', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, estado }),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    errorBox.hidden = false;
    errorBox.textContent = 'No se pudo mover ' + id + ': ' + (detail.error || response.status);
    return;
  }
  await load();
}

search.addEventListener('input', applyFilter);

const events = new EventSource('/eventos');
events.onopen = () => { live.dataset.state = 'on'; };
events.onerror = () => { live.dataset.state = 'off'; };
events.onmessage = () => { load(); };

load();
</script>
</body>
</html>
"""


class BoardServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request: Any, client_address: Any) -> None:
        """A closed SSE stream is normal: do not print a traceback for it."""
        error = sys.exc_info()[1]
        if isinstance(error, (ConnectionResetError, BrokenPipeError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


def main() -> None:
    global VERSION, WRITE_ENABLED

    parser = argparse.ArgumentParser(description="Tablero kanban en vivo del backlog markdown.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--write", action="store_true", help="permite arrastrar tarjetas y reescribir el markdown"
    )
    parser.add_argument("--open", action="store_true", help="abre el navegador por defecto")
    options = parser.parse_args()

    if not BACKLOG_DIR.exists():
        raise SystemExit(f"No existe {BACKLOG_DIR}")

    WRITE_ENABLED = options.write
    VERSION = Version()

    threading.Thread(target=watch_changes, name="backlog-watch", daemon=True).start()

    server = BoardServer((options.host, options.port), Handler)
    url = f"http://{options.host}:{options.port}"
    mode = "lectura y escritura" if WRITE_ENABLED else "solo lectura"
    print(f"Tablero del backlog ({mode}) en {url}")
    print("Ctrl+C para detener.")

    if options.open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando tablero.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
