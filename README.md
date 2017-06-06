# HeadSpin Devops

Uses docker and docker-compose to test locally for nginx container. [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)  Generated configs and pages can easily be used with a standard host nginx install as well.

Setup in a Python 3 environment.  Tested with Python 3.6.0.

````shell
pip install -r requirements.txt
````

Solution

````shell
./do_everything.sh data.yml
````

If configs are adjusted, do `docker exec nginx nginx -s reload` to reload nginx.

`docker stop nginx` to bring down the nginx docker container.

+ spinit.py - generates nginx config and pages given a config yaml

+ tests.py - Looks through the generated nginx configs and checks that the expected ports return 200 OK to get requests.

+ do_everything.sh - does everything. Cleans up any existing configs or content before running spinit, docker-compose, and tests.