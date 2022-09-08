import os

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from fpdf import FPDF
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag, TagRecipe)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from users.models import Follower, User

from .filters import RecipeFilterBackend
from .pagination import StandardResultsSetPagination
from .permissions import IsAuthorOrStaffOrReadOnly
from .serializers import (FollowerSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeShortSerializer,
                          TagSerializer, UserSerializer,
                          UserSuccesfullSignUpSerializer)


class CustomUserViewset(UserViewSet):
    pagination_class = StandardResultsSetPagination

    def create(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        object = User.objects.create_user(**serializer.data)
        headers = self.get_success_headers(serializer.data)
        response_serializer = UserSuccesfullSignUpSerializer(object)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(
        [
            "get",
        ],
        detail=False,
    )
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(["post", "delete"], detail=True)
    def subscribe(self, request, *args, **kwargs):
        if request.method == "POST":
            pk = kwargs.get("id")
            if pk is not None and str(pk).isdigit():
                author = get_object_or_404(User, pk=int(pk))
                if author == request.user:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                follower, status_obj = Follower.objects.get_or_create(
                    follower=request.user, author=author
                )
                if status_obj is False:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                else:
                    contex = {"request": request}
                    serializer = FollowerSerializer(author, context=contex)
                    headers = self.get_success_headers(serializer.data)
                    return Response(
                        serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers,
                    )
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            pk = kwargs.get("id")
            if pk is not None and str(pk).isdigit():
                author = get_object_or_404(User, pk=int(pk))
                if Follower.objects.filter(
                    follower=request.user, author=author
                ).delete():
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        [
            "get",
        ],
        detail=False,
    )
    def subscriptions(self, request, *args, **kwargs):
        follower_qs = Follower.objects.filter(follower=request.user)
        queryset = User.objects.filter(author__in=follower_qs)
        contex = {"request": request}
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FollowerSerializer(page, context=contex, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = FollowerSerializer(queryset, context=contex, many=True)
        return Response(serializer.data)


class TagViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [
        AllowAny,
    ]


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [
        IsAuthorOrStaffOrReadOnly,
    ]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        RecipeFilterBackend,
    ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ingredients = serializer.validated_data.pop("ingredients")
        tags = serializer.validated_data.pop("tags")
        recipe = serializer.save(author=self.request.user)
        TagRecipe.objects.bulk_create(
            [TagRecipe(recipe=recipe, tag=tag) for tag in tags]
        )
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(
                    recipe=recipe,
                    ingredient=Ingredient.objects.get(
                        pk=ingredient["ingredient"]
                    ),
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients
            ]
        )
        serializer_created = self.get_serializer(recipe)
        headers = self.get_success_headers(serializer_created.data)
        return Response(
            serializer_created.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        ingredients_data = serializer.validated_data.pop("ingredients")
        tags_data = serializer.validated_data.pop("tags")
        recipe = serializer.save()
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

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}
        serializer_updated = self.get_serializer(recipe)
        return Response(serializer_updated.data)

    @action(
        detail=False,
        methods=[
            "get",
        ],
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font(
            "DejaVu", "", "api/fonts/DejaVuSerifCondensed.ttf", uni=True
        )
        pdf.set_font("DejaVu", "", 16)
        pdf.cell(200, 10, txt="Ваш список покупок:", ln=1, align="C")
        shopping_cart_qs = ShoppingCart.objects.filter(user=request.user)
        result = []
        for item in shopping_cart_qs:
            ingredients = item.recipe.ingredients.all()
            for ingredient in ingredients:
                full_ingredient = (
                    ingredient.ingredient.name,
                    ingredient.ingredient.measurement_unit,
                    ingredient.amount,
                )
                result.append(full_ingredient)
        if len(result) > 0:
            pdf.set_font("DejaVu", "", 14)
            result.sort()
            amount = result[0][2]
            for i in range(1, len(result)):
                if result[i][0] == result[i - 1][0]:
                    amount += result[i][2]
                    if i == len(result) - 1:
                        pdf.cell(
                            0,
                            10,
                            txt=f"{result[i][0]} ({result[i][1]}) - {amount}",
                            ln=1,
                            align="L",
                        )
                else:
                    pdf.cell(
                        0,
                        10,
                        txt=f"{result[i-1][0]} ({result[i-1][1]}) - {amount}",
                        ln=1,
                        align="L",
                    )
                    amount = result[i][2]
        else:
            pdf.cell(
                0,
                10,
                txt="Вы ещё не добавили рецепты в список покупок :(",
                ln=1,
                align="L",
            )
        pdf.output(f"data/tmp_{request.user}.pdf", "F")
        response = FileResponse(open(f"data/tmp_{request.user}.pdf", "rb"))
        os.remove(f"data/tmp_{request.user}.pdf")
        return response


class ShoppingCartView(APIView):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("recipe_id")
        if pk is not None and str(pk).isdigit():
            recipe = get_object_or_404(Recipe, pk=int(pk))
            serializer = RecipeShortSerializer(recipe)
            shopping_cart, status_obj = ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if status_obj is True:
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get("recipe_id")
        if pk is not None and str(pk).isdigit():
            recipe = get_object_or_404(Recipe, pk=int(pk))
            instance = get_object_or_404(
                ShoppingCart, recipe=recipe, user=request.user
            )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class FavoriteView(APIView):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("recipe_id")
        if pk is not None and str(pk).isdigit():
            recipe = get_object_or_404(Recipe, pk=int(pk))
            serializer = RecipeShortSerializer(recipe)
            favorite, status_obj = Favorite.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if status_obj is True:
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get("recipe_id")
        if pk is not None and str(pk).isdigit():
            recipe = get_object_or_404(Recipe, pk=int(pk))
            instance = get_object_or_404(
                Favorite, recipe=recipe, user=request.user
            )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class IngredientViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [
        AllowAny,
    ]

    def get_queryset(self):
        name = self.request.query_params.get("name")
        if name is not None:
            return Ingredient.objects.filter(name__startswith=name.lower())
        else:
            return Ingredient.objects.all()
