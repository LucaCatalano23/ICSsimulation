FROM ubuntu:20.04

RUN mkdir src

COPY ./src/ ./src/

RUN apt-get update

RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y tzdata

RUN apt-get update \
&& apt-get install -y sudo \
&& apt-get install -y python3 \
&& apt-get install -y python3-pip \
&& apt-get install -y python3-tk \
&& pip install webauthn \
&& pip install flask \
&& pip install pyModbusTCP \
&& pip install mysql-connector-python 

ENV DISPLAY=:0

WORKDIR /src

