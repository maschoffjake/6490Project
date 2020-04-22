class ProtocolServerInterface:
    def start_server(self):
        """
        Start listening to clients.
        """
        pass

    def send_file(self, path_to_file: str, message_size: int):
        """
        Send file to client.
        """
        pass
