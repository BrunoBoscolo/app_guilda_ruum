from django.test import TestCase, Client
from django.urls import reverse
from django.core.management import call_command
from guilda_manager.models import Guild, Building, GuildBuilding
from decimal import Decimal

class ConstrucoesTest(TestCase):
    def setUp(self):
        # Run the setup command
        call_command('setup_mock_data', stdout=open('/dev/null', 'w'))
        self.client = Client()
        self.guild = Guild.objects.first()

    def test_mock_data_buildings(self):
        """Verify mock data created buildings correctly."""
        self.assertTrue(Building.objects.filter(slug='a-grande-forja').exists())
        self.assertTrue(Building.objects.filter(slug='laboratorio-de-alquimia').exists())

        # Check pre-built buildings
        self.assertTrue(GuildBuilding.objects.filter(guild=self.guild, building__slug='a-grande-forja').exists())

    def test_hub_view(self):
        """Test the main hub view."""
        response = self.client.get(reverse('construcoes'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'guilda_manager/construcoes_hub.html')

    def test_projetos_view(self):
        """Test the projects view."""
        response = self.client.get(reverse('construcoes_projetos'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'guilda_manager/construcoes_projetos.html')

        # Check context
        buildings = response.context['buildings']
        self.assertIn('torre-de-vigia', [b.slug for b in buildings])
        self.assertNotIn('a-grande-forja', [b.slug for b in buildings]) # Already built

    def test_infra_view(self):
        """Test the infra view."""
        response = self.client.get(reverse('construcoes_infra'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'guilda_manager/construcoes_infra.html')

        # Check context
        constructions = response.context['constructions']
        self.assertTrue(any(c.building.slug == 'a-grande-forja' for c in constructions))

    def test_construct_building_api(self):
        """Test constructing a building via API."""
        # Give enough funds
        self.guild.funds = Decimal('100000.00')
        self.guild.save()

        # Try to build Torre de Vigia
        response = self.client.post(
            f'/api/guilds/{self.guild.id}/construct_building/',
            data={'building_slug': 'torre-de-vigia'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        # Verify it's built
        self.assertTrue(GuildBuilding.objects.filter(guild=self.guild, building__slug='torre-de-vigia').exists())
