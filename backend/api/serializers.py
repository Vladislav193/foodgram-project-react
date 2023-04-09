from django.shortcuts import get_object_or_404
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
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = IngredientInRecipe
        fields = (
            "id",
            'name',
            'measurement_unit',
            "amount",
        )

    def get_measurement_unit(self, ingredient):
        measurement_unit = ingredient.ingredient.measurement_unit
        return measurement_unit

    def get_name(self, ingredient):
        name = ingredient.ingredient.name
        return name


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

    def get_is_favorited(self, obj):
        """Проверяет находится ли рецепт в избранном."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favourite.objects.filter(recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет находится ли рецепт в продуктовой корзине."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(recipe=obj,
                                           user=request.user).exists()


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

    def create(self, validated_data):
        """Создание рецепта."""
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            recipe.tags.set(tags)
        self.create_amount_ingredients(ingredients, recipe)
        return recipe

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


class FavouriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов"""
    id = serializers.CharField(
        read_only=True,
        source="recipe.id",
    )
    cooking_time = serializers.CharField(
        read_only=True,
        source="recipe.cooking_time",
    )
    image = serializers.CharField(
        read_only=True,
        source="recipe.image",
    )
    name = serializers.CharField(
        read_only=True,
        source="recipe.name",
    )

    def validate(self, data):
        """Валидатор избранных рецептов"""
        recipe = data["recipe"]
        user = data["user"]
        if user == recipe.author:
            raise serializers.ValidationError(
                "Вы не можете добавить свои рецепты в избранное"
            )
        if Favourite.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError(
                "Вы уже добавили рецепт в избранное")
        return data

    def create(self, validated_data):
        """Метод создания избранного"""
        favorite = Favourite.objects.create(**validated_data)
        favorite.save()
        return favorite

    class Meta:
        model = Favourite
        fields = ("id", "name", "image", "cooking_time")


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор продуктовой корзины."""
    id = serializers.CharField(
        read_only=True,
        source="recipe.id",
    )
    cooking_time = serializers.CharField(
        read_only=True,
        source="recipe.cooking_time",
    )
    image = serializers.CharField(
        read_only=True,
        source="recipe.image",
    )
    name = serializers.CharField(
        read_only=True,
        source="recipe.name",
    )

    class Meta:
        model = ShoppingCart
        fields = ("id", "name", "image", "cooking_time")
