import socket
import logging
from .utils import Bet, store_bets

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
    
    def __exit__(self, exc_type, exc, tb):
        if self._server_socket:
            self._server_socket.shutdown(socket.SHUT_RDWR)
            self._server_socket.close()
            logging.info('action: closing_server_socket | result: success')
            

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock)

    def __handle_client_connection(self, client_sock):
        try:
            msg = self.__read_all_until_newline(client_sock)
            logging.info(f"action: receive_message | result: success | msg: {msg}")
            if not msg: return

            fields = msg.split(',')
            if len(fields) == 6:
                bet = Bet(agency=fields[0], first_name=fields[1], last_name=fields[2], 
                          document=fields[3], birthdate=fields[4], number=fields[5])
                
                store_bets([bet])
                
                logging.info(f"action: apuesta_almacenada | result: success | "
                             f"dni: {bet.document} | numero: {bet.number}")

                response = "ACK\n"
                client_sock.sendall(response.encode('utf-8'))

        except Exception as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __read_all_until_newline(self, sock):
        data = b''
        while not data.endswith(b'\n'):
            chunk = sock.recv(1024)
            if not chunk: return None
            data += chunk
        return data.decode('utf-8').strip()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
