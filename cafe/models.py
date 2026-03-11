from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

class MenuBackground(models.Model):
    title = models.CharField(max_length=100, default="")
    title_en = models.CharField(max_length=100, default="", blank=True)
    icon_image = models.ImageField(upload_to='background_icon_images/', blank=True, null=True)
    color = models.CharField(max_length=7, help_text="Enter a hex color code (e.g., #FFFFFF for white)")
    image = models.ImageField(upload_to='background_images/', blank=True, null=True)

    description = models.TextField(default="", null=True)
    description_en = models.TextField(default="", null=True, blank=True)
    href_instagram = models.CharField(max_length=200, default="")
    href_facebook = models.CharField(max_length=200, default="")
    href_twitter = models.CharField(max_length=200, default="")

    name = models.CharField(max_length=200, default="")
    address = models.CharField(max_length=200, default="")
    address_en = models.CharField(max_length=200, default="", blank=True)
    telephone = models.CharField(max_length=200, default="")
    email = models.CharField(max_length=200, default="")
    video_url = models.URLField(max_length=500, blank=True, default="", help_text="YouTube, Vimeo veya Instagram Reel linki (mekan tanıtımı)")

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

    def get_video_embed_url(self):
        """YouTube/Vimeo/Instagram URL'den embed URL döndür."""
        if not self.video_url:
            return None
        url = self.video_url.strip()
        # YouTube: youtu.be/XXX veya youtube.com/watch?v=XXX
        if "youtu.be/" in url:
            vid = url.split("youtu.be/")[-1].split("?")[0]
            return f"https://www.youtube.com/embed/{vid}" if vid else None
        if "youtube.com" in url and "v=" in url:
            import re
            m = re.search(r"[?&]v=([^&]+)", url)
            return f"https://www.youtube.com/embed/{m.group(1)}" if m else None
        # Vimeo: vimeo.com/XXX
        if "vimeo.com/" in url:
            vid = url.split("vimeo.com/")[-1].split("?")[0]
            return f"https://player.vimeo.com/video/{vid}" if vid else None
        # Instagram Reel: instagram.com/reel/XXX
        if "instagram.com/reel/" in url:
            vid = url.split("instagram.com/reel/")[-1].split("/")[0].split("?")[0]
            return f"https://www.instagram.com/reel/{vid}/embed/" if vid else None
        return None

    def __str__(self):
        return f"Background Color: {self.color}"


class Campaign(models.Model):
    """
    Ana sayfada (kategori ekranında) gösterilecek kampanya popup içeriği.
    Örnek: "Hamburger + kola + patates 100 TL".
    """
    title = models.CharField(
        max_length=150,
        help_text="Kısa başlık (örn. 'MENÜ KAMPANYASI' veya 'Günün Fırsatı')."
    )
    title_en = models.CharField(
        max_length=150,
        blank=True,
        default="",
        help_text="İngilizce başlık (boş bırakılırsa Türkçe başlık kullanılır)."
    )
    description = models.TextField(
        help_text="Detay yazısı (örn. 'Hamburger + Kola + Patates sadece 100 TL')."
    )
    description_en = models.TextField(
        blank=True,
        default="",
        help_text="İngilizce açıklama (boş bırakılırsa Türkçe açıklama kullanılır)."
    )
    price_text = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="İsteğe bağlı fiyat metni (örn. '100 TL')."
    )
    image = models.ImageField(
        upload_to="campaign_images/",
        blank=True,
        null=True,
        help_text="Kampanya görseli (örn. hamburger menü fotoğrafı)."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Sadece aktif olan kampanya ana sayfada popup olarak gösterilir."
    )
    show_on_home = models.BooleanField(
        default=True,
        help_text="İşaretliyse kategori (ana menü) sayfasında gösterilir."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class Category(models.Model):
    name = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, default="", blank=True)
    description = models.TextField(default="", null=True)
    description_en = models.TextField(default="", null=True, blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)  # Adjust as needed
    order = models.PositiveIntegerField(default=0)  # Used for manual sorting

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, default="", blank=True)
    description = models.TextField(default="", null=True)
    description_en = models.TextField(default="", null=True, blank=True)
    image = models.ImageField(upload_to='subcategory_images/', blank=True, null=True)  # Subcategory image
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    price = models.CharField(max_length=100, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)  # Used for manual sorting

    class Meta:
        ordering = ['order']
    def __str__(self):
        return self.name

class SubSubCategory(models.Model):
    name = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, default="", blank=True)
    description = models.TextField(default="", null=True)
    description_en = models.TextField(default="", null=True, blank=True)
    image = models.ImageField(upload_to='subsubcategory_images/', blank=True, null=True)  # Sub-subcategory image
    subcategory = models.ForeignKey(SubCategory, related_name='subsubcategories', on_delete=models.CASCADE)
    price = models.CharField(max_length=100, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)  # Used for manual sorting

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class SubSubSubCategory(models.Model):
    name = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, default="", blank=True)
    description = models.TextField(default="", null=True)
    description_en = models.TextField(default="", null=True, blank=True)
    image = models.ImageField(upload_to='subsubsubcategory_images/', blank=True, null=True)  # Sub-subcategory image
    subsubcategory = models.ForeignKey(SubSubCategory, related_name='subsubsubcategories', on_delete=models.CASCADE)
    price = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)  # Used for manual sorting

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name
