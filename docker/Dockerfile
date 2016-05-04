FROM ubuntu
MAINTAINER hectord

WORKDIR /root

RUN apt-get update
RUN apt-get install -y tmux libxml2-dev libxslt1-dev python-dev libjpeg-dev libpng-dev libfreetype6-dev build-essential xvfb firefox wget pkg-config libpq-dev python-dev bzr git vim telnet

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" > /etc/apt/sources.list.d/pgdg.list
apt-get update
apt-get install -y --allow-unauthenticated postgresql-8.4

RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py
ADD requirements.txt .
RUN pip install -r requirements.txt

RUN bzr init-repo --no-trees repo
RUN cd repo && bzr checkout lp:unifield-server server
RUN cd repo && bzr checkout lp:unifield-web web

RUN /etc/init.d/postgresql start && \
    runuser -l  postgres -c "psql -c \"CREATE USER unifield_dev WITH PASSWORD 'unifield_dev';\"" && \
    runuser -l  postgres -c "psql -c \"ALTER USER unifield_dev WITH CREATEDB\"" && \
    runuser -l  postgres -c "psql -c \"UPDATE pg_database set datallowconn = TRUE where datname = 'template0';\"" && \
    runuser -l  postgres -c "psql -c \"UPDATE pg_database set datistemplate = FALSE where datname = 'template1';\"" && \
    runuser -l  postgres -c "psql -c \"DROP DATABASE template1\"" && \
    runuser -l  postgres -c "psql -c \"CREATE DATABASE template1 with template = template0 encoding = 'UTF8'\"" && \
    runuser -l  postgres -c "psql -c \"UPDATE pg_database set datistemplate = TRUE where datname = 'template1';\" template0" && \
    runuser -l  postgres -c "psql -c \"UPDATE pg_database set datallowconn = FALSE where datname = 'template0';\" template1"

VOLUME ["/input"]

VOLUME ["/output"]

ADD docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["/root/docker-entrypoint.sh"]

EXPOSE 8080
EXPOSE 8003

