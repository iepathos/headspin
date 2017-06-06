#!/usr/bin/env python
# check nginx_conf directory and send get request
# to every service listening there
# verify service responds with 200 OK
import os
import requests


def check_port(port):
    url = 'http://127.0.0.1:{}'.format(port)
    r = requests.get(url)
    if r.status_code == 200:
        return True
    return False


success = []
failed = []
for filename in os.listdir('nginx_conf'):
    file = open('nginx_conf/' + filename, 'r')
    for line in file.readlines():
        lsplit = line.strip('').split(' ')
        if 'listen' in lsplit:
            port = lsplit[lsplit.index('listen') + 1].replace(';', '').strip()
            if check_port(port):
                success.append(port)
                print('Port %s checks out' % port)
            else:
                failed.append(port)
                print('Port %s did not return 200 ok' % port)


print('{} ports connected ok'.format(len(success)))
print('{} ports did not return 200 ok'.format(len(failed)))
