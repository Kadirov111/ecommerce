from rest_framework import serializers
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    likes_count = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'thumbnail', 'category', 'average_rating', 'likes_count']


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = serializers.SerializerMethodField()
    average_rating = serializers.ReadOnlyField()
    reviews_count = serializers.ReadOnlyField()
    likes_count = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'images', 'category',
            'attributes', 'average_rating', 'reviews_count', 'likes_count',
            'is_liked', 'in_stock', 'created_at', 'updated_at'
        ]

    def get_images(self, obj):
        return obj.images_list

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ProductLike.objects.filter(user=request.user, product=obj).exists()
        return False


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['product', 'quantity', 'subtotal']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    items_count = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['items', 'total', 'items_count']


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price', 'subtotal']


class OrderListSerializer(serializers.ModelSerializer):
    items_count = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'created_at', 'status', 'total', 'items_count']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'created_at', 'updated_at', 'status',
            'shipping_address', 'notes', 'items', 'subtotal', 'shipping_fee',
            'total', 'tracking_number'
        ]


class PlaceOrderSerializer(serializers.Serializer):
    shipping_address = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)


class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id', read_only=True)
    name = serializers.CharField(source='user.first_name')

    class Meta:
        model = UserProfile
        fields = ['id', 'phone', 'name', 'email', 'default_shipping_address', 'date_joined']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
            instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'product_id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'product_id', 'user', 'created_at']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'name': obj.user.first_name or obj.user.username
        }


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

    def validate(self, data):
        user = self.context['request'].user
        product_id = self.context['product_id']

        if not OrderItem.objects.filter(
                order__user=user,
                product_id=product_id,
                order__status__in=['delivered', 'processing', 'shipped']
        ).exists():
            raise serializers.ValidationError("You can only review products you have purchased.")

        if Review.objects.filter(user=user, product_id=product_id).exists():
            raise serializers.ValidationError("You have already reviewed this product.")

        return data
