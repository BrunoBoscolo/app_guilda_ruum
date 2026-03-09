from django.test import TestCase
from django.urls import reverse
from .models import Guild, Building, Upgrade, GuildBuilding, GuildUpgrade
from rest_framework import status
from rest_framework.test import APIClient
import json

class UpgradeTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.guild = Guild.objects.create(name="Test Guild", funds=10000, level=5)
        self.building = Building.objects.create(
            name="Test Building", slug="test-building",
            description="A test", cost=1000, slots_required=1, min_level_required=1
        )
        self.upgrade1 = Upgrade.objects.create(
            name="Upgrade 1", description="Tier 1",
            tier=1, cost=500, required_building=self.building
        )
        self.upgrade2 = Upgrade.objects.create(
            name="Upgrade 2", description="Tier 2",
            tier=2, cost=1000, required_upgrade=self.upgrade1
        )
        # Guild constructs the base building
        GuildBuilding.objects.create(guild=self.guild, building=self.building)

    def test_upgrades_page_renders(self):
        url = reverse('construcoes_upgrades')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Building', str(response.content))
        self.assertIn('Upgrade 1', str(response.content))

    def test_purchase_upgrade_success(self):
        url = reverse('guild-purchase-upgrade', kwargs={'pk': self.guild.id})
        response = self.client.post(url, {'upgrade_id': self.upgrade1.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(GuildUpgrade.objects.filter(guild=self.guild, upgrade=self.upgrade1).exists())
        self.guild.refresh_from_db()
        self.assertEqual(self.guild.funds, 10000 - 500)

    def test_purchase_upgrade_failure_not_unlocked(self):
        # Upgrade 2 requires Upgrade 1. We don't have Upgrade 1 yet.
        url = reverse('guild-purchase-upgrade', kwargs={'pk': self.guild.id})
        response = self.client.post(url, {'upgrade_id': self.upgrade2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = json.loads(response.content)
        self.assertIn("Upgrade requisito não encontrado na guilda.", content['non_field_errors'][0])

    def test_purchase_upgrade_failure_insufficient_funds(self):
        self.guild.funds = 100
        self.guild.save()
        url = reverse('guild-purchase-upgrade', kwargs={'pk': self.guild.id})
        response = self.client.post(url, {'upgrade_id': self.upgrade1.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = json.loads(response.content)
        self.assertIn("Fundos insuficientes", content['non_field_errors'][0])

    def test_purchase_upgrade_failure_already_owned(self):
        # Purchase it once
        GuildUpgrade.objects.create(guild=self.guild, upgrade=self.upgrade1)

        url = reverse('guild-purchase-upgrade', kwargs={'pk': self.guild.id})
        response = self.client.post(url, {'upgrade_id': self.upgrade1.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = json.loads(response.content)
        self.assertIn("Este upgrade já foi adquirido.", content['non_field_errors'][0])

    def test_purchase_upgrade_failure_missing_building(self):
        # Create a new guild WITHOUT the building
        guild2 = Guild.objects.create(name="No Building Guild", funds=10000, level=5)
        url = reverse('guild-purchase-upgrade', kwargs={'pk': guild2.id})
        response = self.client.post(url, {'upgrade_id': self.upgrade1.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = json.loads(response.content)
        self.assertIn("Construção requisito não encontrada na guilda.", content['non_field_errors'][0])

    def test_purchase_upgrade_invalid_id(self):
        url = reverse('guild-purchase-upgrade', kwargs={'pk': self.guild.id})
        response = self.client.post(url, {'upgrade_id': 9999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = json.loads(response.content)
        self.assertIn("Upgrade not found.", str(content['upgrade_id']))

    def test_purchase_upgrade_missing_id(self):
        url = reverse('guild-purchase-upgrade', kwargs={'pk': self.guild.id})
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = json.loads(response.content)
        self.assertIn("required", str(content['upgrade_id']))
