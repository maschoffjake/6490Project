import os.path
import sys
import pprint

# Used for OAuth2
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# Request access to reading data from google drive
# https://developers.google.com/drive/api/v3/about-auth (for other scopes we could use)
SCOPES = ['https://www.googleapis.com/auth/drive']
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

pp = pprint.PrettyPrinter(indent=4)
refresh_token = ''

def main():

    # Build the credentials associated with our APP (google app)
    flow = InstalledAppFlow.from_client_secrets_file(
        '../conf/credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    print(creds)
    pp.pprint(vars(creds))
    drive = build('drive', 'v3', credentials=creds)
    files = drive.files().list().execute()
    # service = build('gmail', 'v1', credentials=creds) Gmail

    print("Verified!")
    # files_arr = files['files']
    # for item in files_arr:
    #     print(item['name'])
    # pp.pprint(files)
    # Call the Gmail API
    # results = service.users().labels().list(userId='me').execute()
    # labels = results.get('labels', [])

    # print("Size of results:", sys.getsizeof(results))

    # if not labels:
    #     print('No labels found.')
    # else:
    #     print('Labels:')
    #     for label in labels:
    #         print(label['name'])

if __name__ == '__main__':
    main()