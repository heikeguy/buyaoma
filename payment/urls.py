from django.conf.urls import url
from . import views
from django.contrib.staticfiles.urls  import staticfiles_urlpatterns
from django.contrib import staticfiles

urlpatterns = [
    url(r'^process/(.+)/$', views.payment_process
        , name='process'),
    url(r'^done/$', views.payment_done
        , name='done'),
    url(r'^canceled/$', views.payment_canceled
        , name='canceled'),
]

urlpatterns += staticfiles_urlpatterns()