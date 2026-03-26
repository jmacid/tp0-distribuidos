import socket
import logging
import threading
import os
from .utils import Bet, store_bets, load_bets, has_won

class Server:
    def __init__(self, port, listen_backlog):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        
        self.lock = threading.Lock()
        self.draw_condition = threading.Condition(self.lock)
        self.agencies_finished = set()
        
        clients_env = os.environ.get('CLIENT_AMOUNT', os.environ.get('CLIENTS', 5))
        self.expected_agencies = int(clients_env)
        
        self.draw_done = False
        self.winners_by_agency = {}
    
    def run(self):
        while True:
            client_sock = self.__accept_new_connection()
            t = threading.Thread(target=self.__handle_client_connection, args=(client_sock,))
            t.start()

    def __handle_client_connection(self, client_sock):
        try:
            reader = client_sock.makefile('r', encoding='utf-8')
            batch_bets = []
            is_fin = False
            agency_id = None
            
            for line in reader:
                line = line.strip()
                if not line:
                    break
                
                if line == "END_BATCH":
                    break
                    
                if line.startswith("FIN_AGENCIA"):
                    _, agency_id = line.split(',')
                    is_fin = True
                    break

                fields = line.split(',')
                if len(fields) == 6:
                    batch_bets.append(Bet(*fields))
                else:
                    raise ValueError(f"Formato de apuesta inválido: {line}")

            if is_fin:
                self.__handle_fin_agencia(client_sock, agency_id)
            else:
                if batch_bets:
                    with self.lock:
                        store_bets(batch_bets)
                    logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(batch_bets)}")
                    client_sock.sendall(b"ACK\n")
                else:
                    raise ValueError("No se recibieron apuestas en el lote")

        except Exception as e:
            cantidad = len(batch_bets) if not is_fin else 0
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {cantidad}")
            try:
                client_sock.sendall(b"ERR\n")
            except:
                pass
        finally:
            client_sock.close()

    def __handle_fin_agencia(self, client_sock, agency_id):
        with self.draw_condition:
            self.agencies_finished.add(int(agency_id))
            
            while len(self.agencies_finished) < self.expected_agencies and not self.draw_done:
                self.draw_condition.wait()
            
            if not self.draw_done:
                logging.info("action: sorteo | result: success")
                self.__do_draw()
                self.draw_done = True
                self.draw_condition.notify_all()
            
            winners = self.winners_by_agency.get(int(agency_id), [])
            response = ",".join(winners) + "\n"
            client_sock.sendall(response.encode('utf-8'))

    def __do_draw(self):
        self.winners_by_agency = {}
        for bet in load_bets():
            if has_won(bet):
                if bet.agency not in self.winners_by_agency:
                    self.winners_by_agency[bet.agency] = []
                self.winners_by_agency[bet.agency].append(bet.document)

    def __accept_new_connection(self):
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c