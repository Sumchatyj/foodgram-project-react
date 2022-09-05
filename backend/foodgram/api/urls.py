from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewset,
    FavoriteView,
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartView,
    TagViewSet,
)

router = DefaultRouter()
router.register(r"users", CustomUserViewset, "users")
router.register(r"tags", TagViewSet, "tags")
router.register(r"recipes", RecipeViewSet, "recipes")
router.register(r"ingredients", IngredientViewSet, "ingredients")


urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path(
        "recipes/<int:recipe_id>/shopping_cart/",
        ShoppingCartView.as_view(),
        name="shopping_cart",
    ),
    path(
        "recipes/<int:recipe_id>/favorite/",
        FavoriteView.as_view(),
        name="favorite",
    ),
]
