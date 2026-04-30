"""
Module de communication réseau entre PC
"""

import socket
import json
import threading
from typing import Callable
import config

class NetworkServer:
    """
    Serveur réseau pour recevoir les données du PC esclave
    """

    def __init__(self, callback: Callable[[int], None]):
        self.callback = callback
        self.server_socket = None
        self.is_running = False
        self.thread = None

    def start(self):
        """Démarre le serveur d'écoute"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', config.NETWORK_PORT))
            self.server_socket.listen(1)

            self.is_running = True
            self.thread = threading.Thread(target=self._listen, daemon=True)
            self.thread.start()

            print(f"Serveur démarré sur le port {config.NETWORK_PORT}")

        except Exception as e:
            print(f"Erreur serveur: {e}")

    def _listen(self):
        """Boucle d'écoute des connexions"""
        while self.is_running:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()

                data = conn.recv(config.BUFFER_SIZE).decode('utf-8')
                if data:
                    message = json.loads(data)
                    count = message.get('count', 0)
                    self.callback(count)

                conn.close()

            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    print(f"Erreur réception: {e}")

    def stop(self):
        """Arrête le serveur"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()


class NetworkClient:
    """
    Client réseau pour envoyer les données au PC maître
    """

    def __init__(self, master_ip: str):
        self.master_ip = master_ip

    def send_count(self, count: int) -> bool:
        """
        Envoie le comptage au PC maître
        Retourne True si succès, False sinon
        """
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(2.0)
            client_socket.connect((self.master_ip, config.NETWORK_PORT))

            message = json.dumps({'count': count})
            client_socket.send(message.encode('utf-8'))

            client_socket.close()
            return True

        except Exception as e:
            print(f"Erreur envoi réseau: {e}")
            return False
