from django.urls import path
from . import views

urlpatterns = [
    # Products
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:id>/like/', views.like_product, name='like-product'),
    path('products/<int:id>/review/', views.create_review, name='create-review'),
    path('cart/', views.view_cart, name='view-cart'),
    path('cart/', views.add_to_cart, name='add-to-cart'),
    path('cart/<int:product_id>/', views.remove_from_cart, name='remove-from-cart'),
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/', views.place_order, name='place-order'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('profile/', views.get_profile, name='get-profile'),
    path('profile/', views.update_profile, name='update-profile'),
]
