"""Configuration from the environment (and an optional .env file in the repo root).

Two OpenAI-compatible endpoints, generator and falsifier, so the falsifier is never the model
grading its own output. Keys come only from the environment and are never logged.
"""
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Minimal .env reader: KEY=VALUE lines, # comments; the real environment wins."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Endpoint:
    role: str
    base_url: str
    model: str
    api_key: str | None
    # Qwen accepts chat_template_kwargs.enable_thinking; Gemma and most hosted models reject the key.
    thinking_param: bool
    timeout_s: float

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.model)

    def __repr__(self) -> str:  # never print the key
        return f"Endpoint(role={self.role!r}, base_url={self.base_url!r}, model={self.model!r}, key={'set' if self.api_key else 'none'})"


def endpoint(role: str) -> Endpoint:
    p = role.upper()
    base = os.getenv(f"{p}_BASE_URL", "").rstrip("/")
    key = os.getenv(f"{p}_API_KEY") or None
    tf_base = os.getenv("TOKENFACTORY_BASE_URL", "").rstrip("/")
    if key is None and tf_base and base.startswith(tf_base):
        key = os.getenv("TOKENFACTORY_API_KEY") or None
    return Endpoint(
        role=role,
        base_url=base,
        model=os.getenv(f"{p}_MODEL", ""),
        api_key=key,
        thinking_param=os.getenv(f"{p}_THINKING_PARAM", "false").lower() == "true",
        timeout_s=float(os.getenv(f"{p}_TIMEOUT_S", "180")),
    )


@dataclass(frozen=True)
class Settings:
    mode: str  # "public" (tokenfactory) or "local" (Somnus box)
    generator: Endpoint
    falsifier: Endpoint


def settings() -> Settings:
    load_dotenv()
    return Settings(
        mode=os.getenv("AP_MODE", "public"),
        generator=endpoint("generator"),
        falsifier=endpoint("falsifier"),
    )
