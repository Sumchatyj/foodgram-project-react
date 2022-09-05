from django.contrib.auth.models import AnonymousUser
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
    TagRecipe,
)
from recipes.serializers import IngredientRecipeSerializer
from users.models import User
from users.serializers import UserGetSerializer


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientRecipeSerializer(many=True)
    author = UserGetSerializer(default=serializers.CurrentUserDefault())
    is_favorited = serializers.SerializerMethodField(required=False)
    is_in_shopping_cart = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = ("id", "author")

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            TagRecipe.objects.create(recipe=recipe, tag=tag)
        for ingredient in ingredients:
            instance = Ingredient.objects.get(pk=ingredient["ingredient"])
            IngredientRecipe.objects.create(
                recipe=recipe, ingredient=instance, amount=ingredient["amount"]
            )
        return recipe

    def to_representation(self, instance):
        data = super(RecipeSerializer, self).to_representation(instance)
        data["tags"] = []
        data["ingredients"] = []
        tag_recipe_qs = instance.tags.all()
        ingredient_recipe_qs = instance.ingredients.all()
        for tag_recipe in tag_recipe_qs:
            tag = tag_recipe.tag
            tag_dict = {
                "id": tag.pk,
                "name": tag.name,
                "color": tag.color,
                "slug": tag.slug,
            }
            data["tags"].append(tag_dict)
        for ingredient_recipe in ingredient_recipe_qs:
            ingredient = ingredient_recipe.ingredient
            ingredient_dict = {
                "id": ingredient.pk,
                "name": ingredient.name,
                "measurement_unit": ingredient.measurement_unit,
                "amount": ingredient_recipe.amount,
            }
            data["ingredients"].append(ingredient_dict)
        return data

    def update(self, instance, validated_data):
        tags_data = validated_data.pop("tags")
        ingredients_data = validated_data.pop("ingredients")
        instance = super(RecipeSerializer, self).update(
            instance, validated_data
        )
        tag_id_list = []
        for tag_data in tags_data:
            tag_id_list.append(tag_data.pk)
        ingredients_id_list = []
        for ingredient_data in ingredients_data:
            ingredients_id_list.append(ingredient_data["ingredient"])
        for tag in instance.tags.all():
            if tag.tag.pk not in tag_id_list:
                tag_recipe_obj = TagRecipe.objects.get(
                    tag=tag.tag, recipe=instance
                )
                tag_recipe_obj.delete()
        for tag in tags_data:
            tag, status = TagRecipe.objects.get_or_create(
                tag=tag, recipe=instance
            )
        for ingredient in instance.ingredients.all():
            if ingredient.ingredient.pk not in ingredients_id_list:
                ingredient_recipe_obj = IngredientRecipe.objects.get(
                    ingredient=ingredient.ingredient, recipe=instance
                )
                ingredient_recipe_obj.delete()
        for ingredient in ingredients_data:
            ingredient_obj = Ingredient.objects.get(
                pk=ingredient["ingredient"]
            )
            (
                ingredient_recipe_obj,
                status,
            ) = IngredientRecipe.objects.get_or_create(
                ingredient=ingredient_obj,
                recipe=instance,
                amount=ingredient["amount"],
            )
        return instance

    def get_is_favorited(self, instance):
        user = self.context["request"].user
        if (
            not isinstance(user, AnonymousUser)
            and Favorite.objects.filter(user=user, recipe=instance).exists()
        ):
            return True
        else:
            return False

    def get_is_in_shopping_cart(self, instance):
        user = self.context["request"].user
        if (
            not isinstance(user, AnonymousUser)
            and ShoppingCart.objects.filter(
                user=user, recipe=instance
            ).exists()
        ):
            return True
        else:
            return False


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class FollowerSerializer(UserGetSerializer):
    recipes_count = serializers.SerializerMethodField(required=False)
    recipes = RecipeShortSerializer(many=True, read_only=True)

    class Meta:
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        model = User

    def get_recipes_count(self, instance):
        count = Recipe.objects.filter(author=instance).count()
        return count

    def to_representation(self, instance):
        data = super(FollowerSerializer, self).to_representation(instance)
        recipes_limit = self.context["request"].query_params.get(
            "recipes_limit"
        )
        if recipes_limit is not None:
            data["recipes"] = data["recipes"][: int(recipes_limit)]
        return data
