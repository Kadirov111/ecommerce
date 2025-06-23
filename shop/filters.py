import django_filters
from django_filters import rest_framework as filters
from .models import Product
import json

class ProductFilter(filters.FilterSet):
    category = filters.NumberFilter(field_name='category__id')
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    attributes = filters.CharFilter(method='filter_attributes')

    class Meta:
        model = Product
        fields = ['category', 'min_price', 'max_price', 'attributes']

    def filter_attributes(self, queryset, name, value):
        try:
            attrs = json.loads(value)
            for key, val in attrs.items():
                queryset = queryset.filter(**{f'attributes__{key}': val})
            return queryset
        except (json.JSONDecodeError, TypeError):
            return queryset
