from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Guild, GuildBuilding, Building, Member, Quest

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['name', 'slug', 'description', 'cost', 'slots_required', 'min_level_required',
                  'bonus_gold_cap', 'bonus_member_slots', 'bonus_healing']

class GuildBuildingSerializer(serializers.ModelSerializer):
    building = BuildingSerializer(read_only=True)

    class Meta:
        model = GuildBuilding
        fields = ['id', 'building', 'built_at']

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['id', 'name', 'status', 'guild']

class QuestSerializer(serializers.ModelSerializer):
    assigned_members_details = MemberSerializer(source='assigned_members', many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    rank_display = serializers.CharField(source='get_rank_display', read_only=True)

    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'description', 'type', 'status', 'status_display',
            'duration_days', 'rank', 'rank_display',
            'gold_reward', 'gxp_reward', 'operational_cost',
            'guild', 'assigned_members', 'assigned_members_details',
            'created_at', 'updated_at'
        ]

class GuildDashboardSerializer(serializers.ModelSerializer):
    active_buildings = GuildBuildingSerializer(source='guild_buildings', many=True, read_only=True)

    # Computed properties
    max_gold_cap = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    max_member_slots = serializers.IntegerField(read_only=True)
    available_building_slots = serializers.IntegerField(read_only=True)
    base_stats = serializers.DictField(read_only=True)
    used_building_slots = serializers.IntegerField(read_only=True)

    class Meta:
        model = Guild
        fields = [
            'id', 'name', 'level', 'gxp', 'funds', 'influence_points', 'description',
            'legal_status', 'moral_alignment',
            'max_gold_cap', 'max_member_slots', 'available_building_slots', 'used_building_slots',
            'base_stats', 'active_buildings'
        ]

    def validate_funds(self, value):
        if value < 0:
            raise serializers.ValidationError("Fundos não podem ser negativos.")
        return value

class BuildConstructionSerializer(serializers.Serializer):
    building_slug = serializers.SlugField()

    def validate_building_slug(self, value):
        try:
            return Building.objects.get(slug=value)
        except Building.DoesNotExist:
            raise serializers.ValidationError("Construção não encontrada.")

    def validate(self, data):
        guild = self.context.get('guild')
        if not guild:
            raise serializers.ValidationError("Guilda não fornecida no contexto.")

        building = data['building_slug']

        # Check level
        if guild.level < building.min_level_required:
            raise serializers.ValidationError("Nível da guilda insuficiente.")

        # Check funds
        if guild.funds < building.cost:
            raise serializers.ValidationError("Fundos insuficientes")

        # Check slots
        if guild.available_building_slots < building.slots_required:
            raise serializers.ValidationError("Espaço insuficiente na sede")

        return data

    def create(self, validated_data):
        guild = self.context['guild']
        building = validated_data['building_slug']

        # Deduct funds
        guild.funds -= building.cost
        guild.save()

        # Create GuildBuilding
        return GuildBuilding.objects.create(guild=guild, building=building)
