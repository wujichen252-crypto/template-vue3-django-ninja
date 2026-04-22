"""URL Configuration."""
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from apps.users.api import router as user_router
from core.exceptions import register_exception_handlers

api = NinjaAPI(
    title="Template API",
    version="1.0.0",
    description="Django-Ninja 全栈模板接口",
    docs_url="/docs/",
    openapi_url="/openapi.json"
)

register_exception_handlers(api)

api.add_router("/api/v1", user_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api.urls),
]
