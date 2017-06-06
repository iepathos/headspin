# HeadSpin Devops

Uses docker and docker-compose to test locally for nginx container.  Generated configs and pages can easily be used with just a host nginx install as well.

Solution:
````shell
./spinit.py data.yml
docker-compose up -d
./check_services.py
````

or just 

````shell
./do_everything.sh
````

If configs or pages are adjusted, do `docker exec nginx nginx -s reload` to reload nginx.

`docker stop nginx` to bring down the nginx docker container.

+ spinit.py - generates nginx config and pages given a config yaml

+ check_services.py - Looks through the generated nginx configs and checks that the expected ports return 200 OK to get requests.