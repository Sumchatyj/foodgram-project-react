from rest_framework import filters


class RecipeFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        filter_params = {}
        author = request.query_params.get("author")
        if author is not None and author.isdigit():
            filter_params["author"] = author
        is_favorited = request.query_params.get("is_favorited")
        if is_favorited == "1":
            filter_params["favorite__user"] = request.user
        is_in_shopping_cart = request.query_params.get("is_in_shopping_cart")
        if is_in_shopping_cart == "1":
            filter_params["shopping_cart__user"] = request.user
        tags = request.query_params.getlist("tags")
        if len(tags) > 0:
            filter_params["tags__tag__slug__in"] = tags
        return queryset.filter(**filter_params).distinct()
