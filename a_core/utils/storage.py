import os
from django.core.files.storage import FileSystemStorage

class OverwriteStorage(FileSystemStorage):
    """
    FileSystemStorage that overwrites files with the same name by deleting them first.
    """
    def get_available_name(self, name, max_length=None):
        # If the filename already exists, remove it so the new file can reuse the same name.
        if self.exists(name):
            self.delete(name)
        return name