from rest_framework import serializers
from .models import Category, Product, Order, OrderItem
from .telegram_bot_in_drf import bot
from django.contrib.auth import get_user_model

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()  # Вложенная информация о товаре

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)  # Список товаров в заказе

    class Meta:
        model = Order
        fields = ['id', 'user', 'created', 'updated', 'paid', 'items']
        read_only_fields = ['user', 'created', 'updated']


class CreateOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class CreateOrderSerializer(serializers.ModelSerializer):
    items = CreateOrderItemSerializer(many=True)


    class Meta:
        model = Order
        fields = ['items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        order = Order.objects.create(user=user)
        chat_id = user.chat_id

        for item_data in items_data:
            product = item_data['product']
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=item_data['quantity']
            )


        bot.send_message(chat_id=chat_id, text='У вас новый заказ!')
        return order




