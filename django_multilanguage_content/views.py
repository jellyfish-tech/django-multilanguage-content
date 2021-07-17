from operator import attrgetter
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .serializers import translated_model_serializers_fabric
from django.core.exceptions import ObjectDoesNotExist
from .store import models_store


def lang_param_in_global_lang(lang):
    return lang in models_store.global_langs


class TranslationViewSet(ModelViewSet):
    @action(
        methods=['get', 'post'],
        detail=True,
        url_path='translated/(?P<lang>[^/.]+)',
    )
    def retrieve_update_connected(self, request, pk=None, lang=None):
        if not lang_param_in_global_lang(lang):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            retrieved_model = self.get_queryset().get(pk=pk)
            serializer = translated_model_serializers_fabric(
                self.queryset.model, [lang], '__all__', True, False,
                return_serializer_class=True
            )
            connected_model = attrgetter(f'{retrieved_model.get_translate_model_name(lang)}')(retrieved_model)
            if request.method == 'GET':
                return Response(
                    serializer(connected_model).data
                )
            if request.method == 'POST':
                validating = serializer(connected_model, data=request.data)
                if validating.is_valid():
                    validating.save()
                    return Response(serializer(validating.validated_data).data)
                else:
                    return Response(validating.errors)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
