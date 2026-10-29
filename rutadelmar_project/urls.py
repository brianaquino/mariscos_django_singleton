from django.urls import path, include
# from django.contrib import admin  <--- ELIMINAR O COMENTAR

urlpatterns = [
    # path('admin/', admin.site.urls), <--- ELIMINAR O COMENTAR
    path('', include('logistica_app.urls')),
]