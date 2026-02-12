from django.test import TestCase, Client
from .models import Quest, Guild
from decimal import Decimal

class SealViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.guild = Guild.objects.create(name="Test Guild", funds=Decimal('100.00'), level=1)

        # Create quests with different ranks
        self.quest_s = Quest.objects.create(
            title="S Rank Quest",
            guild=self.guild,
            rank='S',
            duration_days=5,
            description="Super hard quest"
        )
        self.quest_f = Quest.objects.create(
            title="F Rank Quest",
            guild=self.guild,
            rank='F',
            duration_days=1,
            description="Easy quest"
        )

    def test_seal_image_path_context(self):
        """
        Verify that the view adds the correct seal_image_path to the quest objects in the context.
        """
        response = self.client.get('/missoes/')
        self.assertEqual(response.status_code, 200)

        quests = response.context['quests']

        # Helper to find quest by title
        def get_quest_by_title(title):
            for q in quests:
                if q.title == title:
                    return q
            return None

        qs = get_quest_by_title("S Rank Quest")
        qf = get_quest_by_title("F Rank Quest")

        self.assertIsNotNone(qs)
        self.assertIsNotNone(qf)

        # Check if the attribute exists and is correct
        self.assertTrue(hasattr(qs, 'seal_image_path'), "Quest object should have seal_image_path attribute")
        self.assertEqual(qs.seal_image_path, "guilda_manager/images/SELOS/S.png")

        self.assertTrue(hasattr(qf, 'seal_image_path'), "Quest object should have seal_image_path attribute")
        self.assertEqual(qf.seal_image_path, "guilda_manager/images/SELOS/F.png")

    def test_seal_image_rendered_html(self):
        """
        Verify that the HTML contains the correct image src.
        """
        response = self.client.get('/missoes/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Check for the S rank seal
        expected_src_s = '/static/guilda_manager/images/SELOS/S.png'
        self.assertIn(expected_src_s, content)

        # Check for the F rank seal
        expected_src_f = '/static/guilda_manager/images/SELOS/F.png'
        self.assertIn(expected_src_f, content)
