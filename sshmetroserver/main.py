from flask import Flask, jsonify, request, abort
from sshmetroserver.model import ServerInfo, Metro
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

__ports_in_use = list()
__live_metros = dict()

parser = argparse.ArgumentParser()

parser.add_argument('--port', type=int, default=9871, help='The port number in which the server is to be started on the'
                                                           ' local machine')


def signal_handler(signum, frame):

    logger.info('Metro Server received signal %s' % signum)
    logger.info('Terminating Metro Server')
    if __live_metros:
        for metro in __live_metros:
            logger.debug('Terminating tunnel for server => %s' % metro)
            __live_metros[metro]['pexpobj'].kill(9)
            __live_metros[metro]['pexpobj'].close(force=True)
    logger.info('Metro Server terminated!')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


@app.route('/api/v1/info', methods=['GET'])
def get_server_info():
    logger.info('Into GET server info')
    return jsonify(server_info.get_dict()), 200


@app.route('/api/v1/metro', methods=['POST'])
def create_metro():
    if not request.json:
        logger.error('Invalid request to POST metro')
        abort(400)

    metro = Metro.get_instance_from_json(request.json)

    logger.debug('Request for metro => %s' % str(metro.get_dict()))

    if '%s:%d' % (metro.original_host, metro.original_port) in  __live_metros:
        logger.debug('Metro for host [%s] and port [%d] already exists' % (metro.original_host, metro.original_port))
        # reuse existing metro
        existing_metro = __live_metros['%s:%d' % (metro.original_host, metro.original_port)]['metro']
        metro.metro_host = existing_metro.metro_host
        metro.metro_port = existing_metro.metro_port
    else:
        metro.metro_host = request.host.split(':')[0]
        port = util.get_free_port()
        __ports_in_use.append(port)
        metro.metro_port = port
        create_ssh_tunnel_child_process(metro)

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
    logger.debug('Command for starting metro SSH tunnel => %s' % ssh_command)
    child = pexpect.spawn(ssh_command)
    logger.info('SSH command response => %s' % child.before)
    index = child.expect(['Are you sure you want to continue connecting', 'password:'], timeout=120)
    if index == 0:
        logger.info('SSH command response => %s' % child.before)
        child.sendline('yes')
        logger.info('SSH command response => %s' % child.before)
        child.expect('password:')
    time.sleep(0.1)
    child.sendline(metro.password)
    # time.sleep(60)
    child.expect(pexpect.EOF)

    logger.info('SSH command response => %s' % child.before)

    live_metros_key = '%s:%d' % (metro.original_host, metro.original_port)

    if live_metros_key not in __live_metros:
        logger.debug('Creating live_metros entry from scratch')
        __live_metros[live_metros_key] = dict()
        __live_metros[live_metros_key]['metro'] = metro

    __live_metros[live_metros_key]['pexpobj'] = child


def main():
    args = parser.parse_args()
    app.run(debug=True, port=args.port, host='0.0.0.0')
    logger.info('Metro Server started!')


if __name__ == '__main__':
    main()
