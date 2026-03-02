from django.test import TestCase
from rest_framework import serializers
from decimal import Decimal
from unittest.mock import MagicMock
from .serializers import BuildConstructionSerializer
from .models import Building, Guild

class BuildConstructionSerializerTest(TestCase):
    def setUp(self):
        self.guild = MagicMock(spec=Guild)
        self.guild.level = 2
        self.guild.funds = Decimal('1000.00')
        self.guild.available_building_slots = 2

        self.building = MagicMock(spec=Building)
        self.building.slug = 'forge'
        self.building.min_level_required = 1
        self.building.cost = Decimal('500.00')
        self.building.slots_required = 1

        self.data = {'building_slug': self.building}

    def test_validate_success(self):
        """Test successful validation when all requirements are met."""
        serializer = BuildConstructionSerializer(context={'guild': self.guild})
        validated_data = serializer.validate(self.data)
        self.assertEqual(validated_data, self.data)

    def test_validate_missing_guild_context(self):
        """Test validation failure when guild is missing from context."""
        serializer = BuildConstructionSerializer(context={})
        with self.assertRaises(serializers.ValidationError) as cm:
            serializer.validate(self.data)
        self.assertIn("Guilda não fornecida no contexto.", str(cm.exception))

    def test_validate_insufficient_level(self):
        """Test validation failure when guild level is insufficient."""
        self.building.min_level_required = 5
        serializer = BuildConstructionSerializer(context={'guild': self.guild})
        with self.assertRaises(serializers.ValidationError) as cm:
            serializer.validate(self.data)
        self.assertIn("Nível da guilda insuficiente.", str(cm.exception))

    def test_validate_insufficient_funds(self):
        """Test validation failure when guild funds are insufficient."""
        self.building.cost = Decimal('2000.00')
        serializer = BuildConstructionSerializer(context={'guild': self.guild})
        with self.assertRaises(serializers.ValidationError) as cm:
            serializer.validate(self.data)
        self.assertIn("Fundos insuficientes", str(cm.exception))

    def test_validate_insufficient_slots(self):
        """Test validation failure when available building slots are insufficient."""
        self.building.slots_required = 5
        serializer = BuildConstructionSerializer(context={'guild': self.guild})
        with self.assertRaises(serializers.ValidationError) as cm:
            serializer.validate(self.data)
        self.assertIn("Espaço insuficiente na sede", str(cm.exception))
