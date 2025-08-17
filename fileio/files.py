from core.types import Doc

class DocValue: 
    def __init__(self, path: str, text: str):
        self.path = path
        self.text = text 
    
def load_doc(path: str):
    with open(path, "r", encoding="utf-8") as f: 
        return Doc, DocValue(path, f.read())