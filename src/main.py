import time
from simulator import SensorSimulator, SensorConfig
from detector import RollingStatsDetector, RollingConfig
from logger import DataLogger, LoggerConfig

def run_live_simulation():
    """Run a simple live simulation, print status, and log the last 250 rows."""
    # --- sensors ---
    temp_sensor = SensorSimulator(
        "Temperature",
        SensorConfig(baseline=60.0, noise_sigma=0.6, anomaly_prob=0.02, anomaly_magnitude=5.0),
    )
    pressure_sensor = SensorSimulator(
        "Pressure",
        SensorConfig(baseline=5.0, noise_sigma=0.10, anomaly_prob=0.015, anomaly_magnitude=4.0),
    )
    vib_sensor = SensorSimulator(
        "Vibration",
        SensorConfig(baseline=2.0, noise_sigma=0.15, anomaly_prob=0.015, anomaly_magnitude=6.0),
    )

    # --- detectors (new API: warn_z / alert_z) ---
    det_cfg = RollingConfig(window_size=60, warn_z=2.0, alert_z=3.0)
    temp_det  = RollingStatsDetector(det_cfg)
    press_det = RollingStatsDetector(det_cfg)
    vib_det   = RollingStatsDetector(det_cfg)

    # --- logger (keeps ONLY the last 250 rows on disk) ---
    logger = DataLogger(LoggerConfig(rel_path="../outputs/log.csv", max_rows=250))

    print("Starting live simulation... Press Ctrl+C to stop.\n")
    print(f"{'Time':<6}{'Temp':>10}{'Press':>10}{'Vib':>10}   Status")

    t = 0
    try:
        while True:
            t += 1
            vt = temp_sensor.next_value()
            vp = pressure_sensor.next_value()
            vv = vib_sensor.next_value()

            # classify before updating the rolling window (uses history up to t-1)
            st, zt = temp_det.classify(vt)
            sp, zp = press_det.classify(vp)
            sv, zv = vib_det.classify(vv)

            # update windows
            temp_det.update(vt)
            press_det.update(vp)
            vib_det.update(vv)

            # combined severity by max z across sensors
            max_z = max(zt, zp, zv)
            if max_z > det_cfg.alert_z:
                severity = "ALERT"
            elif max_z > det_cfg.warn_z:
                severity = "WARN"
            else:
                severity = "OK"

            # simple status string + print
            flags = []
            if st != "OK": flags.append("TEMP")
            if sp != "OK": flags.append("PRESS")
            if sv != "OK": flags.append("VIB")
            status = " | ".join(flags) if flags else "OK"
            print(f"{t:<6}{vt:>10.2f}{vp:>10.2f}{vv:>10.2f}   {status}")

            # log (booleans for each sensor + overall severity)
            logger.log(
                t,
                vt, vp, vv,
                int(st != "OK"), int(sp != "OK"), int(sv != "OK"),
                severity=severity,
            )

            time.sleep(0.15)  # readability
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
    finally:
        logger.close()

if __name__ == "__main__":
    run_live_simulation()
