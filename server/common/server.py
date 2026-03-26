import socket
import logging
from .utils import Bet, store_bets

class Server:
    def __init__(self, port, listen_backlog):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
    
    def run(self):
        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock)

    def __handle_client_connection(self, client_sock):
        batch_bets = []
        try:
            # Envolvemos el socket para manejar el buffer y leer línea por línea automáticamente
            reader = client_sock.makefile('r', encoding='utf-8')
            
            for line in reader:
                line = line.strip()
                # Si el socket se cierra o llega el fin del lote, terminamos de recibir
                if not line or line == "END_BATCH":
                    break
                
                # Procesar cada apuesta
                fields = line.split(',')
                if len(fields) == 6:
                    batch_bets.append(Bet(*fields))
                else:
                    raise ValueError(f"Formato de apuesta inválido: {line}")

            if batch_bets:
                # Persistencia atómica
                store_bets(batch_bets)
                logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(batch_bets)}")
                client_sock.sendall(b"ACK\n")
            else:
                raise ValueError("No se recibieron apuestas en el lote")

        except Exception as e:
            cantidad = len(batch_bets)
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {cantidad}")
            try:
                client_sock.sendall(b"ERR\n")
            except:
                pass
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c