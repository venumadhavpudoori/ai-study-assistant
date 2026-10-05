import os
from pathlib import Path

class PromptService:
    def __init__(self, prompts_dir: str | None = None):
        if prompts_dir:
            self.prompts_dir = Path(prompts_dir)
        else:
            self.prompts_dir = Path(__file__).resolve().parent.parent.parent / "prompts"

    def get_prompt(self, filename: str) -> str:
        path = self.prompts_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Prompt file {filename} not found")
        return path.read_text(encoding="utf-8").strip()

prompt_service = PromptService()
