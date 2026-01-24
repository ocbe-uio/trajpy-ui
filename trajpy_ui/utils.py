import socket


def find_free_port(start_port=8080):
    """Find a free port starting from the given port."""
    port = start_port
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            port += 1
    raise RuntimeError("No free ports available")
