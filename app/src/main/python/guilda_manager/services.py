from decimal import Decimal

class GuildLevelService:
    """
    Helper class to map Guild Levels to their Base Attributes.
    """

    LEVEL_DATA = {
        1: {'gold_cap': 2000, 'member_slots': 5, 'building_slots': 1},
        2: {'gold_cap': 5000, 'member_slots': 10, 'building_slots': 2},
        3: {'gold_cap': 10000, 'member_slots': 15, 'building_slots': 3},
        4: {'gold_cap': 20000, 'member_slots': 20, 'building_slots': 4},
        5: {'gold_cap': 50000, 'member_slots': 25, 'building_slots': 5},
        6: {'gold_cap': 100000, 'member_slots': 30, 'building_slots': 6},
        7: {'gold_cap': 200000, 'member_slots': 35, 'building_slots': 7},
        8: {'gold_cap': 500000, 'member_slots': 40, 'building_slots': 8},
        9: {'gold_cap': 1000000, 'member_slots': 45, 'building_slots': 9},
        10: {'gold_cap': 5000000, 'member_slots': 50, 'building_slots': 10},
    }

    @classmethod
    def get_base_stats(cls, level):
        """Returns base stats for a given level."""
        # Default to level 1 if level is not found or invalid
        stats = cls.LEVEL_DATA.get(level, cls.LEVEL_DATA[1])
        return {
            'base_gold_cap': Decimal(stats['gold_cap']),
            'base_member_slots': stats['member_slots'],
            'base_building_slots': stats['building_slots']
        }
