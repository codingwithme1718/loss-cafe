from django.urls import path
from .views import search_subsubcategory, MenuView, SubCategoryListView, SubSubCategoryListView, SubSubSubCategoryListView

urlpatterns = [
    path('', MenuView.as_view(), name='category_list'),  # Use as_view() here
    path('search/', search_subsubcategory, name='search_subsubcategory'),
    path('subcategory/<int:category_id>/', SubCategoryListView.as_view(), name='subcategory-list'),  # Use as_view() here
    path('subcategory/<int:subcategory_id>/subsubcategory/', SubSubCategoryListView.as_view(), name='subsubcategory-list'),
    path('subcategory/<int:subcategory_id>/subsubcategory/<int:subsubcategory_id>', SubSubSubCategoryListView.as_view(), name='subsubsubcategory-list'),
]
