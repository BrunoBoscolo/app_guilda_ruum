import sys
import os
from django.core.management.base import BaseCommand
from guilda_manager.models import Building, Upgrade, Guild, GuildUpgrade

class Command(BaseCommand):
    help = 'Sets up mock data for base buildings and upgrades tree'

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting up mock upgrades data...")

        # 1. Ensure Guild exists
        guild = Guild.objects.first()
        if not guild:
            guild = Guild.objects.create(name="Guilda Aventureiros", funds=100000)
            self.stdout.write(f"Created dummy Guild: {guild.name}")

        # 2. Base Buildings (Using ones from the hub if they exist, or creating mock ones)
        forge, _ = Building.objects.get_or_create(
            slug="forja",
            defaults={
                "name": "A Grande Forja",
                "description": "Uma forja quente capaz de derreter os metais mais duros.",
                "cost": 5000,
                "slots_required": 1,
                "min_level_required": 1,
            }
        )

        lab, _ = Building.objects.get_or_create(
            slug="laboratorio",
            defaults={
                "name": "Laboratório de Alquimia",
                "description": "Equipamentos de vidro, ervas exóticas e vapores estranhos.",
                "cost": 5000,
                "slots_required": 1,
                "min_level_required": 1,
            }
        )

        tavern, _ = Building.objects.get_or_create(
            slug="taverna",
            defaults={
                "name": "Taverna do Javali",
                "description": "Um lugar para beber, descansar e ouvir boatos.",
                "cost": 2000,
                "slots_required": 1,
                "min_level_required": 1,
            }
        )

        # 3. Upgrades

        # --- FORGE TREE ---
        # Tier 1 Forge
        u_forge_1, _ = Upgrade.objects.get_or_create(
            name="Bigornas de Mitral",
            defaults={
                "description": "Bigornas extremamente resistentes. Acelera o trabalho do ferreiro.",
                "tier": 1,
                "cost": 2500,
                "icon": "hardware",
                "required_building": forge,
            }
        )

        u_forge_2, _ = Upgrade.objects.get_or_create(
            name="Fogo Sagrado",
            defaults={
                "description": "Uma chama divina abençoada. Permite forjar equipamentos sagrados.",
                "tier": 1,
                "cost": 3000,
                "icon": "local_fire_department",
                "required_building": forge,
            }
        )

        # Tier 2 Forge
        u_forge_1_1, _ = Upgrade.objects.get_or_create(
            name="Martelos Autônomos",
            defaults={
                "description": "Golems menores em forma de martelo que trabalham dia e noite.",
                "tier": 2,
                "cost": 8000,
                "icon": "gavel",
                "required_upgrade": u_forge_1,
            }
        )

        # --- LAB TREE ---
        # Tier 1 Lab
        u_lab_1, _ = Upgrade.objects.get_or_create(
            name="Caldeirão da Bruxa",
            defaults={
                "description": "Aumenta a potência de todas as poções de cura feitas aqui.",
                "tier": 1,
                "cost": 2000,
                "icon": "science",
                "required_building": lab,
            }
        )

        u_lab_2, _ = Upgrade.objects.get_or_create(
            name="Estufa Botânica",
            defaults={
                "description": "Permite cultivar ingredientes raros dentro da sede.",
                "tier": 1,
                "cost": 4000,
                "icon": "eco",
                "required_building": lab,
            }
        )

        # Tier 2 Lab
        u_lab_1_1, _ = Upgrade.objects.get_or_create(
            name="Alambique de Cristal",
            defaults={
                "description": "Destilação perfeita. Permite a criação de poções raras.",
                "tier": 2,
                "cost": 5000,
                "icon": "water_drop",
                "required_upgrade": u_lab_1,
            }
        )

        # --- TAVERN TREE ---
        # Tier 1
        u_tav_1, _ = Upgrade.objects.get_or_create(
            name="Quartos de Luxo",
            defaults={
                "description": "Aumenta a moral e recuperação de PV dos aventureiros que dormirem aqui.",
                "tier": 1,
                "cost": 1500,
                "icon": "bed",
                "required_building": tavern,
            }
        )

        self.stdout.write(self.style.SUCCESS('Mock data created successfully!'))
