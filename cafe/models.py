from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

class MenuBackground(models.Model):
    title = models.CharField(max_length=100, default="")
    icon_image = models.ImageField(upload_to='background_icon_images/', blank=True, null=True)
    color = models.CharField(max_length=7, help_text="Enter a hex color code (e.g., #FFFFFF for white)")
    image = models.ImageField(upload_to='background_images/', blank=True, null=True)

    description = models.TextField()
    href_instagram = models.CharField(max_length=200, default="")
    href_facebook = models.CharField(max_length=200, default="")
    href_twitter = models.CharField(max_length=200, default="")

    name = models.CharField(max_length=200, default="")
    address = models.CharField(max_length=200, default="")
    telephone = models.CharField(max_length=200, default="")
    email = models.CharField(max_length=200, default="")

    def save(self, *args, **kwargs):
        # Compress the image if it exists
        if self.image:
            img = Image.open(self.image)
            img = img.convert('RGB')  # Ensure RGB mode for JPEG compatibility

            # Resize and compress the image
            img.thumbnail((800, 800))  # Resize to max 800x800 while keeping the aspect ratio
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=85)  # Save with compression quality
            img_io.seek(0)  # Reset file pointer to the start

            # Save the new image using default storage and update the image field
            self.image.save(
                f"{self.image.name.split('.')[0]}.jpg",
                ContentFile(img_io.getvalue()),
                save=False
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Background Color: {self.color}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)  # Adjust as needed

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='subcategory_images/', blank=True, null=True)  # Subcategory image
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    price = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return self.name

class SubSubCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='subsubcategory_images/', blank=True, null=True)  # Sub-subcategory image
    subcategory = models.ForeignKey(SubCategory, related_name='subsubcategories', on_delete=models.CASCADE)
    price = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return self.name

class SubSubSubCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='subsubsubcategory_images/', blank=True, null=True)  # Sub-subcategory image
    subsubcategory = models.ForeignKey(SubSubCategory, related_name='subsubsubcategories', on_delete=models.CASCADE)
    price = models.CharField(max_length=100)
    def __str__(self):
        return self.name
