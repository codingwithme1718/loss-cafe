from django.shortcuts import render
from django.views import View
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import Category, SubCategory, SubSubCategory, SubSubSubCategory, MenuBackground


def _get_background():
    bg = MenuBackground.objects.first()
    if bg:
        return bg
    return MenuBackground.objects.create(
        title='Loss Cafe', color='#0d5c2e', description='', name='Loss Cafe',
        address='', telephone='', email=''
    )


def search_subsubcategory(request):
    query = request.GET.get('q')
    # Perform the search logic for subsubcategories based on query
    subsubcategories = SubSubCategory.objects.filter(name__contains=query)  # Fetch sub-subcategories for the selected subcategory
    if subsubcategories:
        background = _get_background()
        return render(request, 'cafe/subsubcategories_list.html', {
            'subsubcategories': subsubcategories,
            'background': background
        })
    else:
        categories = Category.objects.all()  # Fetch all categories
        background = _get_background()
        return render(request, 'cafe/category_list.html', {'categories': categories, 'background': background})

class MenuView(View):
    def get(self, request):
        categories = Category.objects.all().prefetch_related('subcategories')
        background = _get_background()
        return render(request, 'cafe/category_list.html', {'categories': categories, 'background': background})

@method_decorator(cache_page(60 * 2), name='dispatch')
class SubCategoryListView(View):
    def get(self, request, category_id):
        subcategories = SubCategory.objects.filter(category_id=category_id).select_related('category')
        category = Category.objects.get(id=category_id)
        background = _get_background()
        return render(request, 'cafe/subcategory_list.html', {
            'subcategories': subcategories,
            'category': category,
            'background': background
        })


@method_decorator(cache_page(60 * 2), name='dispatch')
class SubSubCategoryListView(View):
    def get(self, request, subcategory_id):
        subsubcategories = SubSubCategory.objects.filter(subcategory_id=subcategory_id).select_related('subcategory')
        subcategory = SubCategory.objects.get(id=subcategory_id)
        background = _get_background()
        return render(request, 'cafe/subsubcategories_list.html', {
            'subsubcategories': subsubcategories,
            'subcategory': subcategory,
            'background': background
        })

@method_decorator(cache_page(60 * 2), name='dispatch')
class SubSubSubCategoryListView(View):
    def get(self, request, subcategory_id, subsubcategory_id):
        subsubsubcategories = SubSubSubCategory.objects.filter(subsubcategory_id=subsubcategory_id)
        subsubcategory = SubSubCategory.objects.get(id=subsubcategory_id)
        background = _get_background()
        return render(request, 'cafe/subsubsubcategories_list.html', {
            'subsubsubcategories': subsubsubcategories,
            'subsubcategory': subsubcategory,
            'background': background
        })
