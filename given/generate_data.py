import random
import math
import yaml

if __name__ == '__main__':
    with open('/usr/share/dict/words') as f:
        words = f.readlines()

    def rand(x, y):
        return x + int(math.floor(random.random() * y))

    def word():
        pos = rand(0, len(words))
        word = words[pos].strip()
        return word[0].upper() + word[1:]

    config = dict(
        ports=dict(
            base=16000,
            available_ranges=[
                '0-10',
                '80-85',
                '87-100',
                '150-180',
                '290-292',
                '310-370',
                '400-440',
                '447-552'
            ]),
        services=[]
    )

    for i in xrange(100):
        components = []
        num_ports = rand(1, 10)
        num_components = rand(1, math.ceil(num_ports/2))
        for _ in xrange(num_components):
            components.append(dict(
                name=word(),
                port=rand(1, num_ports)
            ))
        config['services'].append(dict(
            name=word(),
            num_ports=num_ports,
            components=components
        ))

    with open('data.yml', 'w') as outfile:
        yaml.dump(config, outfile, default_flow_style=False)
