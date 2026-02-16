from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from .services import GuildLevelService
import random
import string

class SquadRank(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.IntegerField(default=0, help_text="Rank Hierarchy Order (Lower is lower rank)")
    missions_required = models.IntegerField(default=0)
    min_guild_level = models.IntegerField(default=1)
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class Squad(models.Model):
    name = models.CharField(max_length=100)
    # rank = models.CharField(max_length=20, choices=Rank.choices, default=Rank.RECRUIT)
    rank = models.ForeignKey(SquadRank, related_name='squads', on_delete=models.PROTECT, null=True, blank=True)
    missions_completed = models.IntegerField(default=0)
    guild = models.ForeignKey('Guild', related_name='squads', on_delete=models.CASCADE)

    def __str__(self):
        rank_name = self.rank.name if self.rank else "Sem Patente"
        return f"{self.name} ({rank_name})"

    def check_rank_progression(self):
        """
        Checks if the squad qualifies for a promotion based on dynamic SquadRank rules.
        """
        if not self.rank:
            return

        # Get all ranks ordered by difficulty/order
        ranks = SquadRank.objects.filter(
            order__gt=self.rank.order, # Only consider higher ranks
            missions_required__lte=self.missions_completed,
            min_guild_level__lte=self.guild.level
        ).order_by('-order')

        # If any rank is available
        if ranks.exists():
            new_rank = ranks.first()
            self.rank = new_rank
            self.save()

class Building(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    slots_required = models.IntegerField(default=1)
    min_level_required = models.IntegerField(default=1)

    # Bonus Flags
    bonus_gold_cap = models.BooleanField(default=False)
    bonus_member_slots = models.BooleanField(default=False)
    bonus_healing = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class BuildingPower(models.Model):
    building = models.ForeignKey(Building, related_name='powers', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.title} ({self.building.name})"

class Guild(models.Model):
    class LegalStatus(models.TextChoices):
        PATENTED = 'PATENTED', 'Patenteada'
        INDEPENDENT = 'INDEPENDENT', 'Independente'
        CLANDESTINE = 'CLANDESTINE', 'Clandestina'

    class MoralAlignment(models.TextChoices):
        HUMANITARIAN = 'HUMANITARIAN', 'Humanitária'
        CORPORATE = 'CORPORATE', 'Corporativa'
        PREDATORY = 'PREDATORY', 'Predatória'

    name = models.CharField(max_length=100)
    level = models.IntegerField(default=1)
    gxp = models.IntegerField(default=0)
    funds = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    influence_points = models.IntegerField(default=0)
    description = models.TextField(blank=True, default='')

    legal_status = models.CharField(
        max_length=20,
        choices=LegalStatus.choices,
        default=LegalStatus.INDEPENDENT
    )
    moral_alignment = models.CharField( # Renamed from moral_purpose to match request
        max_length=20,
        choices=MoralAlignment.choices,
        default=MoralAlignment.HUMANITARIAN
    )

    code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    emblem = models.CharField(max_length=50, default='swords')

    def save(self, *args, **kwargs):
        if not self.code:
             self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        while True:
            # Format: XXX-0000
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            digits = ''.join(random.choices(string.digits, k=4))
            code = f"{letters}-{digits}"
            if not self.__class__.objects.filter(code=code).exists():
                return code

    @property
    def qr_code_url(self):
        # Using a reliable public QR code API
        return f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={self.code}"

    def __str__(self):
        return self.name

    @property
    def base_stats(self):
        return GuildLevelService.get_base_stats(self.level)

    @property
    def max_gold_cap(self):
        base = self.base_stats['base_gold_cap']
        # Check for 'Caixa-Forte' by name as per requirements, or slug if available.
        # Using name is safer if slugs aren't guaranteed to be specific strings in the prompt
        # (though prompt implies specific buildings).
        # "Caixa-Forte" is the name given.
        if self.guild_buildings.filter(building__name="Caixa-Forte").exists():
            return base * Decimal('1.5')
        return base

    @property
    def max_member_slots(self):
        base = self.base_stats['base_member_slots']
        # "Alojamentos Expandidos"
        if self.guild_buildings.filter(building__name="Alojamentos Expandidos").exists():
            # Increase by 20%
            return int(base * 1.2)
        return base

    @property
    def used_building_slots(self):
        return self.guild_buildings.aggregate(
            total=models.Sum('building__slots_required')
        )['total'] or 0

    @property
    def available_building_slots(self):
        base = self.base_stats['base_building_slots']
        return base - self.used_building_slots

class GuildBuilding(models.Model):
    guild = models.ForeignKey(Guild, related_name='guild_buildings', on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    built_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.guild.name} - {self.building.name}"

class Member(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        DECEASED = 'DECEASED', 'Deceased'
        INJURED = 'INJURED', 'Injured' # Just in case
        RETIRED = 'RETIRED', 'Retired'

    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    guild = models.ForeignKey(Guild, related_name='members', on_delete=models.CASCADE)
    squad = models.ForeignKey(Squad, related_name='members', on_delete=models.SET_NULL, null=True, blank=True)

    # Optional: Level, Class, etc could be added later.

    def __str__(self):
        return self.name

class Monster(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    # Level 1
    size = models.CharField(max_length=50)
    description = models.TextField()

    # Level 2
    monster_type = models.CharField(max_length=50)
    combat_role = models.CharField(max_length=100, blank=True)
    movement = models.CharField(max_length=100, blank=True)
    defense = models.IntegerField(default=10)
    habitat = models.CharField(max_length=100, blank=True)
    challenge_level = models.DecimalField(max_digits=5, decimal_places=2) # ND

    # Level 3
    health_points = models.IntegerField(default=1)
    weaknesses = models.TextField(blank=True)
    immunities = models.TextField(blank=True)
    special_abilities = models.TextField(blank=True)

    # Metadata
    image = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def register_level(self):
        """
        Determines the quality level of the monster register.
        Level 1 (Rascunho): Basic info only.
        Level 2 (Registro de Campo): Has tactical info (type, defense, etc).
        Level 3 (Tratado Monstruoso): Has vital info (HP, weaknesses, etc).
        """
        # Check Level 3 first
        if self.health_points > 0 and (self.weaknesses or self.immunities or self.special_abilities):
            return 3
        # Check Level 2
        if self.monster_type and self.defense > 0:
            return 2
        # Default Level 1
        return 1

class Quest(models.Model):
    class Type(models.TextChoices):
        EXTERNAL = 'EXTERNAL', 'External'
        INTERNAL = 'INTERNAL', 'Internal'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        DELEGATED = 'DELEGATED', 'Delegated'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        DISASTER = 'DISASTER', 'Disaster'

    class Rank(models.TextChoices):
        F = 'F', 'F'
        E = 'E', 'E'
        D = 'D', 'D'
        C = 'C', 'C'
        B = 'B', 'B'
        A = 'A', 'A'
        S = 'S', 'S'

    RANK_GXP_REWARDS = {
        'F': 2,
        'E': 5,
        'D': 15,
        'C': 35,
        'B': 80,
        'A': 200,
        'S': 450
    }

    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.EXTERNAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    duration_days = models.IntegerField(default=1)
    rank = models.CharField(max_length=2, choices=Rank.choices)

    gold_reward = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gxp_reward = models.IntegerField(default=0)
    operational_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    guild = models.ForeignKey(Guild, related_name='quests', on_delete=models.CASCADE)
    assigned_members = models.ManyToManyField(Member, related_name='assigned_quests', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.gxp_reward and self.rank:
            self.gxp_reward = self.RANK_GXP_REWARDS.get(self.rank, 0)
        super().save(*args, **kwargs)

    def resolve_delegation(self):
        """
        Executes the logic for delegating a quest.
        Assuming 'assigned_members' are already set or handled by the caller before calling this.
        This method performs the 'Destiny Check' immediately as per requirements.
        """

        # Modifiers
        has_war_room = self.guild.guild_buildings.filter(building__name='Sala de Guerra').exists() or \
                       self.guild.guild_buildings.filter(building__slug='sala-de-guerra').exists()

        has_arsenal = self.guild.guild_buildings.filter(building__name='Arsenal').exists() or \
                      self.guild.guild_buildings.filter(building__slug='arsenal').exists()

        # Operational Cost Logic (Deduct Funds)
        cost = self.operational_cost
        if has_arsenal:
            cost = cost * Decimal('0.8') # 20% reduction

        if self.guild.funds >= cost:
             self.guild.funds -= cost
             self.guild.save()
        else:
             # Logic if funds are insufficient?
             # For now, we assume validation happened before, or we proceed with negative funds/error?
             # I'll just deduct it, allowing debt or it should be checked in ViewSet.
             self.guild.funds -= cost
             self.guild.save()

        # Destiny Check
        roll1 = random.randint(1, 20)
        roll = roll1

        if has_war_room:
            roll2 = random.randint(1, 20)
            roll = max(roll1, roll2)

        if roll == 1:
            # Critical Failure -> Disaster
            self.status = self.Status.DISASTER
            self.save()

            # Blood Cost
            dead_count = random.randint(1, 6)
            members = list(self.assigned_members.all())
            # Kill 'dead_count' members randomly? Or first ones?
            # "result is the number of assigned NPCs that are killed"
            # I'll shuffle and pick
            random.shuffle(members)
            victims = members[:dead_count]

            for victim in victims:
                victim.status = Member.Status.DECEASED
                victim.save()

            return {
                'outcome': 'DISASTER',
                'roll': roll,
                'dead_count': len(victims),
                'victims': [m.name for m in victims]
            }

        else:
            # Success (2-20) -> Completed
            self.complete_quest()
            return {
                'outcome': 'SUCCESS',
                'roll': roll
            }

    def complete_quest(self):
        """
        Completes the quest, distributing rewards.
        """
        if self.status == self.Status.COMPLETED:
            return # Already completed

        # Add GXP
        self.guild.gxp += self.gxp_reward

        # Add Gold (Respect Cap)
        max_cap = self.guild.max_gold_cap
        current_funds = self.guild.funds
        reward = self.gold_reward

        # If current funds + reward > max_cap, cap it?
        # "respecting the Vault limit logic implemented previously"
        # Usually this means we can't go over cap, or excess is lost.
        # Assuming excess is lost.

        new_funds = current_funds + reward
        if new_funds > max_cap:
            new_funds = max_cap

        self.guild.funds = new_funds

        # Check level up? The logic for level up is usually manual or handled elsewhere,
        # but prompt says "Guild progression logic (levels 1-10) is encapsulated in a helper class GuildLevelService"
        # Does adding GXP trigger level up? Not specified. I'll just add GXP.

        self.guild.save()
        self.status = self.Status.COMPLETED
        self.save()

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class Dispatch(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        COMPLETED = 'COMPLETED', 'Concluída'
        FAILED = 'FAILED', 'Falhou'
        DISASTER = 'DISASTER', 'Desastre'

    squad = models.ForeignKey(Squad, related_name='dispatches', on_delete=models.CASCADE, null=True, blank=True)
    rank = models.CharField(max_length=2, choices=Quest.Rank.choices, null=True, blank=True)
    npc_count = models.IntegerField(default=0)
    mission = models.ForeignKey(Quest, related_name='dispatches', on_delete=models.CASCADE, null=True, blank=True)
    duration_days = models.IntegerField(default=1)

    start_date = models.DateTimeField(default=timezone.now)
    target_date = models.DateTimeField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    result_log = models.TextField(blank=True, help_text="Log of the resolution (roll, deaths, etc)")

    def save(self, *args, **kwargs):
        if not self.target_date and self.start_date:
            self.target_date = self.start_date + timezone.timedelta(days=self.duration_days)
        super().save(*args, **kwargs)

    def resolve(self):
        """
        Executes the Test of Destiny logic.
        """
        if self.status != self.Status.PENDING:
            return None

        # Guild Context
        if self.squad:
            guild = self.squad.guild
        elif self.mission:
            guild = self.mission.guild
        else:
            return None

        # War Room Check
        has_war_room = guild.guild_buildings.filter(building__name='Sala de Cartografia').exists() or \
                       guild.guild_buildings.filter(building__slug='sala-cartografia').exists() or \
                       guild.guild_buildings.filter(building__name='Sala de Guerra').exists()

        # Roll
        roll1 = random.randint(1, 20)
        roll_final = roll1

        if has_war_room:
            roll2 = random.randint(1, 20)
            roll_final = max(roll1, roll2)

        outcome_data = {
            'roll': roll_final,
            'has_war_room': has_war_room,
            'deaths': 0,
            'dead_names': []
        }

        if roll_final == 1:
            # Critical Failure -> Disaster
            self.status = self.Status.DISASTER

            # Blood Cost
            if self.squad:
                deaths = random.randint(1, 6)
                members = list(self.squad.members.filter(status=Member.Status.ACTIVE))
                random.shuffle(members)
                victims = members[:deaths]
            else:
                deaths = self.npc_count
                members = list(guild.members.filter(status=Member.Status.ACTIVE))
                random.shuffle(members)
                victims = members[:deaths]

            for v in victims:
                v.status = Member.Status.DECEASED
                v.save()
                outcome_data['dead_names'].append(v.name)

            outcome_data['deaths'] = len(victims)
            self.result_log = f"Rolagem: {roll_final} (Crítico). Mortes: {len(victims)} ({', '.join(outcome_data['dead_names'])})"

            if self.mission:
                 self.mission.status = Quest.Status.DISASTER
                 self.mission.save()

        elif roll_final >= 2:
            # Success
            self.status = self.Status.COMPLETED

            if self.squad:
                # Create Internal Quest for History (Legacy)
                quest = Quest.objects.create(
                    title=f"Despacho: {self.squad.name} (Rank {self.rank or 'F'})",
                    description=f"Missão automática realizada pelo esquadrão {self.squad.name}.",
                    type=Quest.Type.INTERNAL,
                    status=Quest.Status.COMPLETED,
                    rank=self.rank or 'F',
                    duration_days=self.duration_days,
                    guild=guild,
                )
                quest.assigned_members.set(self.squad.members.all())
                quest.complete_quest()

                self.squad.missions_completed += 1
                self.squad.check_rank_progression()
                self.squad.save()
            elif self.mission:
                self.mission.complete_quest()

            self.result_log = f"Rolagem: {roll_final}. Sucesso! Recompensa entregue."

        self.save()
        return outcome_data
