FROM postgres:latest

ARG DB_DATABASE
ARG DB_REPL_USER
ARG DB_REPL_PASSWORD
ARG DB_USER
ARG DB_PASSWORD

COPY init.sql /docker-entrypoint-initdb.d/

RUN sed -i -e "s/\$DB_DATABASE/${DB_DATABASE}/g" /docker-entrypoint-initdb.d/init.sql
RUN sed -i -e "s/\$DB_REPL_USER/${DB_REPL_USER}/g" /docker-entrypoint-initdb.d/init.sql
RUN sed -i -e "s/\$DB_REPL_PASSWORD/${DB_REPL_PASSWORD}/g" /docker-entrypoint-initdb.d/init.sql
RUN sed -i -e "s/\$DB_USER/${DB_USER}/g" /docker-entrypoint-initdb.d/init.sql
RUN sed -i -e "s/\$DB_PASSWORD/${DB_PASSWORD}/g" /docker-entrypoint-initdb.d/init.sql


RUN mkdir -p /var/log/postgresql
