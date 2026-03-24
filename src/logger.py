
from dataclasses import dataclass
from pathlib import Path
from typing import List
import pandas as pd

@dataclass
class LoggerConfig:
    # Path to the log file, relative to THIS file unless you pass an absolute path.
    rel_path: str = "../outputs/log.csv"
    # Keep only the latest N rows
    max_rows: int = 250

class DataLogger:
    def __init__(self, cfg: LoggerConfig):
        self.cfg = cfg

        # Resolve final path
        rel = Path(cfg.rel_path)
        if rel.is_absolute():
            self.path = rel
        else:
            self.path = (Path(__file__).parent / rel).resolve()

        # Ensure directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Canonical schema (and order)
        self.columns: List[str] = [
            "t", "temp", "press", "vib",
            "severity",
            "anom_temp", "anom_press", "anom_vib",
        ]

        # Create or normalize existing file
        if not self.path.exists():
            pd.DataFrame(columns=self.columns).to_csv(self.path, index=False)
        else:
            df = self._safe_read()
            df = self._ensure_schema(df)
            self._atomic_write(df)

        # Optional: show exactly where we're writing (debug)
        # print(f"[DataLogger] Writing to: {self.path}")

    # ---------- internals ----------

    def _safe_read(self) -> pd.DataFrame:
        """Read CSV robustly; if empty/corrupt, return empty frame with schema."""
        try:
            df = pd.read_csv(self.path)
        except Exception:
            df = pd.DataFrame(columns=self.columns)
        return df

    def _ensure_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all required columns exist in the right order and types."""
        for col in self.columns:
            if col not in df.columns:
                if col == "severity":
                    df[col] = "OK"
                else:
                    df[col] = 0

        # Drop unexpected columns and fix order
        df = df[self.columns]

        # Best-effort dtype normalization
        int_cols = ["t", "anom_temp", "anom_press", "anom_vib"]
        float_cols = ["temp", "press", "vib"]
        for c in int_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
        for c in float_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
        df["severity"] = df["severity"].astype(str)
        return df

    def _clamp_tail(self, df: pd.DataFrame) -> pd.DataFrame:
        """Keep only the last max_rows rows."""
        max_rows = int(self.cfg.max_rows)
        if len(df) > max_rows:
            return df.iloc[-max_rows:].copy()
        return df

    def _atomic_write(self, df: pd.DataFrame) -> None:
        """Write CSV atomically; fallback to direct write if needed."""
        tmp = self.path.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        try:
            tmp.replace(self.path)
        except Exception:
            # Fallback for filesystems not supporting atomic replace
            df.to_csv(self.path, index=False)
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass

    # ---------- public API ----------

    def log(self,
            t: int,
            temp: float, press: float, vib: float,
            anom_temp: bool, anom_press: bool, anom_vib: bool,
            severity: str = "OK") -> None:
        """
        Append one row and keep only the latest N rows on disk.
        Safe for small N (<= few thousands). Designed for our 250-row cap.
        """
        df = self._safe_read()
        df = self._ensure_schema(df)

        new_row = {
            "t": int(t),
            "temp": float(temp),
            "press": float(press),
            "vib": float(vib),
            "severity": str(severity),
            "anom_temp": int(bool(anom_temp)),
            "anom_press": int(bool(anom_press)),
            "anom_vib": int(bool(anom_vib)),
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df = self._clamp_tail(df)
        self._atomic_write(df)

    def close(self) -> None:
        pass
