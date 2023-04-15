from django.core.exceptions import ValidationError
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
from users.models import Follow, User
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (CustomUserSerializer, FollowSerializer, IngredientSerializer, RecipesReadSerializer,
                          RecipesCreateSerializer, FavouriteSerializer,
                          TagSerializer, ShoppingCartSerializer)
from djoser.views import UserViewSet


class UserViewSet(UserViewSet):
    """Вьюсет для модели пользователя."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
 
    def get_serializer_context(self):
        """Дополнительный контекст, предоставляемый классу serializer."""
        follow = set(
            Follow.objects.filter(user_id=self.request.user.id).values_list('author_id', flat=True))
        data = {
            'follow': follow,
             }
        return data

    @action(
        methods=["GET"],
        detail=False,
        permission_classes=(IsAuthenticated,)
    )

    def subscriptions(self, request):
        """Метод для просмотра подписок на авторов."""
        user = self.request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        permission_classes=[IsAuthenticated]
    )

    def subscribe(self, request, **kwargs):
        user = request.user
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
 
        if request.method == 'POST':
            serializer = FollowSerializer(
                author,
                data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
 
        if request.method == 'DELETE':
            subscription = get_object_or_404(
                Follow,
                user=user,
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


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
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPageNumberPagination

    def get_serializer_context(self):
        """Дополнительный контекст, предоставляемый классу serializer."""
        subscription = set(
            Favourite.objects.filter(user_id=self.request.user).values_list('recipe_id', flat=True))
        shopping_cart = set(
            ShoppingCart.objects.filter(user_id=self.request.user).values_list('recipe_id', flat=True))
        data = {
            'subscriptions': subscription,
            'shopping_cart': shopping_cart
             }
        return data

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipesReadSerializer
        return RecipesCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add(self, request, pk, model, modelserializer):
        # надеюсь я правильно понял твои рекомендации)))
        if request.method != 'POST':
            action_model = get_object_or_404(
                model,
                user=request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            )
            self.perform_destroy(action_model)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = modelserializer(
            data={
                'user': request.user.id,
                'recipe': get_object_or_404(Recipe, pk=pk).pk
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=["POST", "DELETE"],
            detail=True,
            permission_classes=[IsAuthenticated]
            )
    def favorite(self, request, pk):
        return self.add(request, pk, Favourite, FavouriteSerializer)

    @action(
        detail=True,
        methods=["POST", "DELETE"],
        url_path="shopping_cart",
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        """Метод для добавления/удаления из продуктовой корзины."""
        return self.add(request, pk, ShoppingCart, ShoppingCartSerializer)

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
