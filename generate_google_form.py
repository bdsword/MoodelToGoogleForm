#!/usr/bin/python3
"""
Shows basic usage of the Apps Script API.
Call the Apps Script API to create a new script project, upload a file to the
project, and log the script's URL to the user.
"""
from __future__ import print_function
import os.path
import glob
from googleapiclient import errors
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import argparse

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/script.scriptapp',
    'https://www.googleapis.com/auth/forms',
    'https://www.googleapis.com/auth/drive',
]

def parse_args():
    parser = argparse.ArgumentParser(description='Upload assets and generate form with assets.')
    parser.add_argument('--meta_csv_path', required=True,
                        help='Path to the meta data csv file.')
    parser.add_argument('--images_dir_path', required=True, help='Path to the question images.')
    args = parser.parse_args()
    return args

def upload_imgs_and_meta(creds, imgDir, metaPath):
    # Build Drive API service.
    service = build('drive', 'v3', credentials=creds)

    # Create a Assets folder.
    fileMetadata = {
        'name': 'AutoFormAssets',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    assetsFolder = service.files().create(body=fileMetadata, fields='id').execute()
    assetsFolderId = assetsFolder.get('id')

    for imagePath in glob.glob('{}/*.png'.format(imgDir)):
        print('Upload {}...'.format(imagePath), end='', flush=True)
        print(os.path.basename(imagePath))
        fileMetadata = {
            'name': os.path.basename(imagePath),
            'parents': [assetsFolderId]
        }
        media = MediaFileUpload(imagePath,
                                mimetype='image/png',
                                resumable=True)
        file = service.files().create(body=fileMetadata, media_body=media, fields='id').execute()
        print('done', flush=True)

    # Upload meta csv file
    print('Upload {}...'.format(metaPath), end='', flush=True)
    fileMetadata = {
        'name': os.path.basename(metaPath),
        'parents': [assetsFolderId]
    }
    media = MediaFileUpload(metaPath, mimetype=None, resumable=True)
    file = service.files().create(body=fileMetadata, media_body=media, fields='id').execute()
    print('done', flush=True)

    return

def main():
    args = parse_args()

    """Calls the Apps Script API.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    upload_imgs_and_meta(creds, args.images_dir_path, args.meta_csv_path)

    service = build('script', 'v1', credentials=creds)

    deploymentId = '**** Please fill you own Deployment ID ****'

    # Call the Apps Script API
    try:
        print('Create Google Form...', end='', flush=True)
        request = {"function": 'createForm'}
        response = service.scripts().run(body=request, scriptId=deploymentId).execute()
        print('Done')
    except errors.HttpError as error:
        # The API encountered a problem.
        print(error.content)


if __name__ == '__main__':
    main()
