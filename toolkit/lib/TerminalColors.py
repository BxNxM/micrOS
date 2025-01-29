#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys


class Colors:
    is_active = False if sys.platform.startswith('win') else True
    if is_active is True:
        NC = '\033[0m'
        OK = '\033[92m'
        ERR = '\033[91m'
        WARN = '\033[93m'
        BOLD = '\033[1m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        HEADER = '\033[95m'
        UNDERLINE = '\033[4m'
        LIGHT_GRAY = '\033[37m'
        GRAY = '\033[90m'
    else:
        NC = ''
        OK = ''
        ERR = ''
        WARN = ''
        BOLD = ''
        OKBLUE = ''
        OKGREEN = ''
        HEADER = ''
        UNDERLINE = ''
        LIGHT_GRAY = ''
        GRAY = ''


if __name__ == "__main__":
    #TEST COLORS:
    print(Colors.OK + "[ OK ] - green" + Colors.NC)
    print(Colors.ERR + "[ ERR ] - red" + Colors.NC)
    print(Colors.WARN + "[ WAR ] - yellow" + Colors.NC)
    print(Colors.BOLD + "[ BOLD ] - bold" + Colors.NC)

