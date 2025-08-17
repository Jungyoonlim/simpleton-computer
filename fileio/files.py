from dataclasses import dataclass
from core.types import Doc
from typing import List as PyList, Tuple
import re, time, os 

class DocValue: 
    def __init__(self, path: str, text: str):
        self.path = path
        self.text = text 
    
def load_doc(path: str):
    with open(path, "r", encoding="utf-8") as f: 
        return Doc, DocValue(path, f.read())
    
@dataclass
class CommentValue:
    author: str
    date: str   # ISO YYYY-MM-DD
    text: str
    source_path: str

_COMMENT_RE = re.compile(r"^\s*\[(?P<author>[^|\]]+)\|(?P<date>\d{4}-\d{2}-\d{2})\]\s*(?P<text>.+)$")

def parse_comments(doc: DocValue) -> PyList[CommentValue]:
    out: PyList[CommentValue] = []
    for line in doc.text.splitlines():
        m = _COMMENT_RE.match(line)
        if m:
            out.append(CommentValue(
                author=m.group("author").strip(),
                date=m.group("date"),
                text=m.group("text").strip(),
                source_path=doc.path
            ))
    return out