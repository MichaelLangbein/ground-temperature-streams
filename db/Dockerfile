FROM yandex/clickhouse-server:latest

COPY init-clickhouse.sql /docker-entrypoint-initdb.d/

# Use an entrypoint script to initialize the database
ENTRYPOINT ["/bin/bash", "-c", "cat /docker-entrypoint-initdb.d/init-clickhouse.sql | clickhouse-client && exec clickhouse-server"]
