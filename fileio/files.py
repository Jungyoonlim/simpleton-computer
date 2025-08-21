from dataclasses import dataclass
from typing import List as PyList, Union, Optional
import re

# --- Doc container ---
@dataclass(frozen=True)
class DocValue:
    path: str
    text: str

def load_doc(path: str):
    from core.typesys.types import Doc  # avoid circulars
    with open(path, "r", encoding="utf-8") as f:
        return Doc, DocValue(path, f.read())

# --- Domain values ---
@dataclass(frozen=True)
class CommentValue:
    author: str
    date: str   # ISO YYYY-MM-DD
    text: str
    source_path: str
    def __str__(self): return f"[{self.author}|{self.date}] {self.text}"

@dataclass(frozen=True)
class TaskValue: 
    id: str
    status: str  # "open"|"done"|"blocked"|...
    text: str
    source_path: str
    def __str__(self): return f"[{self.id}|{self.status:<7}] {self.text}"

@dataclass(frozen=True)
class LinkValue:
    url: str
    title: Optional[str]
    source_path: str
    def __str__(self): return f"[link|{self.url}] {self.title or ''}".rstrip()


DocAny = Union[CommentValue, TaskValue, LinkValue]

# --- Regexes ---
TAG_RE     = re.compile(r"^\s*(?P<tag>\w+)\s+(?P<body>.+)$")
COMMENT_RE = re.compile(r"^\s*\[(?P<author>[^|\]]+)\|(?P<date>\d{4}-\d{2}-\d{2})\]\s*(?P<text>.+)$")

TASK_RE = re.compile(
    r"^\s*\[(?P<id>[^\]|]+)\|(?P<status>[^\]]+)\]\s*(?P<text>.+)$"
)
LINK_RE = re.compile(
    r"^\s*\[(?P<url>https?://[^\]\s]+)\]\s*(?P<title>\".*?\"|.+)?\s*$"
)

def parse_comments(doc: DocValue) -> PyList[CommentValue]:
    out: PyList[CommentValue] = []
    for line in doc.text.splitlines():
        m = COMMENT_RE.match(line)
        if m:
            out.append(CommentValue(
                author=m.group("author").strip(),
                date=m.group("date"),
                text=m.group("text").strip(),
                source_path=doc.path
            ))
    return out

# ----- Parsers per tag -----
def parse_comment(body: str, path: str) -> Optional[CommentValue]:
    m = COMMENT_RE.match(body)
    if not m: return None
    return CommentValue(
        author=m.group("author").strip(),
        date=m.group("date"),
        text=m.group("text").strip(),
        source_path=path
    )

def parse_task(body: str, path: str) -> Optional[TaskValue]:
    m = TASK_RE.match(body)
    if not m: return None
    return TaskValue(
        id=m.group("id").strip(),
        status=m.group("status").strip(),
        text=m.group("text").strip(),
        source_path=path
    )

def parse_link(body: str, path: str) -> Optional[LinkValue]:
    m = LINK_RE.match(body)
    if not m: return None
    title = m.group("title")
    if title:
        title = title.strip()
        if title.startswith('"') and title.endswith('"'):
            title = title[1:-1]
    return LinkValue(url=m.group("url"), title=title, source_path=path)

PARSERS = {
    "comment": parse_comment,
    "task": parse_task,
    "link": parse_link,
}

# ----- Unified loader -----
def load_mixed(path: str) -> PyList[DocAny]:
    out: PyList[DocAny] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f.read().splitlines():
            if not raw.strip(): 
                continue
            tagm = TAG_RE.match(raw)
            if not tagm: 
                continue  # or collect errors
            tag = tagm.group("tag").lower()
            body = tagm.group("body")
            parser = PARSERS.get(tag)
            if not parser: 
                continue
            val = parser(body, path)
            if val:
                out.append(val)
    return out

# ----- Pretty list helper -----
def print_list(values: PyList[DocAny]) -> None:
    for v in values:
        print(str(v))