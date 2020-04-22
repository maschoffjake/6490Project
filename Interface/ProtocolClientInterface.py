class ProtocolClientInterface:
    def connect(self):
        """
        Connect to server.
        """
        pass

    def receive_file(self, message_size: int):
        """
        Save file from server.
        """
        pass
