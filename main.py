from flask import Flask, jsonify, request, abort
from .model import ServerInfo, Metro
import platform
import util

app = Flask(__name__)

server_info = ServerInfo('localhost', '%s - %s' % (platform.system(), platform.platform()), '127.0.0.1')


@app.route('/metro/api/v1/info', methods=['GET'])
def get_server_info():
    return jsonify(server_info.serialize()), 200


@app.route('/metro/api/v1/metro', methods=['POST'])
def create_metro():
    if not request.json:
        abort(400)


if __name__ == '__main__':
    app.run(debug=True, port=9871)
