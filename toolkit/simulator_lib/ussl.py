
def wrap_socket(sock):
    try:
        from ssl import wrap_socket
        return wrap_socket(sock)
    except Exception as e:
        print(f"[SIMULATOR] WARNING - SSL INTERFACE CHANCE IN PYTHON 3.12...: {e}")
        return sock