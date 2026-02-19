import os
import sys
import django

# Setup Django environment
# Assuming running from repo root
sys.path.append(os.path.join(os.getcwd(), 'app/src/main/python'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from guilda_manager.models import Map, Pin, Hexagon

def setup_data():
    print("Starting Map Data Setup...")

    # 1. Create Map
    map_obj, created = Map.objects.get_or_create(
        name="Reino do Macaco Caolho",
        defaults={
            'background_image': 'guilda_manager/placeholder.png'
        }
    )
    if created:
        print(f"Created Map: {map_obj.name}")
    else:
        print(f"Map already exists: {map_obj.name}")

    # 2. Create Pins
    pins_data = [
        ("Bau do Tesouro", "club-chest.glb"),
        ("Goblin Archer", "goblin_archer_miniature_stl_for_3d_printing.glb"),
        ("Dragão Bebê", "cute_baby_dragon_in_egg_-_3d_print_dragonlet.glb"),
        ("Lobisomem", "lycaon_werewolf_miniature_bust_for_3d_printing.glb"),
        ("Cavaleiro", "callum_edmond.glb"),
        ("Dragão Articulado", "articulated_dragon_cable_winder__organizer.glb")
    ]

    pins = {}
    for name, glb in pins_data:
        pin, created = Pin.objects.get_or_create(
            name=name,
            defaults={'glb_path': glb}
        )
        pins[name] = pin
        if created:
            print(f"Created Pin: {name}")

    # 3. Create Hexagons (Locations)
    # Using the original hardcoded locations + some new ones
    locations = [
        {
            'q': 0, 'r': 0,
            'pin_name': 'Bau do Tesouro',
            'title': 'Bau do Tesouro',
            'desc': 'Um bau antigo contendo riquezas esquecidas.'
        },
        {
            'q': 2, 'r': -1,
            'pin_name': 'Goblin Archer',
            'title': 'Sentinela Goblin',
            'desc': 'Um goblin arqueiro vigiando a area.'
        },
        {
            'q': -2, 'r': 2,
            'pin_name': 'Dragão Bebê',
            'title': 'Ninho de Dragão',
            'desc': 'Um pequeno dragão recém-nascido.'
        },
        # New locations
        {
            'q': 3, 'r': -3,
            'pin_name': 'Lobisomem',
            'title': 'Clareira da Lua',
            'desc': 'Um lobisomem uiva para a lua cheia.'
        },
        {
            'q': -1, 'r': -1,
            'pin_name': 'Cavaleiro',
            'title': 'Posto Avançado',
            'desc': 'Um cavaleiro solitário monta guarda.'
        }
    ]

    for loc in locations:
        pin = pins.get(loc['pin_name'])
        if pin:
            hex_obj, created = Hexagon.objects.update_or_create(
                map=map_obj,
                q=loc['q'],
                r=loc['r'],
                defaults={
                    'pin': pin,
                    'title': loc['title'],
                    'description': loc['desc']
                }
            )
            if created:
                print(f"Created Hex at ({loc['q']}, {loc['r']})")
            else:
                print(f"Updated Hex at ({loc['q']}, {loc['r']})")

    print("Setup Complete.")

if __name__ == "__main__":
    setup_data()
