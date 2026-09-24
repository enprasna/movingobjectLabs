import json
import math
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
ROOT = Path(__file__).parent


def calculate(formula: str, values: dict[str, Any], target: str) -> tuple[float, str]:
    try:
        numbers = {name: float(value) for name, value in values.items()}
    except (TypeError, ValueError):
        raise ValueError("All inputs must be numbers")

    if not all(math.isfinite(value) for value in numbers.values()):
        raise ValueError("All inputs must be finite numbers")

    if formula == "final-velocity":
        u, a, time = numbers.get("initialVelocity"), numbers.get("acceleration"), numbers.get("time")
        if target == "finalVelocity":
            return u + a * time, "m/s"
        if target == "initialVelocity":
            return numbers["finalVelocity"] - a * time, "m/s"
        if target == "acceleration":
            return (numbers["finalVelocity"] - u) / time, "m/s2"
        if target == "time":
            return (numbers["finalVelocity"] - u) / a, "s"

    if formula == "displacement":
        u, a, time = numbers.get("initialVelocity"), numbers.get("acceleration"), numbers.get("time")
        if target == "displacement":
            return u * time + 0.5 * a * time**2, "m"
        if target == "initialVelocity":
            return (numbers["displacement"] - 0.5 * a * time**2) / time, "m/s"
        if target == "acceleration":
            return 2 * (numbers["displacement"] - u * time) / time**2, "m/s2"
        if target == "time":
            if a == 0:
                return numbers["displacement"] / u, "s"
            discriminant = u**2 + 2 * a * numbers["displacement"]
            if discriminant < 0:
                raise ValueError("No real time for these values")
            roots = [(-u + math.sqrt(discriminant)) / a, (-u - math.sqrt(discriminant)) / a]
            valid_roots = [root for root in roots if root >= 0]
            if not valid_roots:
                raise ValueError("No non-negative time for these values")
            return max(valid_roots), "s"

    if formula == "velocity-squared":
        u, a, displacement = numbers.get("initialVelocity"), numbers.get("acceleration"), numbers.get("displacement")
        if target == "finalVelocity":
            velocity_squared = u**2 + 2 * a * displacement
            if velocity_squared < 0:
                raise ValueError("No real velocity for these values")
            return math.sqrt(velocity_squared), "m/s"
        if target == "initialVelocity":
            velocity_squared = numbers["finalVelocity"]**2 - 2 * a * displacement
            if velocity_squared < 0:
                raise ValueError("No real velocity for these values")
            return math.sqrt(velocity_squared), "m/s"
        if target == "acceleration":
            return (numbers["finalVelocity"]**2 - u**2) / (2 * displacement), "m/s2"
        if target == "displacement":
            return (numbers["finalVelocity"]**2 - u**2) / (2 * a), "m"

    raise ValueError("Unknown formula")


class MotionHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self) -> None:
        if self.path != "/api/calculate":
            self.send_error(404, "Endpoint not found")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            answer, unit = calculate(payload["formula"], payload["values"], payload["target"])
            self.send_json(200, {"value": answer, "unit": unit})
        except (KeyError, TypeError, json.JSONDecodeError, ValueError) as error:
            self.send_json(400, {"error": str(error)})

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), MotionHandler)
    print(f"Motion Lab running at http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Motion Lab")
    finally:
        server.server_close()
