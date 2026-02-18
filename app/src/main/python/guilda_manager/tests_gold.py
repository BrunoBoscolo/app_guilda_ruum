from django.test import TestCase
from .models import Guild
from decimal import Decimal

class GoldManagementTestCase(TestCase):
    def setUp(self):
        # Create a guild with 100 gold and default cap (likely 1000 or similar based on level)
        self.guild = Guild.objects.create(name="Gold Guild", level=1, funds=Decimal('100.00'))
        # Base stats for level 1 usually have a cap. Let's assume it's reachable.

    def test_add_gold(self):
        initial_funds = self.guild.funds
        amount = 50.00

        response = self.client.post('/mestre/', {
            'action': 'manage_gold',
            'operation': 'add',
            'amount': amount
        })

        self.guild.refresh_from_db()
        self.assertEqual(self.guild.funds, initial_funds + Decimal(amount))
        # The success message might contain the exact string
        self.assertContains(response, '50.0 T$ adicionados')

    def test_add_gold_cap(self):
        # Cap depends on base stats. Let's force a huge amount.
        cap = self.guild.max_gold_cap
        amount = cap + 1000

        response = self.client.post('/mestre/', {
            'action': 'manage_gold',
            'operation': 'add',
            'amount': amount
        })

        self.guild.refresh_from_db()
        self.assertEqual(self.guild.funds, cap)
        self.assertContains(response, 'Limitado ao teto')

    def test_remove_gold(self):
        initial_funds = self.guild.funds
        amount = 50.00

        response = self.client.post('/mestre/', {
            'action': 'manage_gold',
            'operation': 'remove',
            'amount': amount
        })

        self.guild.refresh_from_db()
        self.assertEqual(self.guild.funds, initial_funds - Decimal(amount))
        self.assertContains(response, '50.0 T$ removidos')

    def test_remove_gold_floor(self):
        amount = 500.00 # More than 100

        response = self.client.post('/mestre/', {
            'action': 'manage_gold',
            'operation': 'remove',
            'amount': amount
        })

        self.guild.refresh_from_db()
        self.assertEqual(self.guild.funds, Decimal('0.00'))
        self.assertContains(response, 'Fundos zerados')

    def test_invalid_amount(self):
        initial_funds = self.guild.funds

        # Negative amount
        response = self.client.post('/mestre/', {
            'action': 'manage_gold',
            'operation': 'add',
            'amount': -10
        })

        self.guild.refresh_from_db()
        self.assertEqual(self.guild.funds, initial_funds)
        self.assertContains(response, 'O valor deve ser positivo')

        # Invalid numeric
        response = self.client.post('/mestre/', {
            'action': 'manage_gold',
            'operation': 'add',
            'amount': 'abc'
        })

        self.guild.refresh_from_db()
        self.assertEqual(self.guild.funds, initial_funds)
        self.assertContains(response, 'Valor inválido')
