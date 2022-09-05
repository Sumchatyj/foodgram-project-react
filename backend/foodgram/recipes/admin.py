from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
    TagRecipe,
)


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "measurement_unit",
    )
    list_filter = ("name",)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "count_favorite")
    list_filter = ("author", "name", "tags__tag")

    @admin.display(description="favorite")
    def count_favorite(self, obj):
        count = Favorite.objects.filter(recipe=obj).count()
        return count


class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(TagRecipe)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)
admin.site.register(IngredientRecipe)
