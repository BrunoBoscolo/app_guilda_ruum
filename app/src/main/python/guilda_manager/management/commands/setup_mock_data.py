from django.core.management.base import BaseCommand
from guilda_manager.models import Guild, Quest, Member, Building, GuildBuilding, BuildingPower, Monster
from decimal import Decimal

class Command(BaseCommand):
    help = 'Sets up mock data for demonstration'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up mock data...')

        # 1. Guild
        guild, created = Guild.objects.get_or_create(
            name="A Guilda do Macaco Caolho",
            defaults={
                'level': 4,
                'funds': Decimal('2500.50'),
                'description': "Uma guilda famosa por aceitar qualquer trabalho, desde que pague bem."
            }
        )
        if created:
             self.stdout.write(self.style.SUCCESS(f'Created Guild: {guild.name}'))
        else:
             self.stdout.write(f'Using existing Guild: {guild.name}')

        # 2. Members
        members_data = ["Tharion", "Elara", "Grom", "Vex", "Lyra"]
        members = []
        for name in members_data:
            m, _ = Member.objects.get_or_create(name=name, guild=guild)
            members.append(m)

        # 3. Quests

        # Quest 1: Open
        q1, c1 = Quest.objects.get_or_create(
            title="Resgate do Mercador",
            guild=guild,
            defaults={
                'description': "Um mercador local desapareceu na estrada do sul. Há rumores de goblins.",
                'rank': Quest.Rank.F,
                'status': Quest.Status.OPEN,
                'duration_days': 2,
                'gold_reward': Decimal('150.00'),
                'operational_cost': Decimal('20.00')
            }
        )

        # Quest 2: Delegated
        q2, c2 = Quest.objects.get_or_create(
            title="Investigar Ruínas Antigas",
            guild=guild,
            defaults={
                'description': "Estranhas luzes foram vistas nas ruínas de Arton. O conselho exige respostas.",
                'rank': Quest.Rank.C,
                'status': Quest.Status.DELEGATED,
                'duration_days': 5,
                'gold_reward': Decimal('800.00'),
                'operational_cost': Decimal('100.00')
            }
        )
        if c2:
            q2.assigned_members.add(members[0], members[1]) # Tharion & Elara

        # Quest 3: Completed (Legendary)
        q3, c3 = Quest.objects.get_or_create(
            title="Caça ao Dragão Vermelho",
            guild=guild,
            defaults={
                'description': "A besta que assola o reino deve cair. Recompensa real oferecida.",
                'rank': Quest.Rank.S,
                'status': Quest.Status.COMPLETED,
                'duration_days': 10,
                'gold_reward': Decimal('10000.00'),
                'operational_cost': Decimal('2000.00')
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully created mock quests.'))

        # 4. Monsters

        # Existing Monsters (Keeping them for compatibility)
        # Troll
        Monster.objects.get_or_create(
            slug="troll",
            defaults={
                'name': "Troll",
                'size': "Grande",
                'description': "Uma criatura humanoide bruta, conhecida por sua fome insaciável e capacidade de regeneração. Sua pele é verde e verrugosa, e seus membros são longos e desengonçados.",
                'monster_type': "Monstro",
                'combat_role': "Bruto",
                'movement': "9m",
                'defense': 16,
                'habitat': "Florestas e Cavernas",
                'challenge_level': Decimal('5.00'),
                'health_points': 80,
                'weaknesses': "Fogo e Ácido (interrompem regeneração)",
                'special_abilities': "Regeneração 5"
            }
        )

        # Sacerdote de Aharadak
        Monster.objects.get_or_create(
            slug="sacerdote-de-aharadak",
            defaults={
                'name': "Sacerdote de Aharadak",
                'size': "Médio",
                'description': "Um cultista deformado pela Tormenta, com quitina rubra cobrindo parte do corpo e tentáculos onde deveria haver um braço.",
                'monster_type': "Humanoide (Lefou)",
                'combat_role': "Conjurador",
                'movement': "9m",
                'defense': 22,
                'habitat': "Áreas de Tormenta",
                'challenge_level': Decimal('10.00'),
                'health_points': 120,
                'immunities': "Acertos Críticos, Veneno",
                'special_abilities': "Magias de Tormenta, Insanidade da Tormenta"
            }
        )

        # Kobold
        Monster.objects.get_or_create(
            slug="kobold",
            defaults={
                'name': "Kobold",
                'size': "Pequeno",
                'description': "Pequenos reptilianos covardes que vivem em bandos. Dizem ser descendentes de dragões, mas parecem mais lagartixas irritadas.",
                'monster_type': "Humanoide",
                'combat_role': "Lacalo",
                'movement': "9m",
                'defense': 14,
                'habitat': "Cavernas",
                'challenge_level': Decimal('0.25'), # ND 1/4
                'health_points': 8,
                'weaknesses': "Luz Solar (Ofuscado)",
                'special_abilities': "Táticas de Bando"
            }
        )

        # Level 1 Example: Goblin (Rascunho)
        Monster.objects.get_or_create(
            slug="goblin-rascunho",
            defaults={
                'name': "Goblin (Avistado)",
                'size': "Pequeno",
                'description': "Vi um vulto verde correndo com uma galinha debaixo do braço. Parecia rir de forma maníaca. Fugiu para o mato antes que eu pudesse ver mais.",
                'challenge_level': Decimal('0.00'), # Unknown
                # Empty Level 2 and 3 fields
                'monster_type': "",
                'combat_role': "",
                'movement': "",
                'defense': 0,
                'habitat': "",
                'health_points': 0,
                'weaknesses': "",
                'immunities': "",
                'special_abilities': ""
            }
        )

        # Level 2 Example: Lobo (Registro de Campo)
        Monster.objects.get_or_create(
            slug="lobo-caverna",
            defaults={
                'name': "Lobo das Cavernas",
                'size': "Médio",
                'description': "Um lobo maior que o normal, com pelagem cinza escuro adaptada para camuflagem em pedras. Ataca em matilha.",
                'monster_type': "Animal",
                'combat_role': "Combatente",
                'movement': "12m",
                'defense': 15,
                'habitat': "Cavernas e Montanhas",
                'challenge_level': Decimal('2.00'),
                # Empty Level 3 fields
                'health_points': 0,
                'weaknesses': "",
                'immunities': "",
                'special_abilities': ""
            }
        )

        # New Monsters (~12 total including above, adding 7 more diverse ones)

        # 6. Esqueleto (Level 1 - Draft)
        Monster.objects.get_or_create(
            slug="esqueleto-antigo",
            defaults={
                'name': "Esqueleto Antigo",
                'size': "Médio",
                'description': "Encontramos restos mortais animados na cripta. Portavam armaduras enferrujadas e armas quebradas. Emitiam um som de ossos estalando.",
                'challenge_level': Decimal('0.5'),
                'monster_type': "",
                'combat_role': "",
                'movement': "",
                'defense': 0,
                'habitat': "",
                'health_points': 0,
                'weaknesses': "",
                'immunities': "",
                'special_abilities': ""
            }
        )

        # 7. Aranha Gigante (Level 2 - Field Record)
        Monster.objects.get_or_create(
            slug="aranha-gigante",
            defaults={
                'name': "Aranha Gigante",
                'size': "Grande",
                'description': "Uma aranha do tamanho de um cavalo. Suas teias são fortes como cordas e ela se move com rapidez assustadora pelas paredes.",
                'monster_type': "Monstro",
                'combat_role': "Controlador",
                'movement': "12m, Escalada 12m",
                'defense': 16,
                'habitat': "Florestas e Subterrâneos",
                'challenge_level': Decimal('2.00'),
                'health_points': 0, # Incomplete vital stats
                'weaknesses': "",
                'immunities': "",
                'special_abilities': ""
            }
        )

        # 8. Minotauro (Level 3 - Monstrous Treatise)
        Monster.objects.get_or_create(
            slug="minotauro-guarda",
            defaults={
                'name': "Minotauro Guarda",
                'size': "Grande",
                'description': "Metade homem, metade touro. Uma massa de músculos e fúria, geralmente armados com machados colossais.",
                'monster_type': "Humanoide",
                'combat_role': "Bruto",
                'movement': "9m",
                'defense': 18,
                'habitat': "Labirintos e Cavernas",
                'challenge_level': Decimal('4.00'),
                'health_points': 60,
                'weaknesses': "Magias Mentais (baixa Vontade)",
                'immunities': "",
                'special_abilities': "Faro, Carga Poderosa"
            }
        )

        # 9. Harpia (Level 2 - Field Record)
        Monster.objects.get_or_create(
            slug="harpia",
            defaults={
                'name': "Harpia",
                'size': "Médio",
                'description': "Mulheres-pássaro com garras afiadas e um canto hipnótico que atrai marinheiros e viajantes para a morte.",
                'monster_type': "Monstro",
                'combat_role': "Controlador",
                'movement': "9m, Voo 18m",
                'defense': 17,
                'habitat': "Montanhas e Costas",
                'challenge_level': Decimal('3.00'),
                'health_points': 0,
                'weaknesses': "",
                'immunities': "",
                'special_abilities': ""
            }
        )

        # 10. Cubo Gelatinoso (Level 3 - Monstrous Treatise)
        Monster.objects.get_or_create(
            slug="cubo-gelatinoso",
            defaults={
                'name': "Cubo Gelatinoso",
                'size': "Enorme",
                'description': "Um cubo transparente de lodo ácido que varre masmorras, dissolvendo qualquer matéria orgânica em seu caminho. Difícil de ver a olho nu.",
                'monster_type': "Limo",
                'combat_role': "Bruto",
                'movement': "6m",
                'defense': 8,
                'habitat': "Masmorras",
                'challenge_level': Decimal('6.00'),
                'health_points': 140,
                'weaknesses': "",
                'immunities': "Ácido, Eletricidade, Corte, Perfuracao",
                'special_abilities': "Engolfar, Paralisia, Transparência"
            }
        )

        # 11. Basilisco (Level 2 - Field Record)
        Monster.objects.get_or_create(
            slug="basilisco",
            defaults={
                'name': "Basilisco",
                'size': "Grande",
                'description': "Um lagarto de oito patas cujo olhar pode transformar carne em pedra. Uma das criaturas mais temidas por aventureiros.",
                'monster_type': "Monstro",
                'combat_role': "Bruto",
                'movement': "6m",
                'defense': 19,
                'habitat': "Desertos e Cavernas",
                'challenge_level': Decimal('7.00'),
                'health_points': 0,
                'weaknesses': "",
                'immunities': "",
                'special_abilities': ""
            }
        )

        # 12. Bandido de Estrada (Level 1 - Draft)
        Monster.objects.get_or_create(
            slug="bandido",
            defaults={
                'name': "Bandido de Estrada",
                'size': "Médio",
                'description': "Homens mal encarados armados com bestas e espadas curtas. Tentaram cobrar pedágio na ponte velha. Fugiram quando mostramos magia.",
                'challenge_level': Decimal('0.25'),
                'monster_type': "",
                'combat_role': "",
                'movement': "",
                'defense': 0,
                'habitat': "",
                'health_points': 0,
                'weaknesses': "",
                'immunities': "",
                'special_abilities': ""
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully created mock monsters.'))

        # 5. Buildings
        buildings_data = [
            {
                "name": "A Grande Forja",
                "slug": "a-grande-forja",
                "cost": Decimal("5000.00"),
                "description": "O calor é insuportável para quem não é do ramo, mas é o abraço do lar para um ferreiro.",
                "min_level": 1,
                "powers": [
                    {
                        "title": "Manufatura Pesada",
                        "description": "Permite a criação e reduz o material de fabricação de armas e armaduras metálicas em 20% (cumulativo com outros poderes)."
                    },
                    {
                        "title": "Ferreiro Amigo",
                        "description": "Disponibiliza armas e armaduras simples na loja da guilda. Ao comprar um desses itens, o jogador pode escolher pagar 150T$ para escolher um modificador simples qualquer."
                    }
                ]
            },
            {
                "name": "Laboratório de Alquimia",
                "slug": "laboratorio-de-alquimia",
                "cost": Decimal("5000.00"),
                "description": "Vidrarias borbulhantes, alambiques de cobre e ventiladores para expulsar vapores tóxicos.",
                "min_level": 1,
                "powers": [
                    {
                        "title": "Destilação",
                        "description": "Ao fabricar poções, elixires ou itens alquímicos, o personagem recupera 20% do custo de fabricação em materiais sobressalentes."
                    },
                    {
                        "title": "Segurança",
                        "description": "Permite fabricar venenos e ácidos sem risco de se envenenar acidentalmente em caso de falha."
                    }
                ]
            },
            {
                "name": "Torre de Vigia",
                "slug": "torre-de-vigia",
                "cost": Decimal("3000.00"),
                "description": "Uma torre alta para observar os arredores e detectar ameaças antes que elas cheguem.",
                "min_level": 1,
                "powers": [
                    {
                        "title": "Olhos de Águia",
                        "description": "Concede +2 em testes de Percepção para vigias alocados na torre."
                    }
                ]
            },
            {
                "name": "Biblioteca Arcana",
                "slug": "biblioteca-arcana",
                "cost": Decimal("12000.00"),
                "description": "O conhecimento é a arma mais perigosa. Guarde-o bem, use-o com sabedoria.",
                "min_level": 2,
                "powers": [
                    {
                        "title": "Acervo Místico",
                        "description": "Concede vantagem em testes de Misticismo para pesquisas realizadas na biblioteca."
                    }
                ]
            },
            {
                "name": "Santuário dos Deuses",
                "slug": "santuario-dos-deuses",
                "cost": Decimal("25000.00"),
                "description": "Um local sagrado para comunhão divina e milagres inesperados.",
                "min_level": 5, # Blocked in example
                "powers": [
                    {
                        "title": "Bênção Divina",
                        "description": "Membros podem orar para recuperar 1d8 pontos de mana adicionais durante o descanso."
                    }
                ]
            },
            {
                "name": "Caixa-Forte",
                "slug": "caixa-forte",
                "cost": Decimal("8000.00"),
                "description": "Proteção extra para os fundos da guilda.",
                "min_level": 3,
                "bonus_gold_cap": True,
                "powers": [
                    {
                        "title": "Cofre Seguro",
                        "description": "Aumenta o limite de ouro da guilda em 50%."
                    }
                ]
            },
            {
                "name": "Alojamentos Expandidos",
                "slug": "alojamentos-expandidos",
                "cost": Decimal("4000.00"),
                "description": "Mais camas, menos conforto.",
                "min_level": 2,
                "bonus_member_slots": True,
                "powers": [
                    {
                        "title": "Beliches Extras",
                        "description": "Aumenta a capacidade de membros da guilda em 20%."
                    }
                ]
            }
        ]

        for b_data in buildings_data:
            building, _ = Building.objects.get_or_create(
                slug=b_data["slug"],
                defaults={
                    "name": b_data["name"],
                    "cost": b_data["cost"],
                    "description": b_data["description"],
                    "min_level_required": b_data.get("min_level", 1),
                    "bonus_gold_cap": b_data.get("bonus_gold_cap", False),
                    "bonus_member_slots": b_data.get("bonus_member_slots", False),
                    "bonus_healing": b_data.get("bonus_healing", False)
                }
            )
            # Create powers
            if "powers" in b_data:
                for power_data in b_data["powers"]:
                    BuildingPower.objects.get_or_create(
                        building=building,
                        title=power_data["title"],
                        defaults={
                            "description": power_data["description"]
                        }
                    )

        self.stdout.write(self.style.SUCCESS('Successfully created mock buildings and powers.'))

        # Build some buildings for the guild (Infra view)
        # Build A Grande Forja and Laboratório de Alquimia
        for slug in ["a-grande-forja", "laboratorio-de-alquimia"]:
            building = Building.objects.filter(slug=slug).first()
            if building:
                GuildBuilding.objects.get_or_create(guild=guild, building=building)

        self.stdout.write(self.style.SUCCESS('Successfully populated guild buildings.'))
