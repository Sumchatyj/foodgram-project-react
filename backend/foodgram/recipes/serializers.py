from rest_framework import serializers

from .models import Ingredient, IngredientRecipe, Tag


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
