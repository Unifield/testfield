FROM ubuntu
MAINTAINER hectord

WORKDIR /root

RUN apt-get update
RUN apt-get install -y tmux libxml2-dev libxslt1-dev python-dev libjpeg-dev libpng-dev libfreetype6-dev build-essential xvfb firefox wget pkg-config libpq-dev python-dev bzr git postgresql-9.5 vim telnet

RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py
ADD requirements.txt .
RUN pip install -r requirements.txt

RUN /etc/init.d/postgresql start && \
    runuser -l  postgres -c "psql -c \"CREATE USER unifield_dev WITH PASSWORD 'unifield_dev';\"" && \
    runuser -l  postgres -c "psql -c \"ALTER USER unifield_dev WITH CREATEDB\"" && \
    runuser -l  postgres -c "psql -c \"ALTER USER unifield_dev WITH SUPERUSER\""

RUN bzr init-repo --no-trees repo

RUN cd repo && bzr checkout lp:unifield-server server
RUN cd repo && bzr checkout lp:unifield-web web

RUN ls && ls && ls && ls && ls && git clone https://github.com/hectord/testfield.git

WORKDIR /root/testfield

RUN mkdir output

ADD instances instances
ADD meta_features meta_features

ADD config.sh .
ADD run.sh .

RUN chmod +x run.sh

ENTRYPOINT ["./run.sh"]

EXPOSE 8080

