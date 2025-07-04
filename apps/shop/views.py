from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import *
from .serializers import *
from .filters import ProductFilter
from .utils import create_success_response, create_error_response


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(in_stock=True)
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'created_at', 'title']
    ordering = ['-created_at']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return create_success_response(
                data=paginated_response.data['results'],
                meta={'pagination': {
                    'total': paginated_response.data['count'],
                    'count': len(paginated_response.data['results']),
                    'per_page': self.paginator.page_size,
                    'current_page': self.paginator.page.number,
                    'total_pages': self.paginator.page.paginator.num_pages,
                    'links': {
                        'next': paginated_response.data['next'],
                        'prev': paginated_response.data['previous']
                    }
                }}
            )

        serializer = self.get_serializer(queryset, many=True)
        return create_success_response(data=serializer.data)


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={'request': request})
            return create_success_response(data=serializer.data)
        except Product.DoesNotExist:
            return create_error_response(
                code="PRODUCT_NOT_FOUND",
                message="Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_product(request, id):
    try:
        product = get_object_or_404(Product, id=id)
        like, created = ProductLike.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        return create_success_response(data={
            'liked': liked,
            'likes_count': product.likes_count
        })
    except Product.DoesNotExist:
        return create_error_response(
            code="PRODUCT_NOT_FOUND",
            message="Product not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart)
    return create_success_response(data=serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    serializer = AddToCartSerializer(data=request.data)
    if serializer.is_valid():
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        try:
            product = Product.objects.get(id=product_id, in_stock=True)
        except Product.DoesNotExist:
            return create_error_response(
                code="PRODUCT_NOT_FOUND",
                message="Product not found or out of stock",
                status_code=status.HTTP_404_NOT_FOUND
            )

        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        cart_serializer = CartSerializer(cart)
        return create_success_response(data=cart_serializer.data)

    return create_error_response(
        code="INVALID_REQUEST",
        message="The provided data is invalid",
        details=serializer.errors
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, product_id):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        cart_item.delete()

        cart_serializer = CartSerializer(cart)
        return create_success_response(data=cart_serializer.data)

    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        return create_error_response(
            code="PRODUCT_NOT_FOUND",
            message="Product not found in cart",
            status_code=status.HTTP_404_NOT_FOUND
        )


class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return create_success_response(
                data=paginated_response.data['results'],
                meta={'pagination': {
                    'total': paginated_response.data['count'],
                    'count': len(paginated_response.data['results']),
                    'per_page': self.paginator.page_size,
                    'current_page': self.paginator.page.number,
                    'total_pages': self.paginator.page.paginator.num_pages,
                    'links': {
                        'next': paginated_response.data['next'],
                        'prev': paginated_response.data['previous']
                    }
                }}
            )

        serializer = self.get_serializer(queryset, many=True)
        return create_success_response(data=serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order(request):
    serializer = PlaceOrderSerializer(data=request.data)
    if serializer.is_valid():
        try:
            cart = Cart.objects.get(user=request.user)
            if not cart.items.exists():
                return create_error_response(
                    code="EMPTY_CART",
                    message="Cart is empty",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Create order
            order = Order.objects.create(
                user=request.user,
                shipping_address=serializer.validated_data['shipping_address'],
                notes=serializer.validated_data.get('notes', ''),
                subtotal=cart.total,
                total=cart.total + 5.00,  # Add shipping fee
                status='processing'
            )

            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    subtotal=cart_item.subtotal
                )

            # Clear cart
            cart.items.all().delete()

            order_serializer = OrderDetailSerializer(order)
            return create_success_response(
                data=order_serializer.data,
                status_code=status.HTTP_201_CREATED
            )

        except Cart.DoesNotExist:
            return create_error_response(
                code="EMPTY_CART",
                message="Cart is empty",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    return create_error_response(
        code="INVALID_REQUEST",
        message="The provided data is invalid",
        details=serializer.errors
    )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return create_success_response(data=serializer.data)
        except Order.DoesNotExist:
            return create_error_response(
                code="ORDER_NOT_FOUND",
                message="Order not found",
                status_code=status.HTTP_404_NOT_FOUND
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile)
        return create_success_response(data=serializer.data)
    except UserProfile.DoesNotExist:
        return create_error_response(
            code="PROFILE_NOT_FOUND",
            message="Profile not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return create_success_response(data=serializer.data)

        return create_error_response(
            code="INVALID_REQUEST",
            message="The provided data is invalid",
            details=serializer.errors
        )
    except UserProfile.DoesNotExist:
        return create_error_response(
            code="PROFILE_NOT_FOUND",
            message="Profile not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, id):
    try:
        product = get_object_or_404(Product, id=id)
        serializer = CreateReviewSerializer(
            data=request.data,
            context={'request': request, 'product_id': id}
        )

        if serializer.is_valid():
            review = serializer.save(user=request.user, product=product)
            review_serializer = ReviewSerializer(review)
            return create_success_response(
                data=review_serializer.data,
                status_code=status.HTTP_201_CREATED
            )

        return create_error_response(
            code="INVALID_REQUEST",
            message="The provided data is invalid",
            details=serializer.errors
        )

    except Product.DoesNotExist:
        return create_error_response(
            code="PRODUCT_NOT_FOUND",
            message="Product not found",
            status_code=status.HTTP_404_NOT_FOUND
        )