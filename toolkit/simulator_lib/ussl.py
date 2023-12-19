
def wrap_socket(sock):
    try:
        from ssl import wrap_socket
        return wrap_socket(sock)
    except Exception as e:
        print(f"[SIMULATOR][micropython DIFF] WARNING(1/2) - SSL INTERFACE CHANCE IN PYTHON 3.12...: {e}")
    try:
        from ssl import create_default_context, CERT_NONE
        context = create_default_context()
        context.check_hostname = False
        context.verify_mode = CERT_NONE
        return context.wrap_socket(sock)
    except Exception as e:
        print(f"[SIMULATOR][WRAP] ERROR(2/2) - SSL INTERFACE CHANCE IN PYTHON 3.12...: {e}")
    return sock