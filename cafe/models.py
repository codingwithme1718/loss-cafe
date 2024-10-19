from django.db import models

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
    def __str__(self):
        return f"Background Color: {self.color}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='category_images/')  # Adjust as needed
    def __str__(self):
        return self.name

class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='subcategory_images/')  # Subcategory image
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class SubSubCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='subsubcategory_images/')  # Sub-subcategory image
    subcategory = models.ForeignKey(SubCategory, related_name='subsubcategories', on_delete=models.CASCADE)

    def __str__(self):
        return self.name