FROM python:3.11

# Debug programs
RUN apt update
RUN apt install -y iputils-ping
RUN apt install -y telnet

# micrOS install via pip
RUN python3 -m pip install --upgrade pip --no-cache-dir

# [A] Build with specific PYPI version
RUN python3 -m pip install micrOSDevToolKit==1.54.3
# [B] Build with development version from github
#RUN python3 -m pip install git+https://github.com/BxNxM/micrOS.git

EXPOSE 5000

# Run start command
# Search and start gateway and start simulator (beta)
#ENTRYPOINT devToolKit.py -s -gw -sim
# Search and start gateway
ENTRYPOINT devToolKit.py -s -gw
