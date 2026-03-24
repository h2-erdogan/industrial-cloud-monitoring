from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from textwrap import dedent

ROOT = Path(__file__).parent
CSV_PATH = ROOT.joinpath("../outputs/log.csv").resolve()
OUT_DIR = ROOT.joinpath("../outputs").resolve()

REQ_MIN_COLS = ["t", "temp", "press", "vib", "anom_temp", "anom_press", "anom_vib"]  # minimal set

def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    df = pd.read_csv(path)
    for c in REQ_MIN_COLS:
        if c not in df.columns:
            raise ValueError(f"Missing column in CSV: {c}")
    # Cast types
    df["t"] = pd.to_numeric(df["t"], errors="coerce").astype("Int64")
    for c in ["temp","press","vib"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["anom_temp","anom_press","anom_vib"]:
        df[c] = (pd.to_numeric(df[c], errors="coerce") > 0).astype(int)
    # Optional severity
    if "severity" in df.columns:
        df["severity"] = df["severity"].astype(str)
    else:
        df["severity"] = "OK"
    return df

def summary_stats(df: pd.DataFrame) -> dict:
    n = len(df)
    res = {
        "rows": n,
        "temp_mean": df["temp"].mean(),
        "temp_std": df["temp"].std(ddof=1),
        "press_mean": df["press"].mean(),
        "press_std": df["press"].std(ddof=1),
        "vib_mean": df["vib"].mean(),
        "vib_std": df["vib"].std(ddof=1),
        "anom_temp": int(df["anom_temp"].sum()),
        "anom_press": int(df["anom_press"].sum()),
        "anom_vib": int(df["anom_vib"].sum()),
    }
    res["rate_temp"]  = 100.0 * res["anom_temp"]  / n
    res["rate_press"] = 100.0 * res["anom_press"] / n
    res["rate_vib"]   = 100.0 * res["anom_vib"]   / n
    # Severity counts
    res["sev_counts"] = df["severity"].value_counts().to_dict()
    return res

def plot_series(df: pd.DataFrame, col: str, anom_col: str, title: str, fname: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(9, 3))
    ax = fig.add_subplot(111)
    ax.plot(df["t"], df[col], lw=1.5, label=col)
    mask = df[anom_col] == 1
    ax.scatter(df.loc[mask, "t"], df.loc[mask, col], s=36, label="anomaly")
    ax.set_title(title)
    ax.set_xlabel("t"); ax.set_ylabel("value")
    ax.grid(True, alpha=0.3); ax.legend(loc="best")
    fig.tight_layout()
    out_path = OUT_DIR / fname
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path.name

def write_markdown(stats: dict, files: list[str]):
    sev_line = ", ".join(f"{k}: {v}" for k, v in stats["sev_counts"].items())
    md = dedent(f"""
    # Smart Industrial Sensor – Log Summary

    **Total ticks:** {stats['rows']}

    ## Sensor Statistics (mean ± std)
    - Temperature: {stats['temp_mean']:.3f} ± {stats['temp_std']:.3f}
    - Pressure: {stats['press_mean']:.3f} ± {stats['press_std']:.3f}
    - Vibration: {stats['vib_mean']:.3f} ± {stats['vib_std']:.3f}

    ## Detected Anomalies
    - Temperature: {stats['anom_temp']}  ({stats['rate_temp']:.2f}%)
    - Pressure:    {stats['anom_press']} ({stats['rate_press']:.2f}%)
    - Vibration:   {stats['anom_vib']}   ({stats['rate_vib']:.2f}%)

    ## Severity Counts
    - {sev_line if sev_line else "n/a"}

    ## Figures
    {chr(10).join(f"- {fn}" for fn in files)}
    """).strip() + "\n"
    md_path = OUT_DIR / "summary.md"
    md_path.write_text(md, encoding="utf-8")
    return md_path.name

def main():
    print(f"Reading: {CSV_PATH}")
    df = load_data(CSV_PATH)
    stats = summary_stats(df)

    print("\n=== SUMMARY ===")
    print(f"Rows: {stats['rows']}")
    print(f"Temp mean±std   : {stats['temp_mean']:.3f} ± {stats['temp_std']:.3f}")
    print(f"Press mean±std  : {stats['press_mean']:.3f} ± {stats['press_std']:.3f}")
    print(f"Vib mean±std    : {stats['vib_mean']:.3f} ± {stats['vib_std']:.3f}")
    print(f"Anomalies (temp, press, vib): {stats['anom_temp']}, {stats['anom_press']}, {stats['anom_vib']}")
    print(f"Rates (%)       : {stats['rate_temp']:.2f}, {stats['rate_press']:.2f}, {stats['rate_vib']:.2f}")
    print(f"Severity counts : {stats['sev_counts']}")

    f1 = plot_series(df, "temp",  "anom_temp",  "Temperature (°C)",    "fig_temp.png")
    f2 = plot_series(df, "press", "anom_press", "Pressure (bar)",      "fig_press.png")
    f3 = plot_series(df, "vib",   "anom_vib",   "Vibration (mm/s RMS)","fig_vib.png")

    md = write_markdown(stats, [f1, f2, f3])

    print("\nArtifacts saved to ../outputs/")
    print(f"- {f1}\n- {f2}\n- {f3}\n- {md}")

if __name__ == "__main__":
    main()