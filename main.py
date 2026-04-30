from simulator.engine import run_simulation
from detection.rules import detect_anomalies
from alerts.manager import build_alerts


def main() -> None:
    samples = run_simulation()
    anomalies = detect_anomalies(samples)
    alerts = build_alerts(anomalies)

    print("Simulation samples:", len(samples))
    print("Anomalies:", len(anomalies))
    print("Alerts:", len(alerts))

    for alert in alerts:
        print(f"[{alert.severity}] {alert.message}")


if __name__ == "__main__":
    main()
