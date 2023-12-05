from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from utils.exceptions import  success

class ModelViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   GenericViewSet):
   
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = success(response.data)
        return response
        


    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        response.data = success(response.data)
        return response


    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = success(response.data)
        return response


    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        response.data = success(response.data)
        return response


    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data = success(response.data)
        return response


        