from django.urls import path
from . import views

urlpatterns = [
    path('upload', views.upload_file),
    path('', views.upload_file)
]

