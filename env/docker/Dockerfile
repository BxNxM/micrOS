FROM python:3.9

# Debug programs
RUN apt update && apt install -y iputils-ping

# micrOS install via pip
RUN python3 -m pip install --upgrade pip
#RUN python3 -m pip install micrOSDevToolKit
RUN python3 -m pip install git+https://github.com/BxNxM/micrOS.git

# Run start command
ENTRYPOINT devToolKit.py -gw -sim
