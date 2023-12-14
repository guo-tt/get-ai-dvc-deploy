from azure.storage.blob import ContainerClient


class AzureBlob():
    def __init__(self, account_url, container_name, sas_token):
        self.container_client = ContainerClient(
            account_url=account_url,
            container_name=container_name,
            credential=sas_token
        )


    def upload_to_blob(self, blob_key, data, overwrite='True', encoding='utf-8'):
        # TODO: separate the logics to handle file and data uploads
        self.container_client.upload_blob(
            blob_key,
            data,
            overwrite=overwrite,
            encoding=encoding
        )


    def get_blob_content(self, blob_key):
        s = self.container_client.download_blob(blob_key)
        return s.content_as_text()


    def list_blob(self, prefix=None):
        return self.container_client.list_blobs(name_starts_with=prefix)
