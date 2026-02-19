from django.test import TestCase, Client
from .models import Quest, Guild

class MissionCreationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.guild = Guild.objects.create(name="Test Guild", level=1)

    def test_create_quick_mission(self):
        initial_count = Quest.objects.count()
        response = self.client.post('/mestre/', {'action': 'create_quick_mission'})

        # Expect 200 because it renders the template with success message
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Quest.objects.count(), initial_count + 1)

        quest = Quest.objects.latest('id')
        self.assertEqual(quest.guild, self.guild)
        self.assertEqual(quest.type, Quest.Type.EXTERNAL)

    def test_create_custom_mission(self):
        initial_count = Quest.objects.count()
        data = {
            'action': 'create_custom_mission',
            'title': 'Custom Quest',
            'description': 'Desc',
            'rank': 'C',
            'reward_gold': 100,
            'reward_xp': 50,
            'duration': 5
        }
        response = self.client.post('/mestre/', data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Quest.objects.count(), initial_count + 1)

        quest = Quest.objects.latest('id')
        self.assertEqual(quest.title, 'Custom Quest')
        self.assertEqual(quest.gold_reward, 100)
        self.assertEqual(quest.gxp_reward, 50)
        self.assertEqual(quest.duration_days, 5)
