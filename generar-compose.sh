#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <config_file_name> <number_of_clients>"
    exit 1
fi

OUTPUT_FILE=$1
NUM_CLIENTS=$2

# Header and Server
cat <<EOF > "$OUTPUT_FILE"
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini
EOF

# Clients
for i in $(seq 1 "$NUM_CLIENTS"); do
    cat <<EOF >> "$OUTPUT_FILE"

  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=$i
      - NOMBRE=Nombre$i
      - APELLIDO=Apellido$i
      - DOCUMENTO=$i$i$i$i$i$i$i$i
      - NACIMIENTO=199$i-0$i-0$i
      - NUMERO=$i$i$i$i
    networks:
      - testing_net
    depends_on:
      - server
    volumes:
      - ./client/config.yaml:/config.yaml
      - ./.data/agency-$i.csv:/agency.csv
EOF
done

# Network and posibly more in the future
cat <<EOF >> "$OUTPUT_FILE"

networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOF

echo "Successfully generated $OUTPUT_FILE with $NUM_CLIENTS clients."