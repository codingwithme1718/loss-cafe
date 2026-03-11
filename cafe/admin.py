from django.contrib import admin
from .models import Category, SubCategory, SubSubCategory, SubSubSubCategory, MenuBackground, Campaign

admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(SubSubCategory)
admin.site.register(SubSubSubCategory)
admin.site.register(MenuBackground)
admin.site.register(Campaign)
