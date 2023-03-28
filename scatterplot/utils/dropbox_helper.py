import dropbox
import dropbox.sharing

class DropboxConnector:
    def __init__(self, access_token):
        self.access_token = access_token
        self.dbx = dropbox.Dropbox(self.access_token)

    def upload_file(self, file_from, file_to):
        """upload a file to Dropbox using API v2
        """
        with open(file_from, 'rb') as f:
            self.dbx.files_upload(f.read(), file_to, mode=dropbox.files.WriteMode.overwrite)

    def download_file(self, file_from, file_to):
        """download a file from Dropbox using API v2
        """
        with open(file_to, "wb") as f:
            metadata, res = self.dbx.files_download(path=file_from)
            f.write(res.content)

    def get_shared_link(self, path)->str:
        """share a file from Dropbox using API v2
        """
        settings = dropbox.sharing.SharedLinkSettings(access=dropbox.sharing.RequestedLinkAccessLevel.viewer, requested_visibility=dropbox.sharing.RequestedVisibility.public)
        shared_url = self.dbx.sharing_create_shared_link_with_settings(path,settings)
        return shared_url
