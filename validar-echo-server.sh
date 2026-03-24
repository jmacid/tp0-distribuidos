#!/bin/bash

NETWORK_NAME="tp0_testing_net"

# Extraer configuración del archivo .ini
CONFIG_FILE="./server/config.ini"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "action: test_echo_server | result: fail (missing config)"
    exit 1
fi

PORT=$(grep "SERVER_PORT" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
SERVER_NAME=$(grep "SERVER_IP" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
TEST_MESSAGE="Hola_Mundo_$(date +%s)"

# Ejecutar Netcat dentro de la misma red de Docker que el servidor
RESULT=$(docker run --rm --network="$NETWORK_NAME" alpine /bin/sh -c "echo '$TEST_MESSAGE' | nc $SERVER_NAME $PORT")

# Validar si lo recibido es igual a lo enviado
if [ "$RESULT" = "$TEST_MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi