from django.contrib import admin
from .models import Building, BuildingPower, Guild, GuildBuilding, Member, Quest, Monster, Upgrade, GuildUpgrade

@admin.register(Guild)
class GuildAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'funds')

@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'rank', 'guild')

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'guild')

class BuildingPowerInline(admin.TabularInline):
    model = BuildingPower
    extra = 1

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost')
    inlines = [BuildingPowerInline]

@admin.register(GuildBuilding)
class GuildBuildingAdmin(admin.ModelAdmin):
    list_display = ('guild', 'building')

@admin.register(Monster)
class MonsterAdmin(admin.ModelAdmin):
    list_display = ('name', 'monster_type', 'challenge_level', 'size')
    search_fields = ('name', 'monster_type', 'description')
    list_filter = ('monster_type', 'size')

@admin.register(Upgrade)
class UpgradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'cost', 'required_building', 'required_upgrade')
    list_filter = ('tier',)
    search_fields = ('name', 'description')

@admin.register(GuildUpgrade)
class GuildUpgradeAdmin(admin.ModelAdmin):
    list_display = ('guild', 'upgrade', 'acquired_at')
    list_filter = ('guild', 'upgrade__tier')
