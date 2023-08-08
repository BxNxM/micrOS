FROM python:3.9

# Debug programs
RUN apt update
RUN apt install -y iputils-ping
RUN apt install -y telnet

# micrOS install via pip
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install micrOSDevToolKit==1.22.2
#RUN python3 -m pip install git+https://github.com/BxNxM/micrOS.git

EXPOSE 5000

# Run start command
#ENTRYPOINT devToolKit.py -gw -sim
ENTRYPOINT devToolKit.py -gw
