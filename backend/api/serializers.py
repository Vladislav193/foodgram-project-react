from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favourite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.serializers import CustomUserSerializer
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели тегов."""
    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
            "color",
            "slug",
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингридиентов."""
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientsRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингридиентов в рецепте"""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(required=True)
    name = serializers.ReadOnlyField(
        source="ingredient.name"
        )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
        )

    class Meta:
        model = IngredientInRecipe
        fields = (
            "id",
            'name',
            'measurement_unit',
            "amount",
        )


class RecipesReadSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов (просмотр)."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientsRecipeSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_user(self):
        return self.context["request"].user

    def get_is_subscribed(self, obj):
        return obj.id in self.context['subscriptions']

    def get_is_in_shopping_cart(self, obj):
        return obj.id in self.context['shopping_cart']


class RecipesCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов (создание)."""
    author = CustomUserSerializer(read_only=True, required=False)
    ingredients = IngredientsRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def create_amount_ingredients(self, ingredients, recipe):
        """Создание ингредиентов в рецепте."""
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient.objects.filter(id=ingredient['id'])[:1]
            )
            ing, _ = IngredientInRecipe.objects.get_or_create(
                ingredient=current_ingredient,
                amount=ingredient["amount"],
            )
            recipe.ingredients.add(ing.id)

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта."""
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            recipe.tags.set(tags)
        self.create_amount_ingredients(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        """Обновление рецепта."""
        if "ingredients" in validated_data:
            ingredients = validated_data.pop("ingredients")
            recipe.ingredients.clear()
            self.create_amount_ingredients(ingredients, recipe)
        if "tags" in validated_data:
            tags_data = validated_data.pop("tags")
            recipe.tags.set(tags_data)
        return super().update(recipe, validated_data)

    def to_representation(self, recipe):
        serializer = RecipesReadSerializer(recipe, context=self.context)
        return serializer.data


class ShortRecipe(serializers.ModelSerializer):
    """Поля ."""
    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = Recipe


class FavouriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов"""
    class Meta:
        fields = ('user', 'recipe')
        model = Favourite

    def validate(self, data):
        request = self.context['request']
        if not request or request.user.is_anonymous:
            return False
        if Favourite.objects.filter(
            user=request.user, recipe=data.get('recipe')
        ).exists():
            raise serializers.ValidationError(
                {'Favorite_exists_error': 'Рецепт уже в избранном.'}
            )
        return data

    def to_representation(self, instance):
        return ShortRecipe(
            instance.recipe,
            context={'request': self.context['request']}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор продуктовой корзины."""
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        request = self.context['request']
        if not request or request.user.is_anonymous:
            return False
        if ShoppingCart.objects.filter(
            user=request.user, recipe=data.get('recipe')
        ).exists():
            raise serializers.ValidationError(
                {'Shoppingсart_exists_error': 'Рецепт уже находится в корзине'}
            )
        return data

    def to_representation(self, instance):
        return ShortRecipe(
            instance.recipe,
            context={'request': self.context['request']}
        ).data
