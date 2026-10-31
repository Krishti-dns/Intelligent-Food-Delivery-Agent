"""Start the local browser dashboard for the AI project."""

import os
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main() -> None:
    project_folder = Path(__file__).resolve().parent
    os.chdir(project_folder)

    server = None
    port = None
    for candidate in range(8000, 8010):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), SimpleHTTPRequestHandler)
            port = candidate
            break
        except OSError:
            continue

    if server is None or port is None:
        raise SystemExit("Ports 8000 through 8009 are busy. Close another local server and try again.")

    address = "http://127.0.0.1:{}".format(port)
    print("Intelligent Food Delivery Agent is running at {}".format(address))
    print("Keep this terminal open. Press Control+C here to stop the local server.")
    webbrowser.open(address)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nLocal server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
