
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
import math
from typing import Deque, Tuple


@dataclass
class RollingConfig:
    """
    Configuration for the rolling detector.
    - window_size: number of samples kept for rolling mean/std
    - warn_z: z threshold for WARN
    - alert_z: z threshold for ALERT
    """
    window_size: int = 60
    warn_z: float = 2.0
    alert_z: float = 3.0


class RollingStatsDetector:
    """
    Rolling z-score anomaly detector.
    Maintains a moving mean/std using a deque and running sums.
    """
    def __init__(self, cfg: RollingConfig):
        self.cfg = cfg
        self._win: Deque[float] = deque(maxlen=cfg.window_size)
        self._sum = 0.0
        self._sum_sq = 0.0

    # ---------- internal update helpers ----------
    def _pop_left(self):
        """Remove oldest value when deque full, updating sums."""
        if len(self._win) == self._win.maxlen:
            old = self._win[0]
            self._sum -= old
            self._sum_sq -= old * old

    # ---------- core operations ----------
    def update(self, x: float):
        """Insert one new sample and update rolling sums."""
        self._pop_left()
        self._win.append(x)
        self._sum += x
        self._sum_sq += x * x

    def mean_std(self) -> Tuple[float, float]:
        """Return current mean and std for the window."""
        n = len(self._win)
        if n == 0:
            return 0.0, 0.0
        mean = self._sum / n
        var = max(self._sum_sq / n - mean * mean, 0.0)
        std = math.sqrt(var)
        return mean, std

    def zscore(self, x: float) -> float:
        """Compute |z| = |x - mean| / std for the current window."""
        n = len(self._win)
        if n < max(5, int(self.cfg.window_size * 0.5)):
            return 0.0
        mean, std = self.mean_std()
        if std <= 1e-12:
            return 0.0
        return abs((x - mean) / std)

    def classify(self, x: float) -> Tuple[str, float]:
        """Return ('OK'|'WARN'|'ALERT', z) for x (without updating)."""
        z = self.zscore(x)
        if z > self.cfg.alert_z:
            return "ALERT", z
        if z > self.cfg.warn_z:
            return "WARN", z
        return "OK", z

    def is_anomaly(self, x: float) -> bool:
        """Boolean flag for anomaly detection."""
        s, _ = self.classify(x)
        return s != "OK"


__all__ = ["RollingConfig", "RollingStatsDetector"]


# ------------------------------------------------------------
# Standalone test for 3 sensors
# ------------------------------------------------------------
if __name__ == "__main__":
    from simulator import SensorSimulator, SensorConfig

    print(">>> multi-sensor rolling detector test (Temperature, Pressure, Vibration)\n")

    cfg = RollingConfig(window_size=60, warn_z=2.0, alert_z=3.0)

    det_temp  = RollingStatsDetector(cfg)
    det_press = RollingStatsDetector(cfg)
    det_vib   = RollingStatsDetector(cfg)

    sim_temp = SensorSimulator("temperature", SensorConfig(baseline=60.0, noise_sigma=0.6, anomaly_prob=0.03, anomaly_magnitude=5.0))
    sim_press = SensorSimulator("pressure", SensorConfig(baseline=5.0, noise_sigma=0.10, anomaly_prob=0.02, anomaly_magnitude=4.0))
    sim_vib = SensorSimulator("vibration", SensorConfig(baseline=2.0, noise_sigma=0.15, anomaly_prob=0.02, anomaly_magnitude=6.0))

    anomalies = 0

    for t in range(1, 301):
        # generate readings
        vt = sim_temp.next_value()
        vp = sim_press.next_value()
        vv = sim_vib.next_value()

        # classify (based on history)
        st, zt = det_temp.classify(vt)
        sp, zp = det_press.classify(vp)
        sv, zv = det_vib.classify(vv)

        # update after classification
        det_temp.update(vt)
        det_press.update(vp)
        det_vib.update(vv)

        # count if any anomaly
        if any(s != "OK" for s in (st, sp, sv)):
            anomalies += 1
            print(f"t={t:03d}  "
                  f"T={vt:6.2f} ({st:6})  "
                  f"P={vp:5.2f} ({sp:6})  "
                  f"V={vv:5.2f} ({sv:6})  "
                  f"z=(T:{zt:.2f}, P:{zp:.2f}, V:{zv:.2f})")

        elif t % 20 == 0:
            # print occasional non-anomalous lines
            print(f"t={t:03d}  T={vt:6.2f}  P={vp:5.2f}  V={vv:5.2f}  (OK)")

    print(f"\nTotal anomaly frames (any WARN/ALERT): {anomalies}")
