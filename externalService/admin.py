from django.contrib import admin

# admin.py
from .models import ExternalService
admin.site.register(ExternalService)
