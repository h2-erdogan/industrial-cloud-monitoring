import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
from pathlib import Path
from datetime import datetime
import time
import numpy as np

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from simulator import SensorSimulator, SensorConfig
from detector import RollingStatsDetector, RollingConfig
from logger import DataLogger, LoggerConfig
from configio import load_config, save_config, UIConfig


# ---------------- Plot Panel ----------------

class SensorPanel:
    """A single sensor chart with a live line and a persistent anomaly scatter."""
    def __init__(self, parent, title: str, max_points: int = 250):
        # Keep only the latest max_points values
        self.title = title
        self.max_points = max_points

        self.xdata = deque(maxlen=max_points)
        self.ydata = deque(maxlen=max_points)

        self.fig = Figure(figsize=(6, 2.2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(title)
        self.ax.set_xlabel("t")
        self.ax.set_ylabel("value")
        self.ax.grid(True, alpha=0.3)

        (self.line,) = self.ax.plot([], [], lw=1.5)

        # anomaly scatter stores (t, value) pairs
        self.anom_points = deque(maxlen=max_points)
        self.anom_scatter = self.ax.scatter([], [], s=36)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _offsets_array(self) -> np.ndarray:
        """Return Nx2 array for scatter offsets (safe for empty list)."""
        if not self.anom_points:
            return np.empty((0, 2), dtype=float)
        arr = np.asarray(self.anom_points, dtype=float)
        return arr.reshape(-1, 2)

    def update(self, t: int, value: float, is_anomaly: bool):
        """Append one point and refresh the axes."""
        self.xdata.append(t)
        self.ydata.append(value)
        self.line.set_data(self.xdata, self.ydata)

        if is_anomaly:
            self.anom_points.append((t, value))
        self.anom_scatter.set_offsets(self._offsets_array())

        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

    def clear(self):
        """Clear buffers and redraw empty axes."""
        self.xdata.clear()
        self.ydata.clear()
        self.line.set_data([], [])
        self.anom_points.clear()
        self.anom_scatter.set_offsets(np.empty((0, 2), dtype=float))
        self.canvas.draw_idle()


# ---------------- Main Dashboard ----------------

class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Industrial Sensor – Anomaly Dashboard")
        self.geometry("1000x940")

        ui_cfg = load_config()

        # --- Controls bar ---
        ctrl = ttk.Frame(self)
        ctrl.pack(side="top", fill="x", padx=10, pady=6)

        ttk.Label(ctrl, text="Window Size").pack(side="left")
        self.window_var = tk.IntVar(value=ui_cfg.window_size)
        ttk.Spinbox(ctrl, from_=10, to=500, textvariable=self.window_var, width=6).pack(side="left", padx=6)

        # Keep legacy k-sigma control but disable it, since thresholds are fixed at 2/3 now.
        ttk.Label(ctrl, text="z-thresholds (fixed: 2/3)").pack(side="left", padx=(12, 0))
        self.ksigma_var = tk.DoubleVar(value=getattr(ui_cfg, "k_sigma", 3.0))
        spin = ttk.Spinbox(ctrl, from_=1.0, to=6.0, increment=0.5, textvariable=self.ksigma_var, width=6, state="disabled")
        spin.pack(side="left", padx=6)

        # --- Status bar (color-coded) ---
        self.status_var = tk.StringVar(value="Status: OK")
        self.status_label = tk.Label(self, textvariable=self.status_var, relief="sunken",
                                     anchor="w", bg="#c7f5c4")
        self.status_label.pack(fill="x", padx=10, pady=(4, 2))

        # Small gray hint explaining two-sided z-score
        self.hint_var = tk.StringVar(
            value="Note: two-sided z; both high and low readings can trigger WARN/ALERT (|z|>2/3)."
        )
        self.hint_label = tk.Label(self, textvariable=self.hint_var, anchor="w", fg="#666666")
        self.hint_label.pack(fill="x", padx=10, pady=(0, 6))

        # --- Panels (each keeps only last 250 points) ---
        body = ttk.Frame(self)
        body.pack(side="top", fill="both", expand=True)

        self.temp_panel = SensorPanel(body, "Temperature (°C)", max_points=250)
        self.press_panel = SensorPanel(body, "Pressure (bar)", max_points=250)
        self.vib_panel  = SensorPanel(body, "Vibration (mm/s RMS)", max_points=250)

        # --- Simulators ---
        self.sim_temp = SensorSimulator(
            "temperature",
            SensorConfig(baseline=60.0, noise_sigma=0.6, anomaly_prob=0.015, anomaly_magnitude=5.0),
        )
        self.sim_press = SensorSimulator(
            "pressure",
            SensorConfig(baseline=5.0, noise_sigma=0.10, anomaly_prob=0.015, anomaly_magnitude=4.0),
        )
        self.sim_vib = SensorSimulator(
            "vibration",
            SensorConfig(baseline=2.0, noise_sigma=0.15, anomaly_prob=0.015, anomaly_magnitude=6.0),
        )

        # --- Detectors (rolling mean/std with fixed warn/alert thresholds) ---
        base_cfg = RollingConfig(
            window_size=self.window_var.get(),
            warn_z=2.0,
            alert_z=3.0
        )
        self.det_temp = RollingStatsDetector(base_cfg)
        self.det_press = RollingStatsDetector(base_cfg)
        self.det_vib  = RollingStatsDetector(base_cfg)

        # --- Logger: keeps ONLY last 250 rows on disk ---
        self.logger = DataLogger(LoggerConfig(rel_path="../outputs/log.csv", max_rows=250))

        # --- Runtime state ---
        self.t = 0
        self.running = True
        self._last_beep_ts = 0.0

        # --- Bottom buttons ---
        btns = ttk.Frame(self)
        btns.pack(side="bottom", fill="x", padx=10, pady=8)

        ttk.Button(btns, text="Pause",   command=self.pause).pack(side="left")
        ttk.Button(btns, text="Resume",  command=self.resume).pack(side="left", padx=6)
        ttk.Button(btns, text="Reset",   command=self.reset).pack(side="left", padx=6)
        ttk.Button(btns, text="Snapshot", command=self.save_snapshot).pack(side="left", padx=6)

        ttk.Button(btns, text="Save Config", command=self.save_ui_config).pack(side="right")
        ttk.Button(btns, text="Load Config", command=self.load_ui_config).pack(side="right", padx=6)

        # Start ticking
        self.after(80, self._tick)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -------- Helpers --------

    def update_status(self, message: str, level: str = "OK"):
        """Set text and background color by severity."""
        self.status_var.set(message)
        if level == "OK":
            self.status_label.config(bg="#c7f5c4")   # green
        elif level == "WARN":
            self.status_label.config(bg="#fff3b0")   # yellow
        elif level == "ALERT":
            self.status_label.config(bg="#ffb3b3")   # red
        else:
            self.status_label.config(bg="#f0f0f0")   # gray

    def _z_from_series(self, value: float, series: deque, window: int) -> float:
        """Two-sided z-score relative to the last `window` values from `series`."""
        if not series:
            return 0.0
        arr = np.asarray(list(series)[-window:], dtype=float)
        mu = arr.mean()
        sd = arr.std(ddof=1) if arr.size > 1 else 0.0
        if sd <= 1e-12:
            return 0.0
        return float(abs(value - mu) / sd)

    # -------- Controls --------

    def pause(self):
        self.running = False
        self.update_status("Status: PAUSED", "WARN")

    def resume(self):
        self.running = True
        self.update_status("Status: OK", "OK")

    def reset(self):
        """Reset detectors and plots. Thresholds remain fixed at 2/3."""
        cfg = RollingConfig(
            window_size=int(self.window_var.get()),
            warn_z=2.0,
            alert_z=3.0
        )
        self.det_temp = RollingStatsDetector(cfg)
        self.det_press = RollingStatsDetector(cfg)
        self.det_vib  = RollingStatsDetector(cfg)

        for p in (self.temp_panel, self.press_panel, self.vib_panel):
            p.clear()

        self.t = 0
        self.update_status("Status: OK", "OK")

    def save_snapshot(self):
        out_dir = Path(__file__).parent.joinpath("../outputs").resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        panels = [
            ("temperature", self.temp_panel),
            ("pressure", self.press_panel),
            ("vibration", self.vib_panel),
        ]
        names = []
        for name, panel in panels:
            path = out_dir / f"{stamp}_{name}.png"
            panel.fig.savefig(path, dpi=150, bbox_inches="tight")
            names.append(path.name)

        self.update_status(f"Saved: {', '.join(names)}", "OK")

    def save_ui_config(self):
        """Persist only the window size (k_sigma kept for backward compatibility)."""
        try:
            cfg = UIConfig(
                window_size=int(self.window_var.get()),
                k_sigma=float(self.ksigma_var.get())  # ignored by detector; kept for compatibility
            )
            save_config(cfg)
            self.update_status("Config saved to outputs/config.json", "OK")
        except Exception as e:
            messagebox.showerror("Save Config", f"Could not save config:\n{e}")

    def load_ui_config(self):
        """Load window size (and legacy k_sigma if present)."""
        try:
            cfg = load_config()
            self.window_var.set(int(cfg.window_size))
            # keep UI in sync even if detector ignores it
            if hasattr(cfg, "k_sigma"):
                self.ksigma_var.set(float(cfg.k_sigma))
            self.update_status("Config loaded from outputs/config.json", "OK")
        except Exception as e:
            messagebox.showerror("Load Config", f"Could not load config:\n{e}")

    # -------- Main tick --------

    def _tick(self):
        try:
            # Live-update only the window size; warn/alert thresholds are fixed (2/3).
            new_cfg = RollingConfig(
                window_size=int(self.window_var.get()),
                warn_z=2.0,
                alert_z=3.0
            )
            self.det_temp.cfg = new_cfg
            self.det_press.cfg = new_cfg
            self.det_vib.cfg   = new_cfg

            if self.running:
                self.t += 1

                # 1) simulate new readings
                vt = self.sim_temp.next_value()
                vp = self.sim_press.next_value()
                vv = self.sim_vib.next_value()

                # 2) anomaly check (pre-update)
                anom_t = self.det_temp.is_anomaly(vt)
                anom_p = self.det_press.is_anomaly(vp)
                anom_v = self.det_vib.is_anomaly(vv)

                # 3) update rolling windows
                self.det_temp.update(vt)
                self.det_press.update(vp)
                self.det_vib.update(vv)

                # 4) update GUI panels (they keep only last 250 points)
                self.temp_panel.update(self.t, vt, anom_t)
                self.press_panel.update(self.t, vp, anom_p)
                self.vib_panel.update(self.t, vv, anom_v)

                # 5) compute severity by max z across series (two-sided)
                N = int(self.window_var.get())
                zt = self._z_from_series(vt, self.temp_panel.ydata, N)
                zp = self._z_from_series(vp, self.press_panel.ydata, N)
                zv = self._z_from_series(vv, self.vib_panel.ydata, N)
                zmax = max(zt, zp, zv)

                if zmax > 3.0:
                    severity = "ALERT"
                elif zmax > 2.0:
                    severity = "WARN"
                else:
                    severity = "OK"

                # 6) status + optional beep
                if severity in ("WARN", "ALERT"):
                    self.update_status(
                        f"Status: {severity} (z: T={zt:.2f}, P={zp:.2f}, V={zv:.2f})",
                        severity
                    )
                    now = time.time()
                    if now - self._last_beep_ts > 0.5:
                        try:
                            self.bell()  # cross-platform UI beep
                        except Exception:
                            pass
                        self._last_beep_ts = now
                else:
                    self.update_status("Status: OK", "OK")

                # 7) log to CSV (logger itself keeps ONLY last 250 rows on disk)
                self.logger.log(
                    self.t, vt, vp, vv,
                    anom_t, anom_p, anom_v,
                    severity=severity
                )

        finally:
            # Schedule next tick
            self.after(80, self._tick)

    # -------- Close --------

    def _on_close(self):
        try:
            if hasattr(self, "logger") and self.logger:
                self.logger.close()
        finally:
            self.destroy()


if __name__ == "__main__":
    app = Dashboard()
    app.mainloop()
