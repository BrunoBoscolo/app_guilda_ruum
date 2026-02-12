from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from .models import Guild, Building, GuildBuilding, Member, Quest, Monster
from .services import GuildLevelService
from unittest.mock import patch
import random
import hashlib
from django.test import Client

class GuildModelTests(TestCase):
    def setUp(self):
        self.guild = Guild.objects.create(name="Heroes of Tormenta", funds=Decimal('10000.00'), level=1)
        self.vault = Building.objects.create(
            name="Caixa-Forte",
            slug="caixa-forte",
            description="Increases gold cap",
            cost=Decimal('1000.00'),
            slots_required=1,
            bonus_gold_cap=True
        )
        self.quarters = Building.objects.create(
            name="Alojamentos Expandidos",
            slug="alojamentos-expandidos",
            description="Increases member slots",
            cost=Decimal('1000.00'),
            slots_required=1,
            bonus_member_slots=True
        )

    def test_default_values(self):
        self.assertEqual(self.guild.level, 1)
        self.assertEqual(self.guild.funds, Decimal('10000.00'))
        self.assertEqual(self.guild.base_stats['base_building_slots'], 1)

    def test_max_gold_cap_logic(self):
        # Level 1 Base: 2000
        self.assertEqual(self.guild.max_gold_cap, Decimal('2000'))

        # Build Vault manually
        GuildBuilding.objects.create(guild=self.guild, building=self.vault)

        # Level 1 + Vault (+50%): 3000
        self.assertEqual(self.guild.max_gold_cap, Decimal('3000'))

    def test_max_member_slots_logic(self):
        # Level 1 Base: 5
        self.assertEqual(self.guild.max_member_slots, 5)

        # Build Quarters manually
        GuildBuilding.objects.create(guild=self.guild, building=self.quarters)

        # Level 1 + Quarters (+20%): 5 * 1.2 = 6
        self.assertEqual(self.guild.max_member_slots, 6)

    def test_used_building_slots(self):
        self.assertEqual(self.guild.used_building_slots, 0)
        GuildBuilding.objects.create(guild=self.guild, building=self.vault)
        self.assertEqual(self.guild.used_building_slots, 1)


class GuildAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.guild = Guild.objects.create(name="Heroes", funds=Decimal('5000.00'), level=1)
        self.building = Building.objects.create(
            name="Enfermaria",
            slug="enfermaria",
            description="Heals stuff",
            cost=Decimal('500.00'),
            slots_required=1,
            min_level_required=1
        )
        self.high_level_building = Building.objects.create(
            name="Tower",
            slug="tower",
            description="Tall",
            cost=Decimal('500.00'),
            slots_required=1,
            min_level_required=5
        )

    def test_retrieve_guild(self):
        response = self.client.get(f'/api/guilds/{self.guild.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Heroes")
        self.assertIn('max_gold_cap', response.data)
        self.assertIn('available_building_slots', response.data)

    def test_construct_building_success(self):
        response = self.client.post(f'/api/guilds/{self.guild.id}/construct_building/', {'building_slug': self.building.slug})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.guild.refresh_from_db()
        self.assertEqual(self.guild.funds, Decimal('4500.00'))
        self.assertTrue(self.guild.guild_buildings.filter(building=self.building).exists())

    def test_construct_building_insufficient_funds(self):
        self.guild.funds = Decimal('0.00')
        self.guild.save()

        response = self.client.post(f'/api/guilds/{self.guild.id}/construct_building/', {'building_slug': self.building.slug})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check for error in any field
        self.assertTrue(any("Fundos insuficientes" in str(err) for err in response.data.values()))

    def test_construct_building_insufficient_slots(self):
        # Fill slot (Level 1 has 1 slot)
        GuildBuilding.objects.create(guild=self.guild, building=self.building)

        # Try to build another
        response = self.client.post(f'/api/guilds/{self.guild.id}/construct_building/', {'building_slug': self.building.slug})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any("Espaço insuficiente na sede" in str(err) for err in response.data.values()))

    def test_construct_building_insufficient_level(self):
        response = self.client.post(f'/api/guilds/{self.guild.id}/construct_building/', {'building_slug': self.high_level_building.slug})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(any("Nível da guilda insuficiente" in str(err) for err in response.data.values()))

class QuestTests(TestCase):
    def setUp(self):
        self.guild = Guild.objects.create(name="QuestGuild", funds=Decimal('10000.00'), level=1)
        self.member1 = Member.objects.create(name="Hero1", guild=self.guild, status=Member.Status.ACTIVE)
        self.member2 = Member.objects.create(name="Hero2", guild=self.guild, status=Member.Status.ACTIVE)

        self.war_room = Building.objects.create(
            name="Sala de Guerra",
            slug="sala-de-guerra",
            description="War Room",
            cost=Decimal('1000.00'),
            slots_required=1
        )
        self.arsenal = Building.objects.create(
            name="Arsenal",
            slug="arsenal",
            description="Arsenal",
            cost=Decimal('1000.00'),
            slots_required=1
        )

    def test_quest_creation_default_gxp(self):
        quest = Quest.objects.create(
            title="Test Quest",
            description="Desc",
            rank=Quest.Rank.F,
            guild=self.guild,
            gold_reward=Decimal('100.00')
        )
        self.assertEqual(quest.gxp_reward, 2) # F Rank = 2 GXP

    def test_delegation_success(self):
        quest = Quest.objects.create(
            title="Test Quest",
            description="Desc",
            rank=Quest.Rank.F,
            guild=self.guild,
            gold_reward=Decimal('100.00'),
            operational_cost=Decimal('50.00')
        )
        quest.assigned_members.add(self.member1)

        # Mock random.randint to return 10 (Success)
        with patch('random.randint', return_value=10):
            result = quest.resolve_delegation()

        self.assertEqual(result['outcome'], 'SUCCESS')
        self.assertEqual(quest.status, Quest.Status.COMPLETED)

        # Check rewards
        self.guild.refresh_from_db()
        self.assertEqual(self.guild.gxp, 2)
        # Funds: 10000 - 50 (cost) + 100 (reward) = 10050. But max cap is 2000.
        # Cost deduction: 9950. Reward addition: 10050 -> Cap 2000.
        self.assertEqual(self.guild.funds, Decimal('2000.00'))

    def test_delegation_arsenal_cost_reduction(self):
        # Build Arsenal
        GuildBuilding.objects.create(guild=self.guild, building=self.arsenal)

        quest = Quest.objects.create(
            title="Arsenal Quest",
            description="Desc",
            rank=Quest.Rank.F,
            guild=self.guild,
            gold_reward=Decimal('0'),
            operational_cost=Decimal('100.00')
        )
        quest.assigned_members.add(self.member1)

        # To avoid cap logic interfering with cost verification, use lower funds.
        self.guild.funds = Decimal('1000.00')
        self.guild.save()

        with patch('random.randint', return_value=10):
            quest.resolve_delegation()

        self.guild.refresh_from_db()
        # 1000 - (100 * 0.8) = 1000 - 80 = 920.
        self.assertEqual(self.guild.funds, Decimal('920.00'))

    def test_delegation_war_room_advantage(self):
        # Build War Room
        GuildBuilding.objects.create(guild=self.guild, building=self.war_room)

        quest = Quest.objects.create(
            title="War Room Quest",
            description="Desc",
            rank=Quest.Rank.F,
            guild=self.guild,
            gold_reward=Decimal('0'),
            operational_cost=Decimal('0')
        )
        quest.assigned_members.add(self.member1)

        # Mock randint. Call 1: 1 (Fail). Call 2: 10 (Success).
        # War room takes max(1, 10) = 10 -> Success.
        with patch('random.randint', side_effect=[1, 10]):
            result = quest.resolve_delegation()

        self.assertEqual(result['outcome'], 'SUCCESS')

    def test_delegation_disaster_blood_cost(self):
        quest = Quest.objects.create(
            title="Disaster Quest",
            description="Desc",
            rank=Quest.Rank.F,
            guild=self.guild,
            gold_reward=Decimal('0'),
            operational_cost=Decimal('0')
        )
        quest.assigned_members.add(self.member1, self.member2)

        # Mock randint. Return 1 (Fail).
        # Then next call is for dead_count. Return 1.
        with patch('random.randint', side_effect=[1, 1]):
             result = quest.resolve_delegation()

        self.assertEqual(result['outcome'], 'DISASTER')
        self.assertEqual(quest.status, Quest.Status.DISASTER)
        self.assertEqual(result['dead_count'], 1)

        # Check 1 member died
        dead_members = Member.objects.filter(guild=self.guild, status=Member.Status.DECEASED).count()
        self.assertEqual(dead_members, 1)

class QuestAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.guild = Guild.objects.create(name="QuestGuild", funds=Decimal('1000.00'), level=1)
        self.member = Member.objects.create(name="Hero", guild=self.guild, status=Member.Status.ACTIVE)
        self.quest = Quest.objects.create(
            title="API Quest",
            description="Desc",
            rank=Quest.Rank.F,
            guild=self.guild,
            gold_reward=Decimal('100.00')
        )

    def test_delegate_endpoint(self):
        with patch('random.randint', return_value=10):
            response = self.client.post(f'/api/quests/{self.quest.id}/delegate/', {
                'assigned_members': [self.member.id]
            })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['delegation_result']['outcome'], 'SUCCESS')
        self.quest.refresh_from_db()
        self.assertEqual(self.quest.status, Quest.Status.COMPLETED)

    def test_delegate_invalid_member(self):
        response = self.client.post(f'/api/quests/{self.quest.id}/delegate/', {
            'assigned_members': [999]
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_endpoint(self):
        self.quest.status = Quest.Status.IN_PROGRESS
        self.quest.save()

        response = self.client.patch(f'/api/quests/{self.quest.id}/complete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.quest.refresh_from_db()
        self.assertEqual(self.quest.status, Quest.Status.COMPLETED)

class MissoesViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.guild = Guild.objects.create(name="ViewTestGuild", funds=Decimal('100.00'), level=1)
        self.quest1 = Quest.objects.create(
            title="Quest 1", guild=self.guild, rank='F', duration_days=5, description="Desc"
        )
        self.quest2 = Quest.objects.create(
            title="Quest 2", guild=self.guild, rank='E', duration_days=3, description="Desc"
        )

    def test_missoes_view_context(self):
        response = self.client.get('/missoes/')
        self.assertEqual(response.status_code, 200)

        quests_context = response.context['quests']
        self.assertEqual(len(quests_context), 2)

        for q in quests_context:
            self.assertTrue(hasattr(q, 'seal_rotation'), "Quest missing seal_rotation")
            self.assertTrue(hasattr(q, 'seal_top_offset'), "Quest missing seal_top_offset")
            self.assertTrue(hasattr(q, 'seal_right_offset'), "Quest missing seal_right_offset")

            # Verify deterministic calculation
            seed_str = f"{q.id}-{q.title}"
            seed_hash = hashlib.md5(seed_str.encode('utf-8')).hexdigest()
            seed_int = int(seed_hash, 16)
            rng = random.Random(seed_int)

            expected_rotation = rng.randint(-20, 20)
            self.assertEqual(q.seal_rotation, expected_rotation, "Seal rotation not deterministic")

class MonsterModelTests(TestCase):
    def test_monster_level_1(self):
        monster = Monster.objects.create(
            name="Goblin",
            slug="goblin",
            size="Small",
            description="A nasty creature.",
            challenge_level=Decimal('0.25')
        )
        self.assertEqual(monster.register_level, 1)

    def test_monster_level_2(self):
        monster = Monster.objects.create(
            name="Orc",
            slug="orc",
            size="Medium",
            description="A brute.",
            challenge_level=Decimal('1.0'),
            monster_type="Humanoid",
            defense=13
        )
        self.assertEqual(monster.register_level, 2)

    def test_monster_level_3(self):
        monster = Monster.objects.create(
            name="Dragon",
            slug="dragon",
            size="Huge",
            description="Fire breather.",
            challenge_level=Decimal('10.0'),
            monster_type="Dragon",
            defense=18,
            health_points=200,
            weaknesses="Cold"
        )
        self.assertEqual(monster.register_level, 3)
