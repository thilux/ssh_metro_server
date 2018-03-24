import socket


def get_free_port():
    """
    Fakely starts a socket server to obtain a port auto assigned by the operating system. The socket is immediately
    closed and the port used for the server is then returned.

    :return: The free port number.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def is_server_alive(host, port):
    """
    Attempts to connect to a given host and port. If the connection is successful then True is returned. Otherwise,
    False is returned.

    :param host: the target host name or ip address.
    :param port: the target port.
    :return: True if the connection to the provided host and port is successful. False if the connection is refused.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        s.shutdown(2)
        return True
    except ConnectionRefusedError:
        return False
