from django.urls import path
import revenue.views as views

app_name = 'revenue'

urlpatterns = [
    path('', views.RevenueView.as_view(), name='revenue-data'),
    path('update-revenue/', views.CreateRevenueView.as_view(), name='revenue-create'),
]