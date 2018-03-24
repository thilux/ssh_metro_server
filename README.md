## SSH metro server

The SSH metro application is an application that allows initiating SSH tunnels dynamically on a remote/server machine and automatically connecting to them.

SSH metro server is the server side application that servers requests from the clients and initiate the required tunnels for the clients to connect on.

### Technology

SSH metro server uses the following frameworks/libraries for the specified purposes:

* Flask: HTTP server implementation to handle requests from clients
* Pexpect: To handle operating system level commands to start the SSH tunnels

### Installation

To install SSH metro server, just run the following command on your server machine:

```
$> pip install ssh-metro-server
```

or

```
$> pipenv install ssh-metro-server
```


### Running

To start SSH metro server on your server machine, simply run:

```
$> ssh_metro_server
```

That command will start SSH metro server on its default port 9871. If you want it to run on an specific port though, just run:

```
$> ssh_metro_server -port {PORT}
```

That way, SSH metro server will start on the port specified by {PORT} :)


### Developers

Currently, this project is maintained and developed by:

* thilux (Thiago Santana)

Contributions are expected and more than welcome. If you have ideas to enhance the solution, please raise and issue and specify your request. The same is required if you simply want to report bugs. If you want to contribute with code, fork the project and submit a pull request and it will be surely reviewed and happily accepted.

### License

Copyright 2018 Thiago Santana (thilux).

Licensed to the Apache Software Foundation (ASF) under one or more contributor license agreements. See the NOTICE file distributed with this work for additional information regarding copyright ownership. The ASF licenses this file to you under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.