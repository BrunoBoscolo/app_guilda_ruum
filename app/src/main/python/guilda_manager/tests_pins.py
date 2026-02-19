from django.test import TestCase
from .models import Guild, Pin
from django.urls import reverse

class PinManagementTestCase(TestCase):
    def setUp(self):
        self.guild = Guild.objects.create(name="Test Guild", level=1)
        self.url = reverse('mestre')

    def test_create_pin(self):
        # Create a pin via POST
        response = self.client.post(self.url, {
            'action': 'create_pin',
            'name': 'Test Pin',
            'glb_path': 'test.glb'
        })

        self.assertEqual(response.status_code, 200)

        # Verify Pin created
        self.assertTrue(Pin.objects.filter(name='Test Pin', glb_path='test.glb').exists())

    def test_delete_pin(self):
        # Create pin manually
        pin = Pin.objects.create(name='Delete Me', glb_path='delete.glb')

        # Delete via POST
        response = self.client.post(self.url, {
            'action': 'delete_pin',
            'pin_id': pin.id
        })

        self.assertEqual(response.status_code, 200)

        # Verify Pin deleted
        self.assertFalse(Pin.objects.filter(id=pin.id).exists())

    def test_available_pins_context(self):
        # Check if context has available_pins
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('available_pins', response.context)
        # We know there are pins in the static folder, so list should not be empty
        # unless running in an environment where static files are missing.
        # But based on list_files earlier, they exist.
        self.assertTrue(len(response.context['available_pins']) > 0)
