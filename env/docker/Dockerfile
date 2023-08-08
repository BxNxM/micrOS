FROM python:3.9

# Debug programs
RUN apt update
RUN apt install -y iputils-ping
RUN apt install -y telnet

# micrOS install via pip
RUN python3 -m pip install --upgrade pip
#RUN python3 -m pip install micrOSDevToolKit
RUN python3 -m pip install git+https://github.com/BxNxM/micrOS.git

# Run start command
ENTRYPOINT devToolKit.py -gw -sim
