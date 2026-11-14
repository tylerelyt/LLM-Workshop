"""Serve the Ollama text routes used by early lessons via the configured chat API."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json

from .deepseek import DeepSeek


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=11435)
    args = parser.parse_args()
    backend = DeepSeek()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            path = self.path
            if path not in ("/api/chat", "/api/generate"):
                self.send_json(404, {"error": "This bridge supports /api/chat and /api/generate."})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 1_000_000:
                    raise ValueError("Invalid request length")
                request = json.loads(self.rfile.read(size))
                if path == "/api/chat":
                    messages = request["messages"]
                else:
                    messages = [{"role": "user", "content": request["prompt"]}]
                answer = backend.complete(messages, thinking=False, max_tokens=2048).content
                if not answer:
                    raise RuntimeError("Empty response")
                # ReAct expects to receive the model text before an Observation
                # so the actual tool can run and supply its own result.
                stop = request.get("options", {}).get("stop") or []
                if isinstance(stop, str):
                    stop = [stop]
                boundaries = [answer.find(marker) for marker in stop if marker and marker in answer]
                if boundaries:
                    answer = answer[:min(boundaries)]
            except (ValueError, KeyError, TypeError):
                self.send_json(400, {"error": "Invalid text request."})
                return
            except Exception as error:
                self.send_json(502, {"error": f"Configured chat model failed: {type(error).__name__}"})
                return

            reply = {"model": request.get("model", backend.model), "done": True, "done_reason": "stop"}
            if path == "/api/chat":
                reply["message"] = {"role": "assistant", "content": answer}
            else:
                reply["response"] = answer
            self.send_json(200, reply, stream=request.get("stream", False))

        def send_json(self, status, reply, *, stream=False):
            body = (json.dumps(reply, ensure_ascii=False) + "\n").encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/x-ndjson" if stream else "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Text bridge for {backend.model} listening on http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
