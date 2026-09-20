import json
import math
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HOST = "127.0.0.1"
PORT = 8000
ROOT = Path(__file__).parent


def calculate(formula: str, values: dict[str, Any]) -> tuple[float, str]:
    try:
        numbers = {name: float(value) for name, value in values.items()}
    except (TypeError, ValueError):
        raise ValueError("All inputs must be numbers")

    if not all(math.isfinite(value) for value in numbers.values()):
        raise ValueError("All inputs must be finite numbers")

    if formula == "final-velocity":
        required = ("initialVelocity", "acceleration", "time")
        answer = numbers[required[0]] + numbers[required[1]] * numbers[required[2]]
        return answer, "m/s"

    if formula == "displacement":
        required = ("initialVelocity", "acceleration", "time")
        time = numbers[required[2]]
        answer = numbers[required[0]] * time + 0.5 * numbers[required[1]] * time**2
        return answer, "m"

    if formula == "velocity-squared":
        required = ("initialVelocity", "acceleration", "displacement")
        velocity_squared = numbers[required[0]]**2 + 2 * numbers[required[1]] * numbers[required[2]]
        if velocity_squared < 0:
            raise ValueError("No real velocity for these values")
        return math.sqrt(velocity_squared), "m/s"

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
            answer, unit = calculate(payload["formula"], payload["values"])
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
