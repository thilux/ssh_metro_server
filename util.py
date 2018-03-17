import socket


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind('', 0)
    port = s.getsockname()[1]
    s.close()
    return port