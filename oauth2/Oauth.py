import sys
import pprint
import requests
import json

# Used for OAuth2
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from Interface.ProtocolClientInterface import ProtocolClientInterface

class Oauth2(ProtocolClientInterface):
    def __init__(self):
        """
        Create an Oauth2 instance that connects to google drive and downloads a file
        """
        # Request access to reading data from google drive
        # https://developers.google.com/drive/api/v3/about-auth (for other scopes we could use)
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.pp = pprint.PrettyPrinter(indent=4)
        self.context = self.create_oauth2_context(self)
        self.access_token = None
        self.authorization_url = "https://www.googleapis.com/oauth2/v4/token"

    @staticmethod
    def create_oauth2_context(self):
        """
        Create the Oauth2 context in order to create an access token used 
        for google drive to download a file
        """

        # Build the credentials associated with our app (google app deployed on GCP)
        # Make sure this credentials path points to a JSON with the following fields for the app:
        #  "client_id"
        #  "project_id"
        #  "auth_uri"
        #  "token_uri"
        #  "auth_provider_x509_cert_url"
        #  "client_secret"
        #  "access_type":"offline"      used for getting a refresh token the first time...
        #  "refresh_token"
        #  "redirect_uris":             where to redirect too on successful authentification
        flow = InstalledAppFlow.from_client_secrets_file(
            './conf/credentials.json', self.SCOPES)

        creds = flow.run_local_server(port=0)
        self.pp.pprint(vars(creds))

        # Need to grab the data from this object returned...
        creds_data = vars(creds)
        oauth2_context = {
            "grant_type": "refresh_token",
            "client_id": creds_data['_client_id'],
            "client_secret": creds_data['_client_secret'],
            "refresh_token": creds_data['_refresh_token']
        }
        return oauth2_context

    def connect(self):
        """
        Function used to connect to Google's Oauth2.0 by using a refresh token
        that was created in the constructor to create an access token
        """

        # Reset access token to ensure a new one is being created each time
        self.access_token = None

        r = requests.post(self.authorization_url, data=self.context)
        print(r.json())

        if r.ok:
            self.access_token = r.json()['access_token']
        else:
            print("Error, didn't receive token. Exiting.")
            exit(-1)

    def receive_file(self, message_size=16*1024):
        """
        Function used for receiving a file from the connection made, defaults to 16KB sized messages
        :param message_size:
        :return:
        """
        total_data = []
        data = self.ssock.recv(message_size)
        while data != bytes(''.encode()):
            total_data.append(data)
            data = self.ssock.recv(message_size)

        logging.debug('CLIENT: Done receiving file')
        # logging.debug('CLIENT: File received (truncated):', total_data[:40])
