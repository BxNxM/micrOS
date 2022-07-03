FROM python:3.8

RUN python3 -m pip install --upgrade pip; python3 -m pip install git+https://github.com/BxNxM/micrOS.git

EXPOSE 5000

ENTRYPOINT devToolKit.py -gw
