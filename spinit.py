#!/usr/bin/env python
import yaml
import os
import argparse
from operator import itemgetter
from itertools import groupby
"""
Generates nginx configs given data.yml

Usage:
    ./spinit.py example.yml

Written By: Glen Baker <iepathos@gmail.com>
"""

parser = argparse.ArgumentParser(description='Generate Nginx Configs from data yaml')
parser.add_argument('data', help='Input data.yml config')
opts = parser.parse_args()

with open(opts.data, 'r') as stream:
    try:
        data = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

ports = data.get('ports')
services = data.get('services')
available_ranges = ports.get('available_ranges')
base_range = int(ports.get('base'))

# shove an int for every port into a list so its easier to deal with
lports = []
for port_range in available_ranges:
    start, end = port_range.split('-')
    lports.extend(list(range(base_range + int(start), base_range + int(end) + 1)))
backup_ports = lports


def find_available_regions(lports):
    # group continuous regions together
    regions = []
    for k, g in groupby(enumerate(lports), lambda ix: ix[0] - ix[1]):
        regions.append(list(map(itemgetter(1), g)))
    return regions


def find_region(regions, chunk):
    # find smallest region of required chunk size
    available_regions = [r for r in regions if len(r) >= chunk]
    if len(available_regions) > 0:
        smallest = len(available_regions[0])
        smallest_idx = 0
        for idx, r in enumerate(available_ranges):
            if len(r) < smallest:
                smallest = len(r)
                smallest_idx = idx
        return available_regions[smallest_idx]
    return []


regions = find_available_regions(lports)
service_port_map = {service.get('name'): None for service in services}
component_service_map = {}
nginx_app_file = open("nginx_service.conf").read()

# sort services by num_ports beforehand so we allocate smallest services first
# the Bonus on the challenge requests as many services as possible
# so that is why prioritize smaller services here rather than some other metric
# like maximize ports used or components deployed
services.sort(key=lambda x: int(x.get('num_ports')), reverse=False)

# using first available port for the registrar service
p = lports.pop(0)
service_port_map['registrar'] = [p]
try:
    os.mkdir('nginx_conf')
except OSError as e:
    print(e)

conf = nginx_app_file.format(ports=p, name='registrar', components='')
open("nginx_conf/{}.conf".format('registrar'), "w+").write(conf)

for service in services:
    name = service.get('name').lower()
    num_ports = service.get('num_ports')
    components = service.get('components')
    conf_ports = []
    regions = find_available_regions(lports)
    cports = [c.get('port') for c in components if c.get('port') >= num_ports]
    # some components have port offsets greater than the service's
    # required ports. At least with the given dataset, increasing
    # the required ports to match greatest component port
    # requirements + 1 here allows additional components to be deployed
    # and increases ports assigned without reducing number of services
    # if len(cports) > 0:
    #     num_ports = cports[0] + 1
    available_region = find_region(regions, num_ports)

    if len(available_region) > num_ports:
        service_port_map[name] = available_region[:num_ports]
        port_offsets = []
        component_names = []
        if num_ports > 1:
            for component in components:
                if len(available_region) == 1:
                    # port offset 0 is saved for the service itself, not components
                    print('WARNING: Port conflict for component %s, skipping.' % component.get('name'))
                else:
                    offset = component.get('port')
                    if offset >= num_ports:
                        # some components have port offsets greater than the service's
                        # required ports.
                        print('WARNING: Port conflict for component %s, port offset greater than required ports for service, skipping.' % component.get('name'))
                    elif offset not in port_offsets and offset < num_ports:
                        port_offsets.append(offset)
                        component_names.append(component.get('name').lower())
                    else:
                        print('WARNING: Port conflict for component %s, skipping.' % component.get('name'))
        else:
            print('WARNING: Port conflict for service %s, skipping components.' % name)

        # allocate ports to components
        cpayload = ''
        for idx, cname in enumerate(component_names):
            port = port_offsets[idx] + available_region[0]
            component_payload = """
server {{
    server_name {name};
    listen {port};
    root /var/www/{name};

    location / {{
        index index.htm index.html;
    }}
}}
""".format(name=cname.lower(), port=port)
            cpayload += component_payload
            service_port_map[cname] = [port]
            component_service_map[cname] = name
            available_region.remove(port)  # port no longer available
            lports.remove(port)

        # fill rest of the required ports for service with default
        # up to port requirement
        for p in range(num_ports - len(component_names)):
            conf_ports.append(str(available_region[p]))
            lports.remove(available_region[p])
        ports = ';\n    listen '.join(conf_ports)
        conf = nginx_app_file.format(ports=ports, name=name, components=cpayload)
        open("nginx_conf/{}.conf".format(name), "w+").write(conf)

        regions = find_available_regions(lports)
    else:
        print('WARNING: Not enough valid ports left to assign, skipping service %s' % name)
        print('Service needs %s ports and there is no available region of that length.' % num_ports)


service_check = {}
for k, v in service_port_map.items():
    if v is not None:
        service_check[k] = v
print('%s services and components allocated' % len(service_check))
print('Unassigned ports: %s' % lports)

try:
    os.mkdir('nginx_www')
except OSError as e:
    print(e)


# create service index
def create_registrar(service_port_map, component_service_map):
    components = {name: ports for name, ports in service_port_map.items() if name in component_service_map.keys()}
    service_port_map['registrar'][0]
    try:
        os.mkdir('nginx_www/registrar')
    except OSError as e:
        print(e)

    # add index
    with open('nginx_www/registrar/index.html', 'w+') as out:
        html = """<h1>%s</h1><ul>""" % 'service registrar'
        for service, ports in service_port_map.items():
            if service != 'registrar':
                if service in component_service_map.keys():
                    for port in ports:
                        html += '<li><a href="http://127.0.0.1:{port}">component {service}:{port}</a></li>'.format(port=port, service=service)
                else:
                    service_ports = [p for p in ports if [p] not in components.values()]
                    for port in service_ports:
                        html += '<li><a href="http://127.0.0.1:{port}">service {service}:{port}</a></li>'.format(port=port, service=service)
        html += '</ul>'
        out.write(html)


# create service
def create_services(service_port_map, component_service_map):
    components = {name: ports for name, ports in service_port_map.items() if name in component_service_map.keys()}
    services = {name: ports for name, ports in service_port_map.items() if name not in component_service_map.keys()}

    for service, ports in services.items():
        if service != 'registrar':
            # map service ports, then check if it has any components
            html = """<h1>service %s</h1>""" % service
            html += '<h2><a href="http://localhost:{port}">service index {service}:{port}</a></h2><ul>'.format(port=services['registrar'][0], service='registrar')
            # number of components
            service_comps = {c: s for c, s in component_service_map.items() if s == service}
            service_ports = [p for p in ports if [p] not in components.values()]
            for port in service_ports:
                html += '<li><a href="http://127.0.0.1:{port}">{service}:{port}</a></li>'.format(port=port, service=service)

            for c, s in service_comps.items():
                cports = components[c]
                html += '<h2>component %s</h2>' % c

                chtml = """<h1>component %s</h1>""" % c
                chtml += '<h2><a href="http://127.0.0.1:{port}">service {service}:{port}</a></h2>'.format(port=ports[0], service=service)

                for cport in cports:
                    html += '<li><a href="http://127.0.0.1:{port}">{service}:{port}</a></li>'.format(port=cport, service=c)
                    chtml += """<h2><a href="http://127.0.0.1:{port}">component {service}:{port}</a></h2>""".format(port=cport, service=c)

                try:
                    os.mkdir('nginx_www/%s' % c)
                except OSError as e:
                    print(e)

                # write service index
                with open('nginx_www/%s/index.html' % c, 'w+') as out:
                    out.write(chtml)
            html += '</ul>'
            os.mkdir('nginx_www/%s' % service)
            # write service index
            with open('nginx_www/%s/index.html' % service, 'w+') as out:
                out.write(html)


create_registrar(service_check, component_service_map)
create_services(service_check, component_service_map)
