from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_all_instances', views.get_all_instances, name='get_all_instances'),
    path('refresh_instances', views.refresh_instances, name='refresh_instances'),
    path('create_ec2_instance', views.create_ec2_instance, name='create_ec2_instance'),
    path('terminate_ec2_instance', views.terminate_ec2_instance, name='terminate_ec2_instance'),
    path('stop_ec2_instance', views.stop_ec2_instance, name='stop_ec2_instance')
]