import os

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from fpdf import FPDF
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from recipes.serializers import IngredientSerializer, TagSerializer
from users.models import Follower, User
from users.serializers import UserSerializer, UserSuccesfullSignUpSerializer

from .pagination import StandardResultsSetPagination
from .permissions import IsAuthorOrStaffOrReadOnly
from .serializers import (
    FollowerSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
)


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
            author = get_object_or_404(User, pk=kwargs.get("id"))
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
        if request.method == "DELETE":
            author = get_object_or_404(User, pk=kwargs.get("id"))
            if Follower.objects.filter(
                follower=request.user, author=author
            ).exists():
                Follower.objects.filter(
                    follower=request.user, author=author
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
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
    serializer_class = RecipeSerializer
    permission_classes = [
        IsAuthorOrStaffOrReadOnly,
    ]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        filter_params = {}
        author = self.request.query_params.get("author")
        if author is not None:
            filter_params["author"] = author
        is_favorited = self.request.query_params.get("is_favorited")
        if is_favorited == "1":
            filter_params["favorite__user"] = self.request.user
        is_in_shopping_cart = self.request.query_params.get(
            "is_in_shopping_cart"
        )
        if is_in_shopping_cart == "1":
            filter_params["shopping_cart__user"] = self.request.user
        tags = self.request.query_params.getlist("tags")
        if len(tags) > 0:
            filter_params["tags__tag__slug__in"] = tags
        queryset = Recipe.objects.filter(**filter_params).distinct()
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

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
        pdf.output(f"data/tmp_{request.user}.pdf", "F")
        response = FileResponse(open(f"data/tmp_{request.user}.pdf", "rb"))
        os.remove(f"data/tmp_{request.user}.pdf")
        return response


class ShoppingCartView(APIView):
    def post(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs.get("recipe_id"))
        serializer = RecipeShortSerializer(recipe)
        shopping_cart, status_obj = ShoppingCart.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if status_obj is True:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs.get("recipe_id"))
        instance = get_object_or_404(
            ShoppingCart, recipe=recipe, user=request.user
        )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteView(APIView):
    def post(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs.get("recipe_id"))
        serializer = RecipeShortSerializer(recipe)
        favorite, status_obj = Favorite.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if status_obj is True:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs.get("recipe_id"))
        instance = get_object_or_404(
            Favorite, recipe=recipe, user=request.user
        )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [
        AllowAny,
    ]

    def get_queryset(self):
        name = self.request.query_params.get("name")
        if name is not None:
            queryset = Ingredient.objects.filter(name__startswith=name.lower())
            return queryset
        else:
            queryset = Ingredient.objects.all()
            return queryset
