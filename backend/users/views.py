from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet

from rest_framework.decorators import action
from rest_framework.permissions import  IsAuthenticated
from rest_framework.response import Response

from users.models import Follow, User
from users.serializers import CustomUserSerializer, FollowSerializer


class UserViewSet(UserViewSet):
    """Вьюсет для модели пользователя."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

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
        methods=["POST", "DELETE"],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        """Метод для подписки/отписки."""
        author = get_object_or_404(User, id=id)
        if request.method == "POST":
            if request.user.id == author.id:
                raise ValidationError(
                    "Вы не можете подписаться сами на себя!"
                )
            else:
                serializer = FollowSerializer(
                    Follow.objects.create(user=request.user, author=author),
                    context={"request": request},
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
        elif request.method == "DELETE":
            if Follow.objects.filter(
                user=request.user, author=author
            ).exists():
                Follow.objects.filter(
                    user=request.user, author=author
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"errors": "Автор отсутсвует в списке подписок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
