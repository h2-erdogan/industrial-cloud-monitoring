from dataclasses import dataclass
import random
import math
from pathlib import Path

@dataclass
class SensorConfig:
    baseline: float
    noise_sigma: float = 0.5
    anomaly_prob: float = 0.01
    anomaly_magnitude: float = 3.0
    drift_prob: float = 0.002

class SensorSimulator:
    """Simulates a sensor producing data with noise, drift, and occasional anomalies."""
    def __init__(self, name: str, config: SensorConfig):
        self.name = name
        self.cfg = config
        self.rng = random.Random()
        self.t = 0
        self.drift = 0.0

    def _maybe_drift(self):
        if self.rng.random() < self.cfg.drift_prob:
            self.drift += self.rng.uniform(-0.05, 0.05)

    def next_value(self) -> float:
        self.t += 1
        self._maybe_drift()

        # baseline + noise
        val = self.cfg.baseline + self.drift + self.rng.gauss(0.0, self.cfg.noise_sigma)

        # ANOMALY INJECTION
        if self.rng.random() < self.cfg.anomaly_prob:
            spike = self.cfg.anomaly_magnitude * self.cfg.noise_sigma
            sign = -1.0 if self.rng.random() < 0.5 else 1.0
            val += sign * spike * self.rng.uniform(1.0, 2.0)  # stronger spike

        # sine variation
        val += 0.3 * math.sin(self.t / 25.0)

        return val


if __name__ == "__main__":
    import argparse
    import csv

    parser = argparse.ArgumentParser(description="Generates random sensor data each run.")
    parser.add_argument("--rows", type=int, default=250)
    parser.add_argument("--out", default="outputs/simulated.csv")
    parser.add_argument("--print", action="store_true")
    args = parser.parse_args()

    # UPDATED CONFIGS (VERY IMPORTANT)

    temp = SensorSimulator(
        "Temperature",
        SensorConfig(
            baseline=60.0,
            noise_sigma=1.0,
            anomaly_prob=0.08,
            anomaly_magnitude=8.0
        )
    )

    press = SensorSimulator(
        "Pressure",
        SensorConfig(
            baseline=5.0,
            noise_sigma=0.3,
            anomaly_prob=0.07,
            anomaly_magnitude=6.0
        )
    )

    vib = SensorSimulator(
        "Vibration",
        SensorConfig(
            baseline=2.0,
            noise_sigma=0.4,
            anomaly_prob=0.07,
            anomaly_magnitude=7.0
        )
    )

    # output path
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["t", "temp", "press", "vib"])

        for t in range(1, args.rows + 1):
            vt = temp.next_value()
            vp = press.next_value()
            vv = vib.next_value()

            writer.writerow([t, f"{vt:.5f}", f"{vp:.5f}", f"{vv:.5f}"])

            if args.print:
                print(f"{t},{vt:.5f},{vp:.5f},{vv:.5f}")

    print(f"Saved {args.rows} rows to {out_path}")