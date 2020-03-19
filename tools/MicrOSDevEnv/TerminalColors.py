class Colors():
    is_active = True
    if is_active is True:
        NC = '\033[0m'
        OK = '\033[92m'
        ERR = '\033[91m'
        WARN = '\033[93m'
        BOLD = '\033[1m'
    else:
        NC = ''
        OK = ''
        ERR = ''
        WARN = ''
        BOLD = ''

if __name__ == "__main__":
    #TEST COLORS:
    print(Colors.OK + "[ OK ] - green" + Colors.NC)
    print(Colors.ERR + "[ ERR ] - red" + Colors.NC)
    print(Colors.WARN + "[ WAR ] - yellow" + Colors.NC)
    print(Colors.BOLD + "[ BOLD ] - bold" + Colors.NC)

