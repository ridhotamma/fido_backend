import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


class LocalMediaStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None):
        location = location or os.path.join(settings.BASE_DIR, 'media')
        base_url = base_url or '/media/'
        super().__init__(location, base_url)


class S3MediaStorage(S3Boto3Storage):
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False
    custom_domain = getattr(settings, 'AWS_CLOUDFRONT_DOMAIN', None)


class ImageVariantMixin:
    VARIANTS = {
        'sm': (64, 64),
        'md': (256, 256),
        'lg': (512, 512),
    }

    def generate_variants(self, image_field, storage, base_path):
        variants = {}
        img = Image.open(image_field)
        for key, size in self.VARIANTS.items():
            img_copy = img.copy()
            img_copy.thumbnail(size, Image.LANCZOS)
            buffer = BytesIO()
            img_copy.save(buffer, format=img.format or 'JPEG')
            file_name = f"{base_path}_{key}.{img.format.lower() if img.format else 'jpg'}"
            file_content = ContentFile(buffer.getvalue())
            storage.save(file_name, file_content)
            variants[key] = storage.url(file_name)
        return variants
