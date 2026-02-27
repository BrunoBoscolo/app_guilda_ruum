from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch
from .models import Guild, Squad, SquadRank, Member, Quest, Dispatch, Building, GuildBuilding

class DispatchModelTests(TestCase):
    def setUp(self):
        self.guild = Guild.objects.create(name="Test Guild", funds=Decimal('1000.00'), level=1)
        self.rank_f = SquadRank.objects.create(name="F", order=0, missions_required=0)
        self.rank_e = SquadRank.objects.create(name="E", order=1, missions_required=1)
        self.squad = Squad.objects.create(name="Test Squad", guild=self.guild, rank=self.rank_f)

        # Add members to squad
        self.m1 = Member.objects.create(name="M1", guild=self.guild, squad=self.squad, status=Member.Status.ACTIVE)
        self.m2 = Member.objects.create(name="M2", guild=self.guild, squad=self.squad, status=Member.Status.ACTIVE)
        self.m3 = Member.objects.create(name="M3", guild=self.guild, squad=self.squad, status=Member.Status.ACTIVE)

        self.mission = Quest.objects.create(
            title="Test Mission",
            description="Desc",
            rank=Quest.Rank.F,
            guild=self.guild,
            gold_reward=Decimal('100.00'),
            gxp_reward=10
        )

    def test_resolve_status_not_pending(self):
        dispatch = Dispatch.objects.create(squad=self.squad, status=Dispatch.Status.COMPLETED)
        result = dispatch.resolve()
        self.assertIsNone(result)

    def test_resolve_no_guild_context(self):
        dispatch = Dispatch.objects.create() # No squad, no mission
        result = dispatch.resolve()
        self.assertIsNone(result)

    def test_resolve_success_squad(self):
        dispatch = Dispatch.objects.create(squad=self.squad, rank='F')

        with patch('random.randint', return_value=10):
            result = dispatch.resolve()

        self.assertEqual(result['roll'], 10)
        self.assertEqual(dispatch.status, Dispatch.Status.COMPLETED)

        # Verify squad progression
        self.squad.refresh_from_db()
        self.assertEqual(self.squad.missions_completed, 1)
        # Should have promoted to Rank E because it requires 1 mission
        self.assertEqual(self.squad.rank, self.rank_e)

        # Verify internal quest creation
        self.assertTrue(Quest.objects.filter(type=Quest.Type.INTERNAL, guild=self.guild).exists())

        # Verify rewards distributed (GXP)
        self.guild.refresh_from_db()
        # Quest Rank F gives 2 GXP by default if not specified, but here Dispatch created it with rank F.
        # Dispatch code: quest.complete_quest() is called.
        self.assertEqual(self.guild.gxp, 2)

    def test_resolve_success_mission(self):
        dispatch = Dispatch.objects.create(mission=self.mission)

        with patch('random.randint', return_value=10):
            dispatch.resolve()

        self.assertEqual(dispatch.status, Dispatch.Status.COMPLETED)
        self.mission.refresh_from_db()
        self.assertEqual(self.mission.status, Quest.Status.COMPLETED)

        # Verify rewards
        self.guild.refresh_from_db()
        self.assertEqual(self.guild.gxp, 10) # From self.mission.gxp_reward

    def test_resolve_disaster_squad(self):
        dispatch = Dispatch.objects.create(squad=self.squad)

        # Mock roll=1 (Disaster) and deaths=2
        with patch('random.randint', side_effect=[1, 2]):
            result = dispatch.resolve()

        self.assertEqual(dispatch.status, Dispatch.Status.DISASTER)
        self.assertEqual(result['deaths'], 2)

        # Check deaths
        dead_count = Member.objects.filter(squad=self.squad, status=Member.Status.DECEASED).count()
        self.assertEqual(dead_count, 2)

    def test_resolve_disaster_mission_npc(self):
        # Create some extra members in the guild not in squad
        Member.objects.create(name="G1", guild=self.guild, status=Member.Status.ACTIVE)
        Member.objects.create(name="G2", guild=self.guild, status=Member.Status.ACTIVE)
        Member.objects.create(name="G3", guild=self.guild, status=Member.Status.ACTIVE)

        dispatch = Dispatch.objects.create(mission=self.mission, npc_count=3)

        with patch('random.randint', return_value=1): # Disaster
            dispatch.resolve()

        self.assertEqual(dispatch.status, Dispatch.Status.DISASTER)
        self.mission.refresh_from_db()
        self.assertEqual(self.mission.status, Quest.Status.DISASTER)

        # Check deaths (should be npc_count=3)
        dead_count = Member.objects.filter(guild=self.guild, status=Member.Status.DECEASED).count()
        self.assertEqual(dead_count, 3)

    def test_resolve_war_room_advantage(self):
        # Add War Room building
        war_room = Building.objects.create(name='Sala de Guerra', slug='sala-de-guerra', cost=0, slots_required=1)
        GuildBuilding.objects.create(guild=self.guild, building=war_room)

        dispatch = Dispatch.objects.create(squad=self.squad)

        # Mock rolls: 1 and 15. max(1, 15) = 15 -> Success
        with patch('random.randint', side_effect=[1, 15]):
            result = dispatch.resolve()

        self.assertTrue(result['has_war_room'])
        self.assertEqual(result['roll'], 15)
        self.assertEqual(dispatch.status, Dispatch.Status.COMPLETED)
