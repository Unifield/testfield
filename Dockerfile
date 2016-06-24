FROM ubuntu:xenial
MAINTAINER hectord

WORKDIR /root

RUN apt-get update && apt-get install -y tmux libxml2-dev libxslt1-dev python-dev libjpeg-dev libpng-dev libfreetype6-dev build-essential wget pkg-config libpq-dev python-dev bzr git vim telnet net-tools unzip netcat-openbsd xvfb
RUN apt-get update && apt-get install -y firefox=45.0.2+build1-0ubuntu1

RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py
ADD requirements.txt .
RUN pip install -r requirements.txt


RUN git clone https://github.com/wolfcw/libfaketime.git && cd libfaketime && make && make install

RUN adduser --disabled-password --gecos "" testing
USER testing

WORKDIR /home/testing

RUN bzr init-repo --no-trees repo
RUN cd repo && bzr checkout lp:unifield-server server
RUN cd repo && bzr checkout lp:unifield-web web

USER root

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" > /etc/apt/sources.list.d/pgdg.list
RUN apt-get update && apt-get install -y --allow-unauthenticated postgresql-8.4

ADD docker/docker-entrypoint.sh .
ADD docker/root-entrypoint.sh .
ADD docker/config.sh .

RUN apt-get update && apt-get install -y expect

ENTRYPOINT ["/home/testing/root-entrypoint.sh"]

EXPOSE 8080
EXPOSE 8006
EXPOSE 8061

VOLUME ["/output"]

