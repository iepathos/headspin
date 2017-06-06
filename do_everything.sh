# this script does everything including
# clearing any configs in nginx_conf and any
# content in nginx_www subfolders to make
# it easy to plug and test any config.
# ${1} the config yaml

# Usage: ./do_everything.sh example.yml

echo 'Bringing down nginx container if running'
docker stop nginx
echo 'Cleaning up any old configs or content'
rm -rf nginx_conf
rm -rf nginx_www
echo 'Generating new configs and content'
./spinit.py ${1}

docker-compose up -d
echo 'Checking services deployed'
./tests.py