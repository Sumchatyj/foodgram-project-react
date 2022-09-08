from django.contrib.auth.models import AnonymousUser
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.models import Follower, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        model = User


class UserSuccesfullSignUpSerializer(UserSerializer):
    class Meta:
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
        )
        model = User


class UserGetSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(required=False)

    class Meta:
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )
        model = User

    def get_is_subscribed(self, instance):
        user = self.context["request"].user
        author = instance
        if (
            not isinstance(user, AnonymousUser)
            and Follower.objects.filter(author=author, follower=user).exists()
        ):
            return True
        else:
            return False


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Tag


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="ingredient")

    class Meta:
        fields = ("id", "amount")
        model = IngredientRecipe


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Ingredient


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
        return Recipe.objects.filter(author=instance).count()

    def to_representation(self, instance):
        data = super(FollowerSerializer, self).to_representation(instance)
        recipes_limit = self.context["request"].query_params.get(
            "recipes_limit"
        )
        if recipes_limit is not None:
            data["recipes"] = data["recipes"][: int(recipes_limit)]
        return data
