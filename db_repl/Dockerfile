FROM postgres:latest
RUN rm -rf /var/lib/postgresql/data/*
RUN echo "host replication repl_user 192.168.218.158/24 password" >> /var/lib/postgresql/data/pg_hba.conf
