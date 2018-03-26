from flask import Flask, jsonify, request, abort, make_response
from sshmetroserver.model import ServerInfo, Metro
from threading import Thread
import platform
import sshmetroserver.util as util
import pexpect
import logging
import os
import time
import signal
import argparse
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO if 'METRO_DEBUG' not in os.environ else logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console_handler.setFormatter(log_formatter)

logger.addHandler(console_handler)

app = Flask(__name__)

server_info = ServerInfo('localhost', '%s - %s' % (platform.system(), platform.platform()), '127.0.0.1')

_ports_in_use = list()
_live_metros = dict()

parser = argparse.ArgumentParser()

parser.add_argument('--port', type=int, default=9871, help='The port number in which the server is to be started on the'
                                                           ' local machine')


@app.errorhandler(500)
def http_500_handler(error):
    """
    Handles the HTTP 500 status returned by one of the methods in any situation. It returns back to the client, a
    default JSON error structure.

    :param error: The returned error code.
    :return: JSON response to the client
    """
    return make_response(jsonify({'error': 'Failure processing request'}))


def signal_handler(signum, frame):
    """
    A unix signal handler to handle SIGTERM and SIGINT signals received by the application in order to perform a clean
    up and don't leave any child processes up consuming machine resources. A system exit is executed as a result of the
    indicated signals as the assurance all threads and child processes are properly terminated.

    :param signum: the unix signal identifier. See python signal documentation.
    :param frame: See signal documentation.
    """

    logger.info('Metro Server received signal %s' % signum)
    logger.info('Terminating Metro Server')
    if _live_metros:
        for metro in _live_metros:
            logger.debug('Terminating tunnel for server => %s' % metro)
            _live_metros[metro]['pexpobj'].kill(9)
            _live_metros[metro]['pexpobj'].close(force=True)
    logger.info('Metro Server terminated!')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


@app.route('/api/v1/info', methods=['GET'])
def get_server_info():
    """
    Processes the HTTP GET request to return information of the application server serving Metro requests.

    :return: a JSON representation of the server info class. See sshmetroserver.model.ServerInfo for format details.
    """
    logger.info('Into GET server info')
    return jsonify(server_info.get_dict()), 200


@app.route('/api/v1/metro', methods=['POST'])
def create_metro():
    """
    Processes the HTTP POST request to create a new metro. It either creates a new metro instance from scratch or
    returns the information of an already created and live metro instance.

    :return: a JSON representation of the metro instance. See sshmetroserver.model.Metro for format details.
    """
    if not request.json:
        logger.error('Invalid request to POST metro')
        abort(400)

    metro = Metro.get_instance_from_json(request.json)

    logger.debug('Request for metro => %s' % str(metro.get_dict()))

    if '%s:%d' % (metro.original_host, metro.original_port) in _live_metros:
        logger.debug('Metro for host [%s] and port [%d] already exists' % (metro.original_host, metro.original_port))
        # reuse existing metro
        existing_metro = _live_metros['%s:%d' % (metro.original_host, metro.original_port)]['metro']
        metro.metro_host = existing_metro.metro_host
        metro.metro_port = existing_metro.metro_port
    else:
        metro.metro_host = request.host.split(':')[0]
        port = util.get_free_port()
        _ports_in_use.append(port)
        metro.metro_port = port
        try:
            create_ssh_tunnel_child_process(metro)
        except IOError:
            abort(500)

    return jsonify(metro.get_dict()), 201


def create_ssh_tunnel_child_process(metro):
    """
    Creates a SSH tunnel child process using pexpect based on the specification of a metro method. This method
    manipulates the internal live_metros store to either create a new record from scratch or to reuse an existing one if
    one is already specified for the same target host and port.

    :param metro: and instance of a Metro object
    :return: True if the pexpect execution goes well and False if it fails.
    """

    # Create new metro!
    logger.debug('Creating new metro for host [%s] and port [%s]' % (metro.original_host, metro.original_port))
    ssh_command = 'ssh -fNT %s@%s -L %s:%d:%s:%d' % (metro.username, metro.original_host, metro.metro_host,
                                                     metro.metro_port, metro.original_host, metro.original_port)

    if metro.original_port != 22:
        ssh_command += ' -p %d' % metro.original_port

    logger.debug('Command for starting metro SSH tunnel => %s' % ssh_command)
    child = pexpect.spawn(ssh_command)
    logger.info('SSH command response => %s' % child.before)
    index = child.expect(['Are you sure you want to continue connecting', 'password:', 'denied', 'refused', 'timeout'],
                         timeout=120)
    logger.debug('Expect index for SSH command is %d' % index)
    if index > 1:
        # Either 'Permission Denied', 'Connection refused' or 'Connection timeout' happens
        raise IOError('Error while establishing SSH connection to %s:%d' % (metro.original_host, metro.original_port))
    if index == 0:
        logger.info('SSH command response(1) => %s' % child.before)
        child.sendline('yes')
        logger.info('SSH command response(2) => %s' % child.before)
        child.expect('password:')
    time.sleep(0.1)
    child.sendline(metro.password)
    # time.sleep(60)
    child.expect(pexpect.EOF)

    logger.info('SSH command response(3) => %s' % child.before)

    live_metros_key = '%s:%d' % (metro.original_host, metro.original_port)

    if live_metros_key not in _live_metros:
        logger.debug('Creating live_metros entry from scratch')
        _live_metros[live_metros_key] = dict()
        _live_metros[live_metros_key]['metro'] = metro

    _live_metros[live_metros_key]['pexpobj'] = child


def keep_live_metros_alive():
    """
    This method is supposed to be run on a separate thread. It performs an evaluation throughout the list of metros
    stored in the live_metros dictionary to preemptively restart those tunnels that are no longer accessible. Tunnels
    can die by themselves due to policies configured for SSH in the target server, so this method is a way to make sure
    a metro request is always kept while the metro server is running.

    The scan of the live metros list is performed every 1 second.
    """

    while True:
        for live_metros_key in _live_metros:
            metro = _live_metros[live_metros_key]['metro']
            logger.debug('Checking if tunnel for host [%s] and port [%d] is alive' % (metro.original_host,
                                                                                      metro.original_port))
            if not util.is_server_alive(metro.metro_host, metro.metro_port):
                logger.info('Restarting metro for host [%s] and port [%d]' % (metro.original_host, metro.original_port))
                create_ssh_tunnel_child_process(metro)
        time.sleep(1)


def main():
    """
    The main application method.
    """
    args = parser.parse_args()
    keep_alive_thread = Thread(target=keep_live_metros_alive)
    keep_alive_thread.start()
    app.run(debug=True, port=args.port, host='0.0.0.0')
    logger.info('Metro Server started!')


if __name__ == '__main__':
    main()
