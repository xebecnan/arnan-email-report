# coding: utf-8

import os

INCOMING = 'incoming'

if not os.path.isdir(INCOMING):
    os.mkdir(INCOMING)

count = 0
for root, dirs, names in os.walk(INCOMING):
    for name in names:
        if name.endswith('.txt'):
            path = os.path.join(root, name)
            print('DELETE:', path)
            os.remove(path)
            count += 1

print('clear-incoming done. %d files deleted' % count)

