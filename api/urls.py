from django.urls import path

from api.views import (
    OrderListCreateView, UpdateOrderStatusView, DeleteOrderView, ItemListView, RevenueListView, UpdateRevenueView,
)

app_name = 'api'

urlpatterns = [

    path('orders/', OrderListCreateView.as_view(), name='order-list'),

    path('orders/<int:order_id>/status/', UpdateOrderStatusView.as_view(), name='order-update-status'),

    path('orders/<int:order_id>/', DeleteOrderView.as_view(), name='order-delete'),
    path('items/', ItemListView.as_view(), name='item-list'),

    path('revenues/', RevenueListView.as_view(), name='revenues-list'),
    path('revenue/update/', UpdateRevenueView.as_view(), name='revenue-update'),

]