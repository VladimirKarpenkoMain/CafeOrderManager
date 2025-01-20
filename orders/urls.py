from django.urls import path
import orders.views as views

app_name = 'orders'

urlpatterns = [
    path('', views.OrdersView.as_view(), name='order-list'),
    path('create/', views.CreateOrderView.as_view(), name='order-create'),
    path('change-status/<int:order_id>/', views.UpdateOrderView.as_view(), name='status-update'),
    path('delete-order/', views.DeleteFormView.as_view(), name='order-delete'),
]