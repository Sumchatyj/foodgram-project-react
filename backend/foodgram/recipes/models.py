from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    color = ColorField(unique=True)
    slug = models.CharField(max_length=32, unique=True)


class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=32)


class Recipe(models.Model):
    author = models.ForeignKey(
        User, related_name="recipes", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    image = models.ImageField()
    text = models.TextField()
    cooking_time = models.IntegerField(validators=[MinValueValidator(1)])
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pub_date"]


class TagRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, related_name="tags", on_delete=models.CASCADE
    )
    tag = models.ForeignKey(
        Tag, related_name="recipes", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("recipe", "tag")


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, related_name="ingredients", on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient, related_name="recipes", on_delete=models.CASCADE
    )
    amount = models.FloatField(max_length=8)


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe, related_name="shopping_cart", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="shopping_cart", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("recipe", "user")


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe, related_name="favorite", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, related_name="favorite", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("recipe", "user")
