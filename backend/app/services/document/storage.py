import os
from pathlib import Path
from app.core.config import settings

class Storage:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_content: bytes, filename: str) -> str:
        file_path = self.upload_dir / filename
        with open(file_path, "wb") as f:
            f.write(file_content)
        return str(file_path.absolute())

    def get_path(self, filename: str) -> str:
        return str((self.upload_dir / filename).absolute())

    def delete_file(self, filename: str) -> None:
        file_path = self.upload_dir / filename
        if file_path.exists():
            file_path.unlink()

# Singleton instance
storage = Storage()
