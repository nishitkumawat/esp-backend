from cloudinary_storage.storage import MediaCloudinaryStorage


class FirmwareStorage(MediaCloudinaryStorage):
    """
    Force RAW upload instead of image upload.
    """

    def __init__(self, *args, **kwargs):
        kwargs["resource_type"] = "raw"
        super().__init__(*args, **kwargs)
