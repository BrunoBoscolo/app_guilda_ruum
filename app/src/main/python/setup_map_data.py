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
            # Leave background_image empty to use default placeholder logic
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

    pin_names = [d[0] for d in pins_data]
    existing_pins = {p.name: p for p in Pin.objects.filter(name__in=pin_names)}

    new_pins = []
    for name, glb in pins_data:
        if name not in existing_pins:
            new_pins.append(Pin(name=name, glb_path=glb))

    if new_pins:
        Pin.objects.bulk_create(new_pins)
        print(f"Created {len(new_pins)} new Pins")
        # Refresh existing_pins
        existing_pins = {p.name: p for p in Pin.objects.filter(name__in=pin_names)}

    pins = existing_pins

    # 3. Create Hexagons (Locations)
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

    existing_hexes = {
        (h.q, h.r): h
        for h in Hexagon.objects.filter(map=map_obj)
    }

    to_create = []
    to_update = []

    for loc in locations:
        pin = pins.get(loc['pin_name'])
        if not pin:
            continue

        coords = (loc['q'], loc['r'])
        if coords in existing_hexes:
            hex_obj = existing_hexes[coords]
            updated = False
            if hex_obj.pin_id != pin.id:
                hex_obj.pin = pin
                updated = True
            if hex_obj.title != loc['title']:
                hex_obj.title = loc['title']
                updated = True
            if hex_obj.description != loc['desc']:
                hex_obj.description = loc['desc']
                updated = True

            if updated:
                to_update.append(hex_obj)
        else:
            to_create.append(Hexagon(
                map=map_obj,
                q=loc['q'],
                r=loc['r'],
                pin=pin,
                title=loc['title'],
                description=loc['desc']
            ))

    if to_create:
        Hexagon.objects.bulk_create(to_create)
        print(f"Created {len(to_create)} new Hexagons")

    if to_update:
        Hexagon.objects.bulk_update(to_update, ['pin', 'title', 'description'])
        print(f"Updated {len(to_update)} existing Hexagons")

    print("Setup Complete.")

if __name__ == "__main__":
    setup_data()
