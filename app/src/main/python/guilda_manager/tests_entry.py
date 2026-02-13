from django.test import TestCase, Client
from django.urls import reverse
from .models import Guild

class EntryPortalTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_root_redirects_to_entry_portal_when_no_guild(self):
        # No guild exists
        response = self.client.get(reverse('root'))
        self.assertRedirects(response, reverse('entry_portal'))

    def test_root_redirects_to_sede_when_guild_exists(self):
        Guild.objects.create(name="Test Guild", code="TEST-1234")
        response = self.client.get(reverse('root'))
        self.assertRedirects(response, reverse('sede'))

    def test_create_guild(self):
        response = self.client.post(reverse('create_guild'), {
            'name': 'New Guild',
            'emblem': 'swords',
            'legal_status': 'INDEPENDENT',
            'moral_alignment': 'HUMANITARIAN',
            'motto': 'We are the best'
        })
        self.assertRedirects(response, reverse('sede'))
        self.assertTrue(Guild.objects.filter(name='New Guild').exists())
        guild = Guild.objects.get(name='New Guild')
        self.assertIsNotNone(guild.code)

    def test_sync_guild_valid_code(self):
        # Simulate valid code
        response = self.client.post(reverse('sync_guild'), {
            'code': 'ABC-1234'
        })
        self.assertRedirects(response, reverse('sede'))
        self.assertTrue(Guild.objects.filter(code='ABC-1234').exists())

    def test_sync_guild_invalid_code(self):
        response = self.client.post(reverse('sync_guild'), {
            'code': 'invalid'
        })
        self.assertEqual(response.status_code, 200) # Renders form with error
        self.assertContains(response, 'Código inválido')
