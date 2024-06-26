from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтр рецептов"""

    tags = filters.AllValuesMultipleFilter(field_name="tags__slug")
    author = filters.CharFilter(lookup_expr="exact")
    is_in_shopping_cart = filters.BooleanFilter(
        field_name="is_in_shopping_cart", method="filter"
    )
    is_favorited = filters.BooleanFilter(
        field_name="is_favorited", method="filter")

    def filter(self, queryset, name, value):
        """Метод фильтрации рецептов"""
        if name == "is_in_shopping_cart" and value:
            queryset = queryset.filter(
                shopping_list_recipe__user=self.request.user)
        if name == "is_favorited" and value:
            queryset = queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = (
            "author",
            "tags",
            "is_in_shopping_cart",
            "is_favorited",
        )


class IngredientFilter(filters.FilterSet):
    """Фильтр ингредиентов"""

    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
