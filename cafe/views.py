from django.shortcuts import render
from django.views import View  # Import View here
from .models import Category, SubCategory, SubSubCategory, SubSubSubCategory, MenuBackground

def search_subsubcategory(request):
    query = request.GET.get('q')
    # Perform the search logic for subsubcategories based on query
    subsubcategories = SubSubCategory.objects.filter(name__contains=query)  # Fetch sub-subcategories for the selected subcategory
    if subsubcategories:
        background = MenuBackground.objects.first()
        return render(request, 'cafe/subsubcategories_list.html', {
            'subsubcategories': subsubcategories,
            'background': background
        })
    else:
        categories = Category.objects.all()  # Fetch all categories
        background = MenuBackground.objects.first()
        return render(request, 'cafe/category_list.html', {'categories': categories, 'background': background})

class MenuView(View):
    def get(self, request):
        categories = Category.objects.all()  # Fetch all categories
        background = MenuBackground.objects.first()
        return render(request, 'cafe/category_list.html', {'categories': categories, 'background': background})

class SubCategoryListView(View):
    def get(self, request, category_id):
        subcategories = SubCategory.objects.filter(category_id=category_id)  # Fetch subcategories for the selected category
        category = Category.objects.get(id=category_id)  # Get the category object
        background = MenuBackground.objects.first()
        return render(request, 'cafe/subcategory_list.html', {
            'subcategories': subcategories,
            'category': category,
            'background': background
        })


class SubSubCategoryListView(View):
    def get(self, request, subcategory_id):
        subsubcategories = SubSubCategory.objects.filter(subcategory_id=subcategory_id)  # Fetch sub-subcategories for the selected subcategory
        subcategory = SubCategory.objects.get(id=subcategory_id)  # Get the subcategory object
        background = MenuBackground.objects.first()
        return render(request, 'cafe/subsubcategories_list.html', {
            'subsubcategories': subsubcategories,
            'subcategory': subcategory,
            'background': background
        })

class SubSubSubCategoryListView(View):
    def get(self, request, subsubcategory_id):
        subsubcategory = SubSubCategory(SubSubCategory, pk=subsubcategory_id)
        subsubsubcategories = SubSubSubCategory.objects.filter(subsubcategory=subsubcategory)
        background = MenuBackground.objects.first()
        return render(request, 'cafe/subsubsubcategories_list.html', {
            'subsubsubcategories': subsubsubcategories,
            'subsubcategory': subsubcategory,
            'background': background
        })
