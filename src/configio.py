from pathlib import Path
import json
from dataclasses import dataclass, asdict

DEFAULT_PATH = Path(__file__).parent.joinpath("../outputs/config.json").resolve()

@dataclass
class UIConfig:
    window_size: int = 60
    k_sigma: float = 3.0

def load_config(path: Path = DEFAULT_PATH) -> UIConfig:
    """Load UIConfig from JSON if it exists, else defaults."""
    if not path.exists():
        return UIConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    # tolerate missing keys
    return UIConfig(
        window_size=int(data.get("window_size", 60)),
        k_sigma=float(data.get("k_sigma", 3.0)),
    )

def save_config(cfg: UIConfig, path: Path = DEFAULT_PATH) -> None:
    """Save UIConfig to JSON (pretty)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")