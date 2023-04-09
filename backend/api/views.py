from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated)
from rest_framework.response import Response

from recipes.models import (Favourite, Ingredient, Recipe,
                            IngredientInRecipe, ShoppingCart, Tag)
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipesReadSerializer,
                          RecipesCreateSerializer, FavouriteSerializer,
                          TagSerializer)


class IngredientsViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели ингридиента."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = IngredientFilter
    search_fields = ("^name",)
    pagination_class = None


class TagsViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели тега."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели рецепта."""
    queryset = Recipe.objects.all().order_by("-id")
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipesReadSerializer
        return RecipesCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, model, user, pk):
        """Метод для добавления рецепта."""
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({
                'errors': 'Рецепт уже добавлен в список!'
            }, status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = FavouriteSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, model, user, pk):
        """Метод для удаления рецепта."""
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({
            'errors': 'Рецепт уже удален'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="favorite",
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        """Метод для добавления/удаления из избранного."""
        if request.method == 'POST':
            return self.create(Favourite, request.user, pk)
        else:
            return self.delete_recipe(Favourite, request.user, pk)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="shopping_cart",
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        """Метод для добавления/удаления из продуктовой корзины."""
        if request.method == 'POST':
            return self.create(ShoppingCart, request.user, pk)
        else:
            return self.delete_recipe(ShoppingCart, request.user, pk)

    @action(
        detail=False,
        methods=["GET"],
        url_path="download_shopping_cart",
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        """Получение и скачивание корзины."""
        user = request.user
        ingredients_list = (
            IngredientInRecipe.objects.filter(
                recipes__shopping_list_recipe__user=user
            )
            .values(
                'ingredient__name',
                'ingredient__measurement_unit'
            )
            .annotate(ingredient_total=Sum('amount'))
        )
        ingredients_list = ingredients_list.order_by('ingredient__name')
        shopping_list = 'Список покупок: \n'
        for ingredient in ingredients_list:
            shopping_list += (
                f'{ingredient["ingredient__name"]} - '
                f'{ingredient["ingredient_total"]} '
                f'({ingredient["ingredient__measurement_unit"]}) \n'
            )
        response = HttpResponse(
            shopping_list, content_type='text/plain; charset=utf8'
        )
        filename = "shopping_list.txt"
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
