from django.test import TestCase
from .models import Guild, Squad, Dispatch, Member, Quest, SquadRank
from django.utils import timezone
import random

class MestreTestCase(TestCase):
    def setUp(self):
        self.guild = Guild.objects.create(name="Test Guild", level=1)

        # Create Ranks
        self.rank_recruit = SquadRank.objects.create(name='Recruta', order=1, missions_required=0, min_guild_level=1)
        self.rank_confirmed = SquadRank.objects.create(name='Confirmados', order=2, missions_required=3, min_guild_level=1)
        self.rank_veteran = SquadRank.objects.create(name='Veteranos', order=3, missions_required=10, min_guild_level=1)
        self.rank_elite = SquadRank.objects.create(name='Elite', order=4, missions_required=20, min_guild_level=7)
        self.rank_legends = SquadRank.objects.create(name='Lendas', order=5, missions_required=999, min_guild_level=10)

        self.squad = Squad.objects.create(name="Alpha Squad", guild=self.guild, rank=self.rank_recruit)
        self.member1 = Member.objects.create(name="Soldier 1", guild=self.guild, squad=self.squad)
        self.member2 = Member.objects.create(name="Soldier 2", guild=self.guild, squad=self.squad)

    def test_squad_rank_progression(self):
        # Initial rank
        self.assertEqual(self.squad.rank, self.rank_recruit)

        # Complete 3 missions
        self.squad.missions_completed = 3
        self.squad.check_rank_progression()
        self.assertEqual(self.squad.rank, self.rank_confirmed)

        # Complete 10 missions
        self.squad.missions_completed = 10
        self.squad.check_rank_progression()
        self.assertEqual(self.squad.rank, self.rank_veteran)

        # Complete 20 missions but Guild Level < 7
        self.squad.missions_completed = 20
        self.squad.check_rank_progression()
        self.assertEqual(self.squad.rank, self.rank_veteran)

        # Guild Level 7
        self.guild.level = 7
        self.guild.save()
        self.squad.check_rank_progression()
        self.assertEqual(self.squad.rank, self.rank_elite)

    def test_dispatch_creation_and_resolution(self):
        dispatch = Dispatch.objects.create(
            squad=self.squad,
            rank=Quest.Rank.D,
            duration_days=1,
            status=Dispatch.Status.PENDING
        )

        self.assertEqual(dispatch.status, Dispatch.Status.PENDING)

        # Resolve (Mocking random to ensure success)
        # We can't easily mock random inside the model method without patching.
        # But we can check if result is one of expected states.

        outcome = dispatch.resolve()

        self.assertIn(dispatch.status, [Dispatch.Status.COMPLETED, Dispatch.Status.DISASTER])
        if dispatch.status == Dispatch.Status.COMPLETED:
            # Refetch squad
            self.squad.refresh_from_db()
            self.assertEqual(self.squad.missions_completed, 1) # Incremented? Default was 0.
            # Check if Quest was created
            self.assertTrue(Quest.objects.filter(type=Quest.Type.INTERNAL, rank=Quest.Rank.D).exists())

        elif dispatch.status == Dispatch.Status.DISASTER:
            # Check for deaths logic if any
            pass

    def test_delete_guild(self):
        # Verify guild exists initially
        self.assertTrue(Guild.objects.exists())

        # Post action to delete guild
        response = self.client.post('/mestre/', {'action': 'delete_guild'})

        # Verify redirect
        self.assertRedirects(response, '/entry/')

        # Verify guild is deleted
        self.assertFalse(Guild.objects.exists())
