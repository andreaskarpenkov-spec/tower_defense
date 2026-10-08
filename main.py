import json
import math
import os
import random
import subprocess
import sys

import pygame

pygame.init()

WIDTH, HEIGHT = 840, 640
FPS = 60
ACHIEVEMENT_CHECK_INTERVAL = 10.0
GRID_SIZE = 40
PATH_WIDTH = 36
START_MONEY = 120
START_LIVES = 8
MINE_COST = 65
MINE_DAMAGE = 160
WALKER_COST = 60
WALKER_DAMAGE = 24
FONT = pygame.font.SysFont("arial", 18)

TOWER_TYPES = {
    "basic": {
        "name": "Basic",
        "range": 140,
        "cooldown": 0.75,
        "damage": 18,
        "cost": 75,
        "color": (40, 110, 200),
        "ring": (100, 180, 240),
    },
    "warden": {
        "name": "Warden",
        "range": 180,
        "cooldown": 0.9,
        "damage": 30,
        "cost": 0,
        "win_cost": 1,
        "color": (130, 180, 110),
        "ring": (180, 240, 160),
    },
    "nova": {
        "name": "Nova",
        "range": 200,
        "cooldown": 1.3,
        "damage": 48,
        "cost": 0,
        "win_cost": 2,
        "color": (170, 110, 210),
        "ring": (220, 160, 255),
    },
    "mine_tower": {
        "name": "Mine Tower",
        "range": 170,
        "cooldown": 1.2,
        "damage": 30,
        "cost": 140,
        "color": (215, 150, 90),
        "ring": (255, 210, 150),
    },
    "rapid": {
        "name": "Rapid",
        "range": 110,
        "cooldown": 0.35,
        "damage": 10,
        "cost": 90,
        "color": (180, 180, 60),
        "ring": (220, 220, 120),
    },
    "sniper": {
        "name": "Sniper",
        "range": 220,
        "cooldown": 1.4,
        "damage": 40,
        "cost": 120,
        "color": (140, 40, 180),
        "ring": (200, 120, 230),
    },
    "freeze": {
        "name": "Freeze",
        "range": 150,
        "cooldown": 1.8,
        "damage": 8,
        "cost": 110,
        "color": (110, 190, 255),
        "ring": (170, 230, 255),
    },
    "boinger": {
        "name": "Boinger",
        "range": 170,
        "cooldown": 1.1,
        "damage": 14,
        "cost": 100,
        "color": (120, 220, 220),
        "ring": (180, 250, 255),
        "move_speed": 120,
    },
    "spawner": {
        "name": "Spawner",
        "range": 0,
        "cooldown": 1.5,
        "damage": 0,
        "cost": 0,
        "win_cost": 5,
        "color": (210, 180, 100),
        "ring": (255, 220, 150),
    },
    "gunner": {
        "name": "Runny Pew-Pew",
        "range": 155,
        "cooldown": 0.65,
        "damage": 24,
        "cost": 130,
        "color": (220, 100, 70),
        "ring": (255, 170, 130),
        "move_speed": 70,
    },
}

TOWER_UNLOCK_WAVES = {
    "basic": 1,
    "mine_tower": 99,
    "rapid": 2,
    "sniper": 3,
    "freeze": 4,
    "boinger": 5,
    "walker": 6,
    "gunner": 6,
    "mine": 2,
}

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savegame.json")
MAP_UNLOCK_COST = 20
STICKMAN_COSTUMES = {
    "classic": {"name": "Classic", "price": 0, "body": (35, 35, 48), "accent": (255, 220, 90), "shirt": (205, 65, 65), "hat": (255, 240, 180)},
}
STICKMAN_HATS = {
    "classic": {"name": "Sick-man Hat", "price": 0},
    "loser": {"name": "Loser Hat", "price": 10},
    "war": {"name": "War Helmet", "price": 5},
    "wizard": {"name": "Wizard Hat", "price": 15},
    "headphones": {"name": "Headphones", "price": 10},
    "graduation": {"name": "Graduation Hat", "price": 10},
    "bicycle": {"name": "Bicycle Helmet", "price": 10},
    "cardboard": {"name": "Cardboard Box", "price": 15},
    "powder": {"name": "Chef Hat", "price": 10},
}
STICKMAN_LEGS = {
    "classic": {"name": "Bare Feet", "price": 0},
    "hermes": {"name": "Hermes Sandals", "price": 10},
    "boots": {"name": "Boots", "price": 5},
}
STICKMAN_SUITS = {
    "classic": {"name": "Default Suit", "price": 0},
    "fish": {"name": "Fish Suit", "price": 70},
    "cactus": {"name": "Cactus Suit", "price": 45},
    "jetpack": {"name": "Jetpack", "price": 50},
}
STICKMAN_OBJECTS = {
    "none": {"name": "No Object", "price": 0},
    "magic_hat": {"name": "Magic Hat", "price": 75},
    "sword": {"name": "Sword", "price": 50},
}

ACHIEVEMENTS = {
    "developer_mode": {"name": "Hacker", "description": "Open developer mode"},
    "the_beginning": {"name": "The Beginning", "description": "Place your first tower"},
    "first_wave": {"name": "First Wave", "description": "Clear wave 1"},
    "wave_six": {"name": "Wave Six", "description": "Clear wave 6"},
    "spiral_map": {"name": "Spiral Map", "description": "Unlock the Spiral map"},
    "first_costume": {"name": "Style Check", "description": "Buy a costume item"},
    "code_rain": {"name": "Code Rain", "description": "Clear wave 3"},
    "bullet_time": {"name": "Bullet-Time Tactician", "description": "Clear wave 4 without losing a life"},
    "matrix_dodge": {"name": "Matrix Dodge", "description": "Make a flyer evade a tower"},
    "exit_construct": {"name": "Exit the Construct", "description": "Win the campaign"},
}
ACHIEVEMENT_POPUP_SECONDS = 5.0
ACHIEVEMENT_POPUPS = []


def queue_achievement_popup(achievement_id):
    if achievement_id not in ACHIEVEMENTS:
        return False
    if any(popup["achievement_id"] == achievement_id for popup in ACHIEVEMENT_POPUPS):
        return False
    ACHIEVEMENT_POPUPS.append({
        "achievement_id": achievement_id,
        "remaining": ACHIEVEMENT_POPUP_SECONDS,
    })
    return True


def award_achievement(achievements, achievement_id):
    if achievement_id not in ACHIEVEMENTS or achievement_id in achievements:
        return False
    achievements.add(achievement_id)
    queue_achievement_popup(achievement_id)
    return True


def update_achievement_popups(dt):
    for popup in ACHIEVEMENT_POPUPS:
        popup["remaining"] -= dt
    ACHIEVEMENT_POPUPS[:] = [popup for popup in ACHIEVEMENT_POPUPS if popup["remaining"] > 0]


def load_achievements():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                achievements = data.get("achievements", [])
                if isinstance(achievements, str):
                    achievements = [achievements]
                if isinstance(achievements, list):
                    return {achievement for achievement in achievements if achievement in ACHIEVEMENTS}
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return set()


def load_progress():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                unlocked = {
                    tower
                    for tower in data.get("unlocked_towers", [])
                    if tower in TOWER_UNLOCK_WAVES or tower == "basic"
                }
                win_coins = int(data.get("win_coins", 0) or 0)
                if win_coins < 0:
                    win_coins = 0
                return unlocked, win_coins
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return {"basic"}, 0


def load_developer_mode_state():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                return bool(data.get("developer_mode_opened", False))
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return False


def load_unlocks():
    unlocked_towers, _ = load_progress()
    return unlocked_towers


def load_stickman_costumes():
    default_costumes = {"classic"}
    default_equipped = "classic"
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                unlocked = {
                    costume_id for costume_id in data.get("stickman_costumes", []) if costume_id in STICKMAN_COSTUMES
                }
                if not unlocked:
                    unlocked = default_costumes.copy()
                equipped = data.get("equipped_stickman_costume", default_equipped)
                if equipped not in STICKMAN_COSTUMES or equipped not in unlocked:
                    equipped = next(iter(sorted(unlocked))) if unlocked else default_equipped
                return unlocked, equipped
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return default_costumes.copy(), default_equipped


def load_stickman_hat_text():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                text = str(data.get("stickman_hat_text", "sick-man") or "sick-man").strip()
                if text:
                    return text[:16]
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return "sick-man"


def load_stickman_hat():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict) and data.get("stickman_hat") in STICKMAN_HATS:
                return data["stickman_hat"]
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return "classic"


def load_stickman_legs():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict) and data.get("stickman_legs") in STICKMAN_LEGS:
                return data["stickman_legs"]
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return "classic"


def load_stickman_object():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict) and data.get("stickman_object") in STICKMAN_OBJECTS:
                return data["stickman_object"]
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return "none"


def load_stickman_suit():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict) and data.get("stickman_suit") in STICKMAN_SUITS:
                return data["stickman_suit"]
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return "classic"


def load_stickman_legs_unlocked():
    unlocked = {"classic"}
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                unlocked.update(leg_id for leg_id in data.get("stickman_legs_unlocked", []) if leg_id in STICKMAN_LEGS)
                equipped = data.get("stickman_legs")
                if equipped in STICKMAN_LEGS:
                    unlocked.add(equipped)
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return unlocked


def load_stickman_suits():
    unlocked = {"classic"}
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                unlocked.update(suit_id for suit_id in data.get("stickman_suits", []) if suit_id in STICKMAN_SUITS)
                equipped = data.get("stickman_suit")
                if equipped in STICKMAN_SUITS:
                    unlocked.add(equipped)
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return unlocked


def load_stickman_objects():
    unlocked = {"none"}
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                unlocked.update(object_id for object_id in data.get("stickman_objects", []) if object_id in STICKMAN_OBJECTS)
                equipped = data.get("stickman_object")
                if equipped in STICKMAN_OBJECTS:
                    unlocked.add(equipped)
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return unlocked


def load_stickman_hats():
    unlocked = {"classic"}
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                unlocked.update(hat_id for hat_id in data.get("stickman_hats", []) if hat_id in STICKMAN_HATS)
                equipped = data.get("stickman_hat")
                if equipped in STICKMAN_HATS:
                    unlocked.add(equipped)
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return unlocked


def save_unlocks(unlocked_towers, win_coins=0, unlocked_maps=None, highest_cleared_wave=None, stickman_costumes=None, equipped_stickman_costume=None, developer_mode_opened=None, stickman_hat_text=None, stickman_hat=None, stickman_hats=None, stickman_legs=None, stickman_legs_unlocked=None, stickman_suit=None, stickman_suits=None, stickman_object=None, stickman_objects=None, achievements=None):
    try:
        if unlocked_maps is None:
            unlocked_maps = load_unlocked_maps()
        if highest_cleared_wave is None:
            highest_cleared_wave = load_highest_cleared_wave()
        if achievements is None:
            achievements = load_achievements()
        if stickman_costumes is None:
            stickman_costumes, _ = load_stickman_costumes()
        if equipped_stickman_costume is None:
            _, equipped_stickman_costume = load_stickman_costumes()
        if developer_mode_opened is None:
            developer_mode_opened = load_developer_mode_state()
        if stickman_hat_text is None:
            stickman_hat_text = load_stickman_hat_text()
        if stickman_hat is None:
            stickman_hat = load_stickman_hat()
        if stickman_hat not in STICKMAN_HATS:
            stickman_hat = "classic"
        if stickman_hats is None:
            stickman_hats = load_stickman_hats()
        stickman_hats = set(stickman_hats) | {"classic", stickman_hat}
        if stickman_legs is None:
            stickman_legs = load_stickman_legs()
        if stickman_legs not in STICKMAN_LEGS:
            stickman_legs = "classic"
        if stickman_legs_unlocked is None:
            stickman_legs_unlocked = load_stickman_legs_unlocked()
        stickman_legs_unlocked = set(stickman_legs_unlocked) | {"classic", stickman_legs}
        if stickman_suit is None:
            stickman_suit = load_stickman_suit()
        if stickman_suit not in STICKMAN_SUITS:
            stickman_suit = "classic"
        if stickman_suits is None:
            stickman_suits = load_stickman_suits()
        stickman_suits = set(stickman_suits) | {"classic", stickman_suit}
        if stickman_object is None:
            stickman_object = "none"
        if stickman_object not in STICKMAN_OBJECTS:
            stickman_object = "none"
        if stickman_objects is None:
            stickman_objects = load_stickman_objects()
        stickman_objects = set(stickman_objects) | {"none", stickman_object}
        if equipped_stickman_costume not in STICKMAN_COSTUMES:
            equipped_stickman_costume = "classic"
        achievements = {achievement for achievement in set(achievements) if achievement in ACHIEVEMENTS}
        with open(SAVE_FILE, "w", encoding="utf-8") as save_file:
            json.dump(
                {
                    "unlocked_towers": sorted(unlocked_towers),
                    "win_coins": int(win_coins),
                    "unlocked_maps": sorted(unlocked_maps),
                    "highest_cleared_wave": int(highest_cleared_wave),
                    "stickman_costumes": sorted(stickman_costumes),
                    "equipped_stickman_costume": equipped_stickman_costume,
                    "stickman_hat_text": str(stickman_hat_text or "sick-man")[:16],
                    "stickman_hat": stickman_hat,
                    "stickman_hats": sorted(stickman_hats),
                    "stickman_legs": stickman_legs,
                    "stickman_legs_unlocked": sorted(stickman_legs_unlocked),
                    "stickman_suit": stickman_suit,
                    "stickman_suits": sorted(stickman_suits),
                    "stickman_object": stickman_object,
                    "stickman_objects": sorted(stickman_objects),
                    "developer_mode_opened": bool(developer_mode_opened),
                    "achievements": sorted(achievements),
                },
                save_file,
            )
    except OSError:
        pass


def check_achievements(game=None):
    achievements = load_achievements()
    highest_cleared_wave = load_highest_cleared_wave()
    if game is not None and not game.sandbox:
        highest_cleared_wave = max(highest_cleared_wave, game.highest_cleared_wave)

    if load_developer_mode_state():
        award_achievement(achievements, "developer_mode")
    if highest_cleared_wave >= 1:
        award_achievement(achievements, "first_wave")
    if highest_cleared_wave >= 6:
        award_achievement(achievements, "wave_six")
    if highest_cleared_wave >= 3:
        award_achievement(achievements, "code_rain")
    if game is not None and not game.sandbox and game.victory:
        award_achievement(achievements, "exit_construct")
    if "Spiral" in load_unlocked_maps():
        award_achievement(achievements, "spiral_map")
    if (
        load_stickman_costumes()[0] - {"classic"}
        or load_stickman_hats() - {"classic"}
        or load_stickman_legs_unlocked() - {"classic"}
        or load_stickman_suits() - {"classic"}
        or load_stickman_objects() - {"none"}
    ):
        award_achievement(achievements, "first_costume")

    if game is not None:
        game.achievements = set(achievements)
    if achievements != load_achievements():
        unlocked_towers, saved_win_coins = load_progress()
        save_unlocks(
            game.unlocked_towers if game is not None and not game.sandbox else unlocked_towers,
            game.win_coins if game is not None and not game.sandbox else saved_win_coins,
            load_unlocked_maps(),
            highest_cleared_wave=highest_cleared_wave,
            achievements=achievements,
        )
    return achievements


def update_achievement_check_timer(elapsed, dt, game=None):
    elapsed += dt
    if elapsed >= ACHIEVEMENT_CHECK_INTERVAL:
        check_achievements(game)
        elapsed %= ACHIEVEMENT_CHECK_INTERVAL
    return elapsed


MAPS = {
    "Classic": [
        (0, 200),
        (280, 200),
        (280, 480),
        (560, 480),
        (560, 140),
        (840, 140),
    ],
    "Loop": [
        (0, 320),
        (160, 320),
        (160, 160),
        (520, 160),
        (520, 480),
        (320, 480),
        (320, 240),
        (840, 240),
    ],
    "Cross": [
        (0, 320),
        (260, 320),
        (260, 120),
        (420, 120),
        (420, 520),
        (580, 520),
        (580, 320),
        (840, 320),
    ],
    "Spiral": [
        (0, 120),
        (720, 120),
        (720, 520),
        (120, 520),
        (120, 240),
        (600, 240),
        (600, 400),
        (280, 400),
        (280, 320),
        (840, 320),
    ],
}

MAP_BACKGROUNDS = {
    "Classic": (20, 25, 35),
    "Loop": (18, 30, 24),
    "Cross": (28, 22, 38),
    "Spiral": (40, 90, 55),
}

DEFAULT_MAP = "Classic"
FREE_MAPS = {"Classic", "Loop", "Cross"}
SPIRAL_BUY_RECT = pygame.Rect(300, 195, 90, 26)
BACKSTORY_RECT = pygame.Rect(40, 390, 180, 42)
HOME_COSTUMES_RECT = pygame.Rect(240, 390, 180, 42)
ACHIEVEMENTS_BUTTON_RECT = pygame.Rect(440, 285, 220, 42)
HOME_COSTUME_WINDOW_RECT = pygame.Rect(120, 70, 600, 560)
HOME_COSTUME_CLOSE_RECT = pygame.Rect(650, 84, 52, 24)


def load_unlocked_maps():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                saved_maps = data.get("unlocked_maps", [])
                return FREE_MAPS | {map_name for map_name in saved_maps if map_name in MAPS}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return set(FREE_MAPS)


def load_highest_cleared_wave():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as save_file:
            data = json.load(save_file)
            if isinstance(data, dict):
                highest_cleared_wave = int(data.get("highest_cleared_wave", 0) or 0)
                if 0 <= highest_cleared_wave <= len(WAVES):
                    return highest_cleared_wave
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return 0

WAVES = [
    {"count": 5, "speed": 4.0, "hp": 180, "reward": 18},
    {"count": 7, "speed": 5.0, "hp": 230, "reward": 24},
    {"count": 9, "speed": 6.0, "hp": 300, "reward": 28},
    {"count": 12, "speed": 7.2, "hp": 390, "reward": 34},
    {"count": 15, "speed": 8.5, "hp": 520, "reward": 42},
    {"count": 18, "speed": 9.5, "hp": 650, "reward": 50},
]

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Tower Defense")
CLOCK = pygame.time.Clock()


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def draw_sword(surface, hand_x, hand_y, facing=1, scale=1.0):
    direction_x = facing * 0.62
    direction_y = -0.78
    perpendicular_x = -direction_y
    perpendicular_y = direction_x

    def point(distance, offset=0):
        return (
            round(hand_x + direction_x * distance * scale + perpendicular_x * offset * scale),
            round(hand_y + direction_y * distance * scale + perpendicular_y * offset * scale),
        )

    blade_base = point(9)
    blade_tip = point(52)
    blade_points = [blade_base, point(52, 4), blade_tip, point(52, -4)]
    pygame.draw.polygon(surface, (75, 85, 105), blade_points)
    pygame.draw.polygon(surface, (205, 220, 235), [blade_base, point(52, 2), blade_tip, point(52, -2)])
    pygame.draw.line(surface, (255, 255, 255), point(12, 1), point(47, 1), max(1, round(2 * scale)))
    pygame.draw.line(surface, (135, 95, 55), point(-14), point(7), max(1, round(8 * scale)))
    pygame.draw.line(surface, (210, 170, 100), point(9, -12), point(9, 12), max(2, round(4 * scale)))
    pygame.draw.circle(surface, (225, 185, 110), point(-15), max(2, round(4 * scale)))


def draw_stickman_preview(surface, center_x, center_y, costume_id, facing=1, hat_id="classic", hat_text="sick-man", leg_id="classic", suit_id="classic", object_id="none"):
    costume = STICKMAN_COSTUMES.get(costume_id, STICKMAN_COSTUMES["classic"])
    x = int(center_x)
    y = int(center_y)
    ink = (250, 250, 250)
    accent = costume["accent"]
    if suit_id == "jetpack":
        pygame.draw.rect(surface, (110, 120, 140), (x - 12, y - 38, 24, 23), border_radius=5)
        pygame.draw.rect(surface, (255, 180, 80), (x - 8, y - 6, 4, 10), border_radius=2)
        pygame.draw.rect(surface, (255, 180, 80), (x + 4, y - 6, 4, 10), border_radius=2)
    elif suit_id == "cactus":
        pygame.draw.rect(surface, (80, 180, 90), (x - 12, y - 12, 24, 32), border_radius=5)
        for spine_x in (-8, -3, 3, 8):
            pygame.draw.line(surface, (120, 220, 110), (x + spine_x, y - 9), (x + spine_x, y + 16), 1)
    elif suit_id == "fish":
        pygame.draw.rect(surface, (80, 160, 220), (x - 12, y - 18, 24, 32), border_radius=7)
        pygame.draw.polygon(surface, (140, 220, 255), [(x + 10, y - 5), (x + 19, y - 1), (x + 10, y + 4)])
        pygame.draw.line(surface, (210, 235, 255), (x - 5, y - 5), (x + 5, y - 5), 1)
        pygame.draw.line(surface, (210, 235, 255), (x - 5, y + 5), (x + 5, y + 5), 1)
    if object_id == "magic_hat":
        off_x = x + 18
        off_y = y - 10
        pygame.draw.circle(surface, (220, 140, 255), (off_x, off_y - 8), 10)
        pygame.draw.polygon(surface, (255, 180, 255), [(off_x - 10, off_y - 6), (off_x + 10, off_y - 6), (off_x + 4, off_y - 22), (off_x - 4, off_y - 22)])
        pygame.draw.line(surface, (245, 235, 255), (x + 12, y - 4), (off_x, off_y - 4), 2)
        for spark in [(off_x - 8, off_y - 18), (off_x + 4, off_y - 20), (off_x + 10, off_y - 14)]:
            pygame.draw.circle(surface, (255, 255, 255), spark, 2)
    elif object_id == "sword":
        draw_sword(surface, x + facing * 13, y - 12, facing)
    pygame.draw.circle(surface, accent, (x, y - 42), 17)
    pygame.draw.circle(surface, ink, (x, y - 42), 17, 3)
    if hat_id == "loser":
        pygame.draw.polygon(surface, (125, 125, 135), [(x - 20, y - 65), (x + 20, y - 65), (x, y - 103)])
        pygame.draw.ellipse(surface, (80, 80, 90), (x - 26, y - 70, 52, 13))
        rendered_hat_text = pygame.font.SysFont("arial", 12, bold=True).render("L", True, (230, 230, 240))
        surface.blit(rendered_hat_text, (x - rendered_hat_text.get_width() // 2, y - 81))
    elif hat_id == "war":
        pygame.draw.ellipse(surface, (85, 95, 110), (x - 28, y - 78, 56, 28))
        pygame.draw.rect(surface, (125, 135, 150), (x - 31, y - 69, 62, 10), border_radius=4)
        pygame.draw.polygon(surface, (210, 70, 70), [(x - 5, y - 78), (x, y - 94), (x + 5, y - 78)])
    elif hat_id == "wizard":
        pygame.draw.polygon(surface, (75, 45, 125), [(x - 22, y - 66), (x + 22, y - 66), (x + 4, y - 108), (x - 5, y - 108)])
        pygame.draw.ellipse(surface, (45, 25, 80), (x - 27, y - 71, 54, 13))
        pygame.draw.circle(surface, (245, 220, 90), (x - 7, y - 79), 3)
    elif hat_id == "headphones":
        pygame.draw.arc(surface, (70, 190, 220), (x - 28, y - 75, 56, 48), 0, math.pi, 5)
        pygame.draw.rect(surface, (70, 190, 220), (x - 31, y - 55, 9, 20), border_radius=4)
        pygame.draw.rect(surface, (70, 190, 220), (x + 22, y - 55, 9, 20), border_radius=4)
    elif hat_id == "graduation":
        pygame.draw.polygon(surface, (35, 35, 45), [(x - 30, y - 71), (x, y - 84), (x + 30, y - 71), (x, y - 58)])
        pygame.draw.rect(surface, (55, 55, 65), (x - 17, y - 65, 34, 12))
        pygame.draw.line(surface, (245, 210, 80), (x + 20, y - 70), (x + 26, y - 47), 2)
        pygame.draw.circle(surface, (245, 210, 80), (x + 26, y - 45), 3)
    elif hat_id == "bicycle":
        pygame.draw.ellipse(surface, (235, 70, 55), (x - 27, y - 80, 54, 30))
        pygame.draw.rect(surface, (245, 220, 90), (x - 29, y - 68, 58, 8), border_radius=4)
        pygame.draw.line(surface, (170, 40, 35), (x - 12, y - 80), (x - 18, y - 68), 3)
        pygame.draw.line(surface, (170, 40, 35), (x + 4, y - 80), (x + 10, y - 68), 3)
    elif hat_id == "cardboard":
        pygame.draw.rect(surface, (170, 115, 55), (x - 28, y - 88, 56, 30), border_radius=2)
        pygame.draw.line(surface, (115, 75, 35), (x, y - 88), (x, y - 58), 2)
        pygame.draw.line(surface, (115, 75, 35), (x - 28, y - 73), (x + 28, y - 73), 2)
    elif hat_id == "powder":
        pygame.draw.circle(surface, (245, 245, 240), (x - 18, y - 74), 15)
        pygame.draw.circle(surface, (245, 245, 240), (x, y - 82), 17)
        pygame.draw.circle(surface, (245, 245, 240), (x + 18, y - 74), 15)
        pygame.draw.ellipse(surface, (225, 225, 220), (x - 30, y - 72, 60, 13))
    else:
        pygame.draw.ellipse(surface, (25, 25, 35), (x - 34, y - 67, 68, 13))
        pygame.draw.rect(surface, costume["body"], (x - 28, y - 89, 56, 29), border_radius=5)
        pygame.draw.rect(surface, costume["shirt"], (x - 28, y - 68, 56, 9))
        rendered_hat_text = pygame.font.SysFont("arial", 11, bold=True).render(hat_text, True, costume["hat"])
        surface.blit(rendered_hat_text, (x - rendered_hat_text.get_width() // 2, y - 70))
    pygame.draw.line(surface, ink, (x, y - 25), (x, y + 25), 5)
    pygame.draw.line(surface, ink, (x, y - 9), (x - facing * 28, y + 10), 5)
    pygame.draw.line(surface, ink, (x, y - 9), (x + facing * 28, y - 24), 5)
    pygame.draw.line(surface, ink, (x, y + 25), (x - facing * 22, y + 58), 5)
    pygame.draw.line(surface, ink, (x, y + 25), (x + facing * 22, y + 58), 5)
    if leg_id == "hermes":
        pygame.draw.ellipse(surface, (120, 95, 70), (x - 24, y + 58, 18, 9))
        pygame.draw.ellipse(surface, (120, 95, 70), (x + 6, y + 58, 18, 9))
        pygame.draw.line(surface, (120, 95, 70), (x - 17, y + 58), (x - 12, y + 38), 3)
        pygame.draw.line(surface, (120, 95, 70), (x + 17, y + 58), (x + 12, y + 38), 3)
        pygame.draw.polygon(surface, (210, 215, 255), [(x - 22, y + 44), (x - 8, y + 38), (x - 14, y + 52)])
        pygame.draw.polygon(surface, (210, 215, 255), [(x + 18, y + 44), (x + 4, y + 38), (x + 12, y + 52)])
    elif leg_id == "boots":
        pygame.draw.rect(surface, (85, 55, 45), (x - 20, y + 56, 16, 12), border_radius=2)
        pygame.draw.rect(surface, (85, 55, 45), (x + 4, y + 56, 16, 12), border_radius=2)
    pygame.draw.circle(surface, accent, (x - 6, y - 46), 2)
    pygame.draw.circle(surface, accent, (x + 6, y - 46), 2)


class Enemy:
    def __init__(self, path_points, speed, hp, reward, enemy_type="ground"):
        self.path = path_points
        self.base_speed = speed
        self.speed = speed
        self.max_hp = hp
        self.hp = hp
        self.reward = reward
        self.type = enemy_type
        self.segment = 0
        self.x, self.y = self.path[0]
        self.finished = False
        self.cooldown = 0.9
        self.time_since_shot = 0.0
        self.attack_damage = 15
        self.projectiles = []
        self.slow_timer = 0.0
        self.slow_amount = 1.0
        self.loser_hat = False
        self.dodged_tower = False

    def update(self, dt, towers):
        if self.finished:
            return
        if self.slow_timer > 0:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.slow_timer = 0.0
                self.slow_amount = 1.0
        self.speed = self.base_speed * self.slow_amount
        if self.segment >= len(self.path) - 1:
            self.finished = True
            return

        tx, ty = self.path[self.segment + 1]
        dx, dy = tx - self.x, ty - self.y
        distance = math.hypot(dx, dy)
        if distance == 0:
            self.segment += 1
            return

        if self.type == "flyer":
            dir_x, dir_y = dx / distance, dy / distance
            avoid_x = 0.0
            avoid_y = 0.0
            for tower in towers:
                tx_dist = tower.x - self.x
                ty_dist = tower.y - self.y
                tower_dist = math.hypot(tx_dist, ty_dist)
                danger_radius = tower.range + 24
                if 0 < tower_dist < danger_radius:
                    self.dodged_tower = True
                    strength = (danger_radius - tower_dist) / danger_radius
                    avoid_x -= (tx_dist / tower_dist) * strength * 70
                    avoid_y -= (ty_dist / tower_dist) * strength * 70
            steer_x = dir_x * 1.2 + avoid_x
            steer_y = dir_y * 1.2 + avoid_y
            steer_dist = math.hypot(steer_x, steer_y)
            if steer_dist < 0.1:
                steer_x, steer_y = dir_x, dir_y
                steer_dist = math.hypot(steer_x, steer_y)
            dir_x = steer_x / steer_dist
            dir_y = steer_y / steer_dist
            step = self.speed * dt
            self.x += dir_x * step
            self.y += dir_y * step
            if math.hypot(self.x - tx, self.y - ty) < 18:
                self.segment += 1
            self.x = clamp(self.x, 0, WIDTH)
            self.y = clamp(self.y, 0, HEIGHT)
            return

        if self.type == "shooter":
            self.time_since_shot += dt
            if self.time_since_shot >= self.cooldown:
                self.time_since_shot = 0.0
                if towers:
                    eligible_towers = [tower for tower in towers if not tower.shooter_immunity]
                    if eligible_towers:
                        target_tower = min(eligible_towers, key=lambda tower: math.hypot(tower.x - self.x, tower.y - self.y))
                        self.projectiles.append(ShooterProjectile(self.x, self.y, target_tower, self.attack_damage))
            step = self.speed * dt
            if step >= distance:
                self.x, self.y = tx, ty
                self.segment += 1
            else:
                self.x += dx / distance * step
                self.y += dy / distance * step
            return

        step = self.speed * dt
        if step >= distance:
            self.x, self.y = tx, ty
            self.segment += 1
        else:
            self.x += dx / distance * step
            self.y += dy / distance * step

    def draw(self, surface):
        center_x, center_y = int(self.x), int(self.y)
        if self.type == "flyer":
            wing_color = (70, 150, 155)
            body_color = (115, 205, 210)
            pygame.draw.polygon(
                surface,
                wing_color,
                [(center_x - 8, center_y), (center_x - 25, center_y - 10), (center_x - 18, center_y + 8)],
            )
            pygame.draw.polygon(
                surface,
                wing_color,
                [(center_x + 8, center_y), (center_x + 25, center_y - 10), (center_x + 18, center_y + 8)],
            )
            pygame.draw.circle(surface, body_color, (center_x, center_y), 13)
            pygame.draw.polygon(
                surface,
                (45, 105, 110),
                [(center_x - 7, center_y - 10), (center_x, center_y - 20), (center_x + 7, center_y - 10)],
            )
            eye_color = (255, 245, 150)
        elif self.type == "shooter":
            body_color = (190, 105, 55)
            pygame.draw.polygon(
                surface,
                (105, 55, 35),
                [(center_x - 14, center_y - 8), (center_x - 8, center_y - 17), (center_x, center_y - 12),
                 (center_x + 8, center_y - 17), (center_x + 14, center_y - 8), (center_x + 11, center_y + 12),
                 (center_x, center_y + 18), (center_x - 11, center_y + 12)],
            )
            pygame.draw.circle(surface, body_color, (center_x, center_y), 12)
            pygame.draw.line(surface, (70, 35, 25), (center_x + 8, center_y + 5), (center_x + 22, center_y + 1), 5)
            eye_color = (255, 220, 100)
        else:
            pygame.draw.polygon(
                surface,
                (125, 35, 45),
                [(center_x - 14, center_y - 5), (center_x - 11, center_y - 18), (center_x - 4, center_y - 12),
                 (center_x, center_y - 22), (center_x + 5, center_y - 12), (center_x + 13, center_y - 18),
                 (center_x + 14, center_y + 8), (center_x + 5, center_y + 17), (center_x - 7, center_y + 15)],
            )
            pygame.draw.circle(surface, (215, 55, 65), (center_x, center_y), 12)
            eye_color = (255, 235, 120)

        pygame.draw.circle(surface, eye_color, (center_x - 5, center_y - 3), 3)
        pygame.draw.circle(surface, eye_color, (center_x + 5, center_y - 3), 3)
        pygame.draw.circle(surface, (35, 25, 25), (center_x - 5, center_y - 3), 1)
        pygame.draw.circle(surface, (35, 25, 25), (center_x + 5, center_y - 3), 1)
        pygame.draw.arc(surface, (45, 20, 20), (center_x - 7, center_y + 1, 14, 9), 0.2, math.pi - 0.2, 2)
        if self.loser_hat:
            pygame.draw.polygon(
                surface,
                (125, 125, 135),
                [(center_x - 10, center_y - 30), (center_x + 10, center_y - 30), (center_x, center_y - 52)],
            )
            pygame.draw.ellipse(surface, (80, 80, 90), (center_x - 13, center_y - 33, 26, 7))
            loser_text = pygame.font.SysFont("arial", 8, bold=True).render("L", True, (230, 230, 240))
            surface.blit(loser_text, (center_x - loser_text.get_width() // 2, center_y - 40))
        for projectile in self.projectiles:
            projectile.draw(surface)
        hp_ratio = self.hp / self.max_hp
        bar_width = 24
        bar_height = 4
        bar_x = self.x - bar_width / 2
        bar_y = self.y - 20
        pygame.draw.rect(surface, (40, 40, 40), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2))
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (80, 200, 80), (bar_x, bar_y, bar_width * hp_ratio, bar_height))

    def is_dead(self):
        return self.hp <= 0

    def reached_goal(self):
        return self.finished


class Tower:
    def __init__(self, x, y, tower_type="basic", path_points=None):
        self.x = x
        self.y = y
        self.type = tower_type
        self.range = TOWER_TYPES[tower_type]["range"]
        self.cooldown = TOWER_TYPES[tower_type]["cooldown"]
        self.damage = TOWER_TYPES[tower_type]["damage"]
        self.color = TOWER_TYPES[tower_type]["color"]
        self.ring = TOWER_TYPES[tower_type]["ring"]
        self.time_since_shot = 0.0
        self.aim_angle = -math.pi / 2
        self.target = None
        if self.type == "spawner":
            self.spawn_timer = 0.0
        self.health = 120
        self.shooter_immunity = False
        if self.type == "boinger":
            self.move_speed = TOWER_TYPES[self.type]["move_speed"]
            angle = random.uniform(0, math.tau)
            self.vx = math.cos(angle) * self.move_speed
            self.vy = math.sin(angle) * self.move_speed
        if self.type == "gunner":
            self.path_points = path_points or []
            self.move_speed = TOWER_TYPES[self.type]["move_speed"]
            self.path_segment = 0
            if len(self.path_points) > 1:
                closest_distance = float("inf")
                for index in range(len(self.path_points) - 1):
                    start_x, start_y = self.path_points[index]
                    end_x, end_y = self.path_points[index + 1]
                    distance, progress = self._segment_projection(
                        self.x, self.y, start_x, start_y, end_x, end_y
                    )
                    if distance <= closest_distance:
                        closest_distance = distance
                        self.path_segment = index
                        self.x = start_x + (end_x - start_x) * progress
                        self.y = start_y + (end_y - start_y) * progress

    def _distance_to_segment(self, px, py, x1, y1, x2, y2):
        distance, _ = self._segment_projection(px, py, x1, y1, x2, y2)
        return distance

    def _segment_projection(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1), 0.0
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        return math.hypot(px - closest_x, py - closest_y), t

    def is_dead(self):
        return self.health <= 0

    def update(self, dt, enemies):
        if self.type == "spawner":
            self.spawn_timer += dt
            if self.spawn_timer >= self.cooldown:
                self.spawn_timer = 0.0
                return "spawn_walker"
            return None

        if self.type == "gunner" and len(self.path_points) > 1:
            target_x, target_y = self.path_points[self.path_segment + 1]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.hypot(dx, dy)
            step = self.move_speed * dt
            if distance <= step or distance == 0:
                self.x, self.y = target_x, target_y
                self.path_segment += 1
                if self.path_segment >= len(self.path_points) - 1:
                    self.path_segment = 0
                    self.x, self.y = self.path_points[0]
            else:
                self.x += dx / distance * step
                self.y += dy / distance * step

        if self.type in ("flyer", "boinger"):
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.x <= GRID_SIZE // 2 or self.x >= WIDTH - GRID_SIZE // 2:
                self.vx *= -1
                self.x = clamp(self.x, GRID_SIZE // 2, WIDTH - GRID_SIZE // 2)
            if self.y <= GRID_SIZE // 2 or self.y >= HEIGHT - GRID_SIZE // 2:
                self.vy *= -1
                self.y = clamp(self.y, GRID_SIZE // 2, HEIGHT - GRID_SIZE // 2)

        self.time_since_shot += dt
        if self.time_since_shot < self.cooldown:
            return None

        nearest = None
        best_dist = float("inf")
        for enemy in enemies:
            if enemy.is_dead() or enemy.reached_goal():
                continue
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            dist = math.hypot(dx, dy)
            if dist <= self.range and dist < best_dist:
                nearest = enemy
                best_dist = dist

        if nearest:
            self.target = nearest
            dx = nearest.x - self.x
            dy = nearest.y - self.y
            self.aim_angle = math.atan2(dy, dx)
            self.time_since_shot = 0.0
            if self.type == "freeze":
                return FreezeProjectile(self.x, self.y, nearest, self.damage, self.color)
            if self.type == "mine_tower":
                return BombProjectile(self.x, self.y, nearest, self.damage, self.color, enemies=enemies)
            return Projectile(self.x, self.y, nearest, self.damage, self.color)
        self.target = None
        return None

    def draw(self, surface, show_range=True):
        base_x, base_y = int(self.x), int(self.y)
        pygame.draw.circle(surface, (20, 20, 20), (base_x, base_y + 3), 18)
        pygame.draw.circle(surface, (50, 50, 50), (base_x, base_y), 16)
        pygame.draw.circle(surface, self.color, (base_x, base_y), 12)
        if self.shooter_immunity:
            pygame.draw.circle(surface, (180, 255, 180), (base_x, base_y), 14, 2)
        if self.health < 120:
            health_ratio = self.health / 120
            pygame.draw.rect(surface, (60, 60, 60), (base_x - 14, base_y - 28, 28, 4))
            pygame.draw.rect(surface, (80, 220, 80), (base_x - 14, base_y - 28, 28 * health_ratio, 4))

        if self.type == "basic":
            pygame.draw.rect(surface, (70, 80, 96), (base_x - 8, base_y - 12, 16, 20))
            pygame.draw.rect(surface, (120, 140, 170), (base_x - 6, base_y - 10, 12, 16))
            barrel_end_x = base_x + int(math.cos(self.aim_angle) * 18)
            barrel_end_y = base_y + int(math.sin(self.aim_angle) * 18)
            pygame.draw.line(surface, (220, 230, 240), (base_x, base_y - 2), (barrel_end_x, barrel_end_y), 3)
        elif self.type == "rapid":
            pygame.draw.rect(surface, (90, 90, 60), (base_x - 10, base_y - 12, 20, 22))
            pygame.draw.rect(surface, (150, 150, 90), (base_x - 8, base_y - 10, 16, 18))
            barrel_end_x = base_x + int(math.cos(self.aim_angle) * 16)
            barrel_end_y = base_y + int(math.sin(self.aim_angle) * 16)
            pygame.draw.line(surface, (255, 255, 180), (base_x - 3, base_y - 2), (barrel_end_x - 3, barrel_end_y), 3)
            pygame.draw.line(surface, (255, 255, 180), (base_x + 3, base_y - 2), (barrel_end_x + 3, barrel_end_y), 3)
        elif self.type == "sniper":
            pygame.draw.rect(surface, (70, 40, 90), (base_x - 8, base_y - 12, 16, 22))
            pygame.draw.rect(surface, (140, 70, 170), (base_x - 6, base_y - 10, 12, 18))
            barrel_end_x = base_x + int(math.cos(self.aim_angle) * 24)
            barrel_end_y = base_y + int(math.sin(self.aim_angle) * 24)
            pygame.draw.line(surface, (240, 180, 255), (base_x, base_y - 2), (barrel_end_x, barrel_end_y), 4)
        elif self.type == "freeze":
            pygame.draw.rect(surface, (60, 100, 150), (base_x - 10, base_y - 14, 20, 24))
            pygame.draw.rect(surface, (150, 220, 255), (base_x - 8, base_y - 12, 16, 20))
            barrel_end_x = base_x + int(math.cos(self.aim_angle) * 18)
            barrel_end_y = base_y + int(math.sin(self.aim_angle) * 18)
            pygame.draw.line(surface, (180, 240, 255), (base_x, base_y - 2), (barrel_end_x, barrel_end_y), 4)
            pygame.draw.circle(surface, (220, 250, 255), (base_x, base_y - 12), 5)
        elif self.type == "warden":
            pygame.draw.rect(surface, (25, 50, 25), (base_x - 12, base_y - 14, 24, 28))
            pygame.draw.rect(surface, (100, 170, 90), (base_x - 10, base_y - 12, 20, 24))
            pygame.draw.arc(surface, (170, 240, 160), (base_x - 16, base_y - 18, 32, 32), math.pi * 0.15, math.pi * 1.85, 3)
            pygame.draw.line(surface, (200, 255, 200), (base_x, base_y - 14), (base_x + int(math.cos(self.aim_angle) * 18), base_y + int(math.sin(self.aim_angle) * 18)), 3)
            pygame.draw.circle(surface, (200, 255, 200), (base_x, base_y - 16), 4)
        elif self.type == "nova":
            for i in range(4):
                angle = self.aim_angle + i * (math.pi / 2)
                ray_x = base_x + int(math.cos(angle) * 14)
                ray_y = base_y + int(math.sin(angle) * 14)
                pygame.draw.line(surface, (220, 170, 255), (base_x, base_y), (ray_x, ray_y), 2)
            pygame.draw.circle(surface, (100, 60, 150), (base_x, base_y), 14)
            pygame.draw.circle(surface, (220, 160, 255), (base_x, base_y), 9)
            pygame.draw.circle(surface, (255, 240, 255), (base_x, base_y), 4)
            barrel_end_x = base_x + int(math.cos(self.aim_angle) * 18)
            barrel_end_y = base_y + int(math.sin(self.aim_angle) * 18)
            pygame.draw.line(surface, (255, 210, 255), (base_x, base_y), (barrel_end_x, barrel_end_y), 3)
        elif self.type == "mine_tower":
            pygame.draw.rect(surface, (90, 70, 50), (base_x - 10, base_y - 12, 20, 22))
            pygame.draw.rect(surface, (150, 110, 70), (base_x - 8, base_y - 10, 16, 18))
            barrel_end_x = base_x + int(math.cos(self.aim_angle) * 16)
            barrel_end_y = base_y + int(math.sin(self.aim_angle) * 16)
            pygame.draw.line(surface, (80, 60, 45), (base_x, base_y - 1), (barrel_end_x, barrel_end_y), 3)
            pygame.draw.circle(surface, (255, 140, 70), (base_x + int(math.cos(self.aim_angle) * 10), base_y + int(math.sin(self.aim_angle) * 10)), 6)
        elif self.type == "spawner":
            pygame.draw.rect(surface, (180, 150, 70), (base_x - 12, base_y - 12, 24, 24))
            pygame.draw.rect(surface, (220, 190, 120), (base_x - 9, base_y - 9, 18, 18))
            for i in range(4):
                angle = (self.aim_angle + i * math.pi / 2)
                exit_x = base_x + int(math.cos(angle) * 10)
                exit_y = base_y + int(math.sin(angle) * 10)
                pygame.draw.circle(surface, (255, 220, 150), (exit_x, exit_y), 4)
        elif self.type == "gunner":
            pygame.draw.rect(surface, (90, 45, 35), (base_x - 11, base_y - 12, 22, 24))
            pygame.draw.rect(surface, (220, 100, 70), (base_x - 8, base_y - 10, 16, 20))
            barrel_end_x = base_x + int(math.cos(self.aim_angle) * 23)
            barrel_end_y = base_y + int(math.sin(self.aim_angle) * 23)
            pygame.draw.line(surface, (255, 220, 170), (base_x, base_y - 2), (barrel_end_x, barrel_end_y), 5)
            pygame.draw.circle(surface, (255, 230, 180), (base_x, base_y - 12), 5)
        if self.type in ("flyer", "boinger"):
            pygame.draw.polygon(surface, (100, 200, 200), [
                (base_x - 12, base_y),
                (base_x + 12, base_y - 8),
                (base_x + 12, base_y + 8),
            ])
            pygame.draw.circle(surface, (160, 240, 240), (base_x, base_y), 10)
            barrel_end_x = base_x + int(math.cos(self.aim_angle) * 18)
            barrel_end_y = base_y + int(math.sin(self.aim_angle) * 18)
            pygame.draw.line(surface, (220, 255, 255), (base_x, base_y), (barrel_end_x, barrel_end_y), 3)

        if show_range:
            pygame.draw.circle(surface, self.ring, (base_x, base_y), self.range, 1)


class Projectile:
    def __init__(self, x, y, target, damage, color, speed=520):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.color = color
        self.speed = speed
        self.active = True

    def update(self, dt):
        if not self.active or self.target.is_dead() or self.target.reached_goal():
            self.active = False
            return False

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.hypot(dx, dy)
        if distance <= 6 or distance == 0:
            self.target.hp -= self.damage
            self.active = False
            return False

        step = self.speed * dt
        if step >= distance:
            self.x, self.y = self.target.x, self.target.y
            self.target.hp -= self.damage
            self.active = False
            return False
        self.x += dx / distance * step
        self.y += dy / distance * step
        return True

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 5)


class FreezeProjectile(Projectile):
    def __init__(self, x, y, target, damage, color, speed=420, slow_amount=0.4, slow_time=2.2):
        super().__init__(x, y, target, damage, color, speed)
        self.slow_amount = slow_amount
        self.slow_time = slow_time

    def update(self, dt):
        if not self.active or self.target.is_dead() or self.target.reached_goal():
            self.active = False
            return False

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.hypot(dx, dy)
        if distance <= 6 or distance == 0:
            self.target.hp -= self.damage
            self.target.slow_amount = self.slow_amount
            self.target.slow_timer = self.slow_time
            self.active = False
            return False

        step = self.speed * dt
        if step >= distance:
            self.x, self.y = self.target.x, self.target.y
            self.target.hp -= self.damage
            self.target.slow_amount = self.slow_amount
            self.target.slow_timer = self.slow_time
            self.active = False
            return False
        self.x += dx / distance * step
        self.y += dy / distance * step
        return True

    def draw(self, surface):
        pygame.draw.circle(surface, (140, 220, 255), (int(self.x), int(self.y)), 5)
        pygame.draw.circle(surface, (220, 250, 255), (int(self.x), int(self.y)), 2)


class ShooterProjectile:
    def __init__(self, x, y, target, damage, speed=320):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.speed = speed
        self.active = True

    def update(self, dt):
        if not self.active or self.target is None or self.target.is_dead():
            self.active = False
            return False
        if hasattr(self.target, "reached_goal") and self.target.reached_goal():
            self.active = False
            return False

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.hypot(dx, dy)
        if distance <= 6 or distance == 0:
            if hasattr(self.target, "health"):
                self.target.health -= self.damage
            else:
                self.target.hp -= self.damage
            self.active = False
            return False

        step = self.speed * dt
        if step >= distance:
            self.x, self.y = self.target.x, self.target.y
            if hasattr(self.target, "health"):
                self.target.health -= self.damage
            else:
                self.target.hp -= self.damage
            self.active = False
            return False
        self.x += dx / distance * step
        self.y += dy / distance * step
        return True

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 120, 60), (int(self.x), int(self.y)), 4)
        pygame.draw.circle(surface, (255, 190, 120), (int(self.x), int(self.y)), 2)


class Explosion:
    def __init__(self, x, y, radius=52, damage=0, color=(255, 150, 80), duration=0.35):
        self.x = x
        self.y = y
        self.radius = radius
        self.damage = damage
        self.color = color
        self.duration = duration
        self.time = 0.0
        self.active = True

    def update(self, dt):
        self.time += dt
        if self.time >= self.duration:
            self.active = False
            return False
        return True

    def draw(self, surface):
        progress = min(self.time / max(self.duration, 0.001), 1.0)
        glow_radius = int(self.radius * (0.2 + progress * 0.9))
        alpha = max(0, 255 - int(progress * 230))
        flash = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(flash, (self.color[0], self.color[1], self.color[2], alpha), (glow_radius, glow_radius), glow_radius)
        surface.blit(flash, (self.x - glow_radius, self.y - glow_radius))
        pygame.draw.circle(surface, (255, 220, 160), (int(self.x), int(self.y)), max(4, int(glow_radius * 0.18)))


class BombProjectile:
    def __init__(self, x, y, target, damage, color, speed=260, splash_radius=52, enemies=None):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.color = color
        self.speed = speed
        self.splash_radius = splash_radius
        self.enemies = enemies or []
        self.active = True
        self.explosion = None
        self.trail = []
        self.trail_timer = 0.0

    def _apply_damage(self, enemy):
        if enemy is None or enemy.is_dead() or enemy.reached_goal():
            return
        if hasattr(enemy, "health"):
            enemy.health -= self.damage
        else:
            enemy.hp -= self.damage

    def _explode(self):
        if self.target is not None:
            self._apply_damage(self.target)
        for enemy in self.enemies:
            if enemy is self.target:
                continue
            if enemy.is_dead() or enemy.reached_goal():
                continue
            if math.hypot(enemy.x - self.x, enemy.y - self.y) <= self.splash_radius:
                damage = self.damage * 0.7
                if hasattr(enemy, "health"):
                    enemy.health -= damage
                else:
                    enemy.hp -= damage
        self.explosion = Explosion(self.x, self.y, radius=self.splash_radius, damage=self.damage, color=(255, 140, 80))

    def update(self, dt):
        if not self.active or self.target is None or self.target.is_dead():
            self.active = False
            return False
        if hasattr(self.target, "reached_goal") and self.target.reached_goal():
            self.active = False
            return False

        self.trail_timer += dt
        if self.trail_timer >= 0.05:
            self.trail_timer = 0.0
            self.trail.append((self.x, self.y))
            if len(self.trail) > 8:
                self.trail.pop(0)

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.hypot(dx, dy)
        if distance <= 10 or distance == 0:
            self._explode()
            self.active = False
            return False

        step = self.speed * dt
        if step >= distance:
            self.x, self.y = self.target.x, self.target.y
            self._explode()
            self.active = False
            return False
        self.x += dx / distance * step
        self.y += dy / distance * step
        return True

    def draw(self, surface):
        for i, (px, py) in enumerate(self.trail):
            radius = max(2, 8 - i)
            alpha = max(20, 120 - i * 12)
            flame = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(flame, (255, 120, 40, alpha), (radius, radius), radius)
            surface.blit(flame, (int(px) - radius, int(py) - radius))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 6)
        pygame.draw.circle(surface, (255, 180, 120), (int(self.x), int(self.y)), 3)


class Mine:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.damage = MINE_DAMAGE
        self.radius = 26
        self.active = True

    def update(self, enemies):
        for enemy in enemies:
            if enemy.is_dead() or enemy.reached_goal():
                continue
            if math.hypot(enemy.x - self.x, enemy.y - self.y) <= self.radius:
                enemy.hp -= self.damage
                self.active = False
                return True
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, (180, 80, 80), (self.x - 10, self.y - 10, 20, 20), border_radius=4)
        pygame.draw.circle(surface, (255, 180, 120), (self.x, self.y), 6)
        pygame.draw.circle(surface, (255, 100, 100), (self.x, self.y), self.radius, 1)


class Walker:
    def __init__(self, x, y, path_points, damage=WALKER_DAMAGE, speed=60):
        self.x = x
        self.y = y
        self.path = path_points
        self.damage = damage
        self.speed = speed
        self.radius = 16
        self.active = True
        self.hit_timer = 0.0
        self.target_index = self._find_closest_segment_index()

    def _find_closest_segment_index(self):
        best_index = 0
        best_dist = float("inf")
        for i in range(len(self.path) - 1):
            x1, y1 = self.path[i]
            x2, y2 = self.path[i + 1]
            proj = self._closest_point_on_segment(self.x, self.y, x1, y1, x2, y2)
            dist = math.hypot(self.x - proj[0], self.y - proj[1])
            if dist < best_dist:
                best_dist = dist
                best_index = i
        return best_index

    def _closest_point_on_segment(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return x1, y1
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        return x1 + t * dx, y1 + t * dy

    def update(self, dt, enemies):
        if not self.active:
            return False

        if self.target_index < 0:
            self.target_index = 0

        target_x, target_y = self.path[self.target_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)
        if distance <= 2:
            if self.target_index > 0:
                self.target_index -= 1
            else:
                self.active = False
                return False
        else:
            step = self.speed * dt
            if step >= distance:
                self.x, self.y = target_x, target_y
                if self.target_index > 0:
                    self.target_index -= 1
                else:
                    self.active = False
                    return False
            else:
                self.x += dx / distance * step
                self.y += dy / distance * step

        self.hit_timer = max(0.0, self.hit_timer - dt)
        for enemy in enemies:
            if enemy.is_dead() or enemy.reached_goal():
                continue
            if math.hypot(enemy.x - self.x, enemy.y - self.y) <= self.radius + 12:
                if self.hit_timer <= 0.0:
                    enemy.hp -= self.damage
                    self.hit_timer = 0.35
        return True

    def draw(self, surface):
        pygame.draw.circle(surface, (200, 140, 80), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (240, 190, 120), (int(self.x), int(self.y)), self.radius - 6)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), 4)


class Game:
    def __init__(self, path_points, sandbox=False, map_name=None):
        self.path_points = path_points
        self.map_name = map_name or self._detect_map_name(path_points)
        self.background_color = MAP_BACKGROUNDS.get(self.map_name, (20, 25, 35))
        self.sandbox = sandbox
        self.developer_mode = False
        self.developer_code = "sick_man"
        self.developer_buffer = ""
        self.enemies_paused = False
        self.enemies = []
        self.towers = []
        self.projectiles = []
        self.explosions = []
        self.mines = []
        self.money = START_MONEY
        self.lives = START_LIVES
        self.wave_index = 0
        self.spawned = 0
        self.wave_timer = 0.0
        self.wave_delay = 2.0
        self.next_spawn = 0.0
        self.wave_ready = False
        self.wave_button_rect = pygame.Rect(WIDTH - 250, 330, 220, 40)
        self.game_over = False
        self.victory = False
        self.selected_tower = "basic"
        self.walkers = []
        self.key_buffer = ""
        self.dragged_enemy = None
        self.drag_offset = (0, 0)
        self.developer_spawn_type = "ground"
        self.developer_spawn_rects = {}
        self.developer_stickman_active = False
        self.developer_stickman_x = WIDTH / 2
        self.developer_stickman_y = HEIGHT / 2
        self.developer_stickman_vx = 130.0
        self.developer_stickman_vy = 95.0
        self.developer_stickman_time = 0.0
        self.developer_stickman_turn_timer = 0.0
        self.magic_hat_particle_timer = 0.0
        self.magic_hat_particles = []
        self.jetpack_flame_timer = 0.0
        self.jetpack_flames = []
        self.achievements = load_achievements()
        self.stickman_costume_menu_unlocked = load_developer_mode_state()
        self.stickman_costume_menu_open = False
        self.stickman_costume_button_rect = pygame.Rect(20, 90, 170, 30)
        self.stickman_costume_window_rect = pygame.Rect(220, 130, 400, 260)
        self.stickman_costume_close_rect = pygame.Rect(548, 142, 52, 24)
        self.stickman_hat_text = load_stickman_hat_text()
        self.stickman_hat = load_stickman_hat()
        self.stickman_legs = load_stickman_legs()
        self.stickman_suit = load_stickman_suit()
        self.stickman_object = load_stickman_object()
        self.unlocked_stickman_hats = load_stickman_hats()
        self.unlocked_stickman_legs = load_stickman_legs_unlocked()
        self.unlocked_stickman_suits = load_stickman_suits()
        self.unlocked_stickman_objects = load_stickman_objects()
        self.unlocked_stickman_costumes, self.equipped_stickman_costume = load_stickman_costumes()
        if self.sandbox:
            self.unlocked_towers = {"basic"}
            self.money = 1_000_000
            self.lives = 1000
            _, self.win_coins = load_progress()
            self.highest_cleared_wave = 0
            self.unlocked_stickman_costumes = set(STICKMAN_COSTUMES)
            self.unlocked_stickman_legs = set(STICKMAN_LEGS)
            self.equipped_stickman_costume = self.equipped_stickman_costume if self.equipped_stickman_costume in self.unlocked_stickman_costumes else "classic"
        else:
            self.unlocked_towers, self.win_coins = load_progress()
            self.wave_six_cleared = load_highest_cleared_wave() >= 6
            self.highest_cleared_wave = load_highest_cleared_wave()
            self.unlocked_towers.discard("gunner")
            if self.wave_six_cleared:
                self.unlocked_towers.add("gunner")
            if self.equipped_stickman_costume not in self.unlocked_stickman_costumes:
                self.equipped_stickman_costume = "classic"
        if self.sandbox:
            self.wave_six_cleared = False
        self.victory_coins_awarded = False
        self._apply_unlocks_from_progress()

    def _detect_map_name(self, path_points):
        for map_name, points in MAPS.items():
            if points == path_points:
                return map_name
        return "Classic"

    def _apply_unlocks_from_progress(self):
        if self.sandbox:
            return
        for tower_type, wave_required in TOWER_UNLOCK_WAVES.items():
            if tower_type != "basic" and self.highest_cleared_wave >= wave_required:
                self.unlocked_towers.add(tower_type)

    def is_tower_unlocked(self, tower_type):
        if self.sandbox:
            return True
        if tower_type == "gunner":
            return self.wave_six_cleared
        if tower_type == "basic":
            return True
        return tower_type in self.unlocked_towers

    def unlock_towers(self):
        if self.game_over:
            return
        self._apply_unlocks_from_progress()

    def complete_wave_unlocks(self):
        if self.game_over or self.sandbox:
            return
        if self.wave_index >= len(WAVES):
            return
        wave = WAVES[self.wave_index]
        if self.spawned < wave["count"]:
            return
        if not all(enemy.is_dead() or enemy.reached_goal() for enemy in self.enemies):
            return
        self.highest_cleared_wave = max(self.highest_cleared_wave, self.wave_index + 1)
        if self.wave_index + 1 >= 1:
            self.unlock_achievement("first_wave")
        if self.wave_index + 1 >= 3:
            self.unlock_achievement("code_rain")
        if self.wave_index + 1 >= 4 and self.lives == START_LIVES:
            self.unlock_achievement("bullet_time")
        if self.wave_index + 1 >= 6:
            self.wave_six_cleared = True
            self.unlock_achievement("wave_six")
        self._apply_unlocks_from_progress()

    def unlock_mine_tower_if_ready(self):
        if self.is_tower_unlocked("mine_tower"):
            return
        for mine in self.mines:
            above = any(tower.x == mine.x and tower.y == mine.y - GRID_SIZE for tower in self.towers)
            below = any(tower.x == mine.x and tower.y == mine.y + GRID_SIZE for tower in self.towers)
            if above and below:
                self.unlocked_towers.add("mine_tower")
                return

    def upgrade_tower(self, mouse_pos):
        for tower in self.towers:
            if math.hypot(tower.x - mouse_pos[0], tower.y - mouse_pos[1]) <= 24:
                if tower.shooter_immunity:
                    return False
                if self.money < 80:
                    return False
                tower.shooter_immunity = True
                self.money -= 80
                return True
        return False

    def upgrade_all_towers(self):
        for tower in self.towers:
            tower.shooter_immunity = True

    def unlock_achievement(self, achievement_id):
        if not award_achievement(self.achievements, achievement_id):
            return False
        save_unlocks(
            self.unlocked_towers,
            self.win_coins,
            load_unlocked_maps(),
            highest_cleared_wave=self.highest_cleared_wave,
            stickman_costumes=self.unlocked_stickman_costumes,
            equipped_stickman_costume=self.equipped_stickman_costume,
            developer_mode_opened=self.stickman_costume_menu_unlocked,
            stickman_hat_text=self.stickman_hat_text,
            stickman_hat=self.stickman_hat,
            stickman_hats=self.unlocked_stickman_hats,
            stickman_legs=self.stickman_legs,
            stickman_legs_unlocked=self.unlocked_stickman_legs,
            stickman_suit=self.stickman_suit,
            stickman_suits=self.unlocked_stickman_suits,
            stickman_object=self.stickman_object,
            stickman_objects=self.unlocked_stickman_objects,
            achievements=self.achievements,
        )
        return True

    def register_key(self, key):
        if self.developer_mode:
            return
        if isinstance(key, int):
            key_name = pygame.key.name(key)
            if key_name in {"underscore", "minus"}:
                key_name = "_"
        else:
            key_name = str(key)
        self.developer_buffer += key_name.lower()
        if len(self.developer_buffer) > len(self.developer_code):
            self.developer_buffer = self.developer_buffer[-len(self.developer_code):]
        if self.developer_buffer.endswith(self.developer_code):
            self.developer_mode = True
            self.developer_stickman_active = True
            self.stickman_costume_menu_unlocked = True
            self.unlock_achievement("developer_mode")
            save_unlocks(
                self.unlocked_towers,
                self.win_coins,
                load_unlocked_maps(),
                highest_cleared_wave=self.highest_cleared_wave,
                stickman_costumes=self.unlocked_stickman_costumes,
                equipped_stickman_costume=self.equipped_stickman_costume,
                developer_mode_opened=True,
                achievements=self.achievements,
            )
            self.developer_buffer = ""

    def toggle_enemy_pause(self):
        if self.developer_mode:
            self.enemies_paused = not self.enemies_paused

    def move_enemies(self, dx, dy):
        if not self.developer_mode:
            return
        for enemy in self.enemies:
            if enemy.is_dead() or enemy.reached_goal():
                continue
            enemy.x = clamp(enemy.x + dx, 0, WIDTH)
            enemy.y = clamp(enemy.y + dy, 0, HEIGHT)

    def set_developer_spawn_type(self, enemy_type):
        if enemy_type in {"ground", "flyer", "shooter"}:
            self.developer_spawn_type = enemy_type

    def developer_spawn_enemy(self):
        if not self.developer_mode:
            return
        enemy_type = self.developer_spawn_type
        if enemy_type == "ground":
            enemy = Enemy(self.path_points, speed=5.0, hp=180, reward=18, enemy_type="ground")
        elif enemy_type == "flyer":
            enemy = Enemy(self.path_points, speed=6.0, hp=160, reward=26, enemy_type="flyer")
        else:
            enemy = Enemy(self.path_points, speed=4.5, hp=220, reward=28, enemy_type="shooter")
        self.enemies.append(enemy)

    def begin_enemy_drag(self, mouse_pos):
        if not self.developer_mode:
            return False
        candidates = [
            enemy
            for enemy in self.enemies
            if not enemy.is_dead() and not enemy.reached_goal()
        ]
        if not candidates:
            return False
        enemy = min(candidates, key=lambda item: math.hypot(item.x - mouse_pos[0], item.y - mouse_pos[1]))
        if math.hypot(enemy.x - mouse_pos[0], enemy.y - mouse_pos[1]) > 18:
            return False
        self.dragged_enemy = enemy
        self.drag_offset = (enemy.x - mouse_pos[0], enemy.y - mouse_pos[1])
        return True

    def drag_enemy(self, mouse_pos):
        if not self.developer_mode or self.dragged_enemy is None:
            return
        self.dragged_enemy.x = clamp(mouse_pos[0] + self.drag_offset[0], 0, WIDTH)
        self.dragged_enemy.y = clamp(mouse_pos[1] + self.drag_offset[1], 0, HEIGHT)

    def end_enemy_drag(self):
        self.dragged_enemy = None
        self.drag_offset = (0, 0)

    def update_developer_stickman(self, dt):
        if not self.developer_stickman_active:
            return
        self.developer_stickman_time += dt
        self.developer_stickman_turn_timer -= dt
        if self.developer_stickman_turn_timer <= 0:
            direction = random.uniform(0, math.tau)
            speed = random.uniform(90, 170)
            self.developer_stickman_vx = math.cos(direction) * speed
            self.developer_stickman_vy = math.sin(direction) * speed
            self.developer_stickman_turn_timer = random.uniform(0.35, 1.1)
        self.developer_stickman_x += self.developer_stickman_vx * dt
        self.developer_stickman_y += self.developer_stickman_vy * dt
        if self.developer_stickman_x < 24 or self.developer_stickman_x > WIDTH - 24:
            self.developer_stickman_vx *= -1
            self.developer_stickman_x = clamp(self.developer_stickman_x, 24, WIDTH - 24)
        if self.developer_stickman_y < 30 or self.developer_stickman_y > HEIGHT - 24:
            self.developer_stickman_vy *= -1
            self.developer_stickman_y = clamp(self.developer_stickman_y, 30, HEIGHT - 24)
        if self.stickman_object == "magic_hat":
            self.magic_hat_particle_timer -= dt
            while self.magic_hat_particle_timer <= 0:
                facing = 1 if self.developer_stickman_vx >= 0 else -1
                hat_x = self.developer_stickman_x + facing * 28
                hat_y = self.developer_stickman_y - 42
                particle_shape = random.choices(
                    ("star", "coin", "cube", "orb", "house", "hut", "office_building", "dancing_cat"),
                    weights=(24, 24, 20, 20, 6, 6, 4, 4),
                )[0]
                self.magic_hat_particles.append({
                    "x": hat_x + random.uniform(-5, 5),
                    "y": hat_y + random.uniform(-24, -16),
                    "vx": random.uniform(-100, 100),
                    "vy": random.uniform(-150, -45),
                    "life": random.uniform(0.8, 1.4),
                    "color": random.choice([(255, 225, 90), (100, 220, 255), (255, 120, 190), (170, 255, 130)]),
                    "shape": particle_shape,
                    "size": random.randint(8, 10) if particle_shape in ("house", "hut", "office_building") else random.randint(9, 11) if particle_shape == "dancing_cat" else random.randint(3, 6),
                    "dance_phase": random.uniform(0, math.tau) if particle_shape == "dancing_cat" else 0,
                })
                self.magic_hat_particle_timer += 0.14
        else:
            self.magic_hat_particle_timer = 0.0
        if self.stickman_suit == "jetpack":
            self.jetpack_flame_timer -= dt
            while self.jetpack_flame_timer <= 0:
                speed = max(1, math.hypot(self.developer_stickman_vx, self.developer_stickman_vy))
                direction_x = self.developer_stickman_vx / speed
                direction_y = self.developer_stickman_vy / speed
                for nozzle_offset in (-6, 6):
                    flame_speed = random.uniform(55, 100)
                    self.jetpack_flames.append({
                        "x": self.developer_stickman_x + nozzle_offset,
                        "y": self.developer_stickman_y + 18,
                        "vx": -direction_x * flame_speed * 0.35 + random.uniform(-18, 18),
                        "vy": 75 - direction_y * flame_speed * 0.2 + random.uniform(-12, 12),
                        "life": random.uniform(0.2, 0.38),
                        "size": random.randint(3, 6),
                        "color": random.choice([(255, 90, 30), (255, 145, 35), (255, 205, 65)]),
                    })
                self.jetpack_flame_timer += 0.045
        else:
            self.jetpack_flame_timer = 0.0
        for particle in self.magic_hat_particles:
            particle["life"] -= dt
            particle["x"] += particle["vx"] * dt
            particle["y"] += particle["vy"] * dt
            particle["vy"] += 180 * dt
            if particle["shape"] == "dancing_cat":
                particle["dance_phase"] = (particle["dance_phase"] + dt * 14) % math.tau
        self.magic_hat_particles = [particle for particle in self.magic_hat_particles if particle["life"] > 0]
        for flame in self.jetpack_flames:
            flame["life"] -= dt
            flame["x"] += flame["vx"] * dt
            flame["y"] += flame["vy"] * dt
            flame["vy"] += 100 * dt
        self.jetpack_flames = [flame for flame in self.jetpack_flames if flame["life"] > 0]

    def tag_touched_enemies(self):
        if not self.developer_stickman_active:
            return
        for enemy in self.enemies:
            if enemy.is_dead() or enemy.reached_goal():
                continue
            if math.hypot(enemy.x - self.developer_stickman_x, enemy.y - self.developer_stickman_y) <= 25:
                enemy.loser_hat = True

    def buy_hat_text(self, new_text):
        cleaned = str(new_text or "").strip()[:16]
        if not cleaned:
            return False
        if self.sandbox:
            self.stickman_hat_text = cleaned
            return True
        if self.win_coins < 5:
            return False
        self.win_coins -= 5
        self.stickman_hat_text = cleaned
        save_unlocks(
            self.unlocked_towers,
            self.win_coins,
            load_unlocked_maps(),
            highest_cleared_wave=self.highest_cleared_wave,
            stickman_costumes=self.unlocked_stickman_costumes,
            equipped_stickman_costume=self.equipped_stickman_costume,
            developer_mode_opened=self.stickman_costume_menu_unlocked,
            stickman_hat_text=self.stickman_hat_text,
        )
        return True

    def buy_stickman_hat(self, hat_id):
        if hat_id not in STICKMAN_HATS:
            return False
        hat_info = STICKMAN_HATS[hat_id]
        if hat_id not in self.unlocked_stickman_hats and not self.sandbox:
            if self.win_coins < hat_info["price"]:
                return False
            self.win_coins -= hat_info["price"]
        self.unlocked_stickman_hats.add(hat_id)
        self.stickman_hat = hat_id
        if not self.sandbox:
            save_unlocks(
                self.unlocked_towers,
                self.win_coins,
                load_unlocked_maps(),
                highest_cleared_wave=self.highest_cleared_wave,
                stickman_costumes=self.unlocked_stickman_costumes,
                equipped_stickman_costume=self.equipped_stickman_costume,
                developer_mode_opened=self.stickman_costume_menu_unlocked,
                stickman_hat_text=self.stickman_hat_text,
                stickman_hat=self.stickman_hat,
                stickman_hats=self.unlocked_stickman_hats,
                stickman_legs=self.stickman_legs,
            )
        return True

    def buy_stickman_legs(self, leg_id):
        if leg_id not in STICKMAN_LEGS:
            return False
        if leg_id not in self.unlocked_stickman_legs and not self.sandbox:
            if self.win_coins < STICKMAN_LEGS[leg_id]["price"]:
                return False
            self.win_coins -= STICKMAN_LEGS[leg_id]["price"]
        self.unlocked_stickman_legs.add(leg_id)
        self.stickman_legs = leg_id
        if not self.sandbox:
            save_unlocks(
                self.unlocked_towers,
                self.win_coins,
                load_unlocked_maps(),
                highest_cleared_wave=self.highest_cleared_wave,
                stickman_costumes=self.unlocked_stickman_costumes,
                equipped_stickman_costume=self.equipped_stickman_costume,
                developer_mode_opened=self.stickman_costume_menu_unlocked,
                stickman_hat_text=self.stickman_hat_text,
                stickman_hat=self.stickman_hat,
                stickman_hats=self.unlocked_stickman_hats,
                stickman_legs=self.stickman_legs,
                stickman_legs_unlocked=self.unlocked_stickman_legs,
            )
        return True

    def buy_stickman_suit(self, suit_id):
        if suit_id not in STICKMAN_SUITS:
            return False
        if suit_id not in self.unlocked_stickman_suits and not self.sandbox:
            if self.win_coins < STICKMAN_SUITS[suit_id]["price"]:
                return False
            self.win_coins -= STICKMAN_SUITS[suit_id]["price"]
        self.unlocked_stickman_suits.add(suit_id)
        self.stickman_suit = suit_id
        if not self.sandbox:
            save_unlocks(
                self.unlocked_towers,
                self.win_coins,
                load_unlocked_maps(),
                highest_cleared_wave=self.highest_cleared_wave,
                stickman_costumes=self.unlocked_stickman_costumes,
                equipped_stickman_costume=self.equipped_stickman_costume,
                developer_mode_opened=self.stickman_costume_menu_unlocked,
                stickman_hat_text=self.stickman_hat_text,
                stickman_hat=self.stickman_hat,
                stickman_hats=self.unlocked_stickman_hats,
                stickman_legs=self.stickman_legs,
                stickman_legs_unlocked=self.unlocked_stickman_legs,
                stickman_suit=self.stickman_suit,
                stickman_suits=self.unlocked_stickman_suits,
            )
        return True

    def buy_stickman_object(self, object_id):
        if object_id not in STICKMAN_OBJECTS:
            return False
        if object_id not in self.unlocked_stickman_objects and not self.sandbox:
            if self.win_coins < STICKMAN_OBJECTS[object_id]["price"]:
                return False
            self.win_coins -= STICKMAN_OBJECTS[object_id]["price"]
        self.unlocked_stickman_objects.add(object_id)
        self.stickman_object = object_id
        if not self.sandbox:
            save_unlocks(
                self.unlocked_towers,
                self.win_coins,
                load_unlocked_maps(),
                highest_cleared_wave=self.highest_cleared_wave,
                stickman_costumes=self.unlocked_stickman_costumes,
                equipped_stickman_costume=self.equipped_stickman_costume,
                developer_mode_opened=self.stickman_costume_menu_unlocked,
                stickman_hat_text=self.stickman_hat_text,
                stickman_hat=self.stickman_hat,
                stickman_hats=self.unlocked_stickman_hats,
                stickman_legs=self.stickman_legs,
                stickman_legs_unlocked=self.unlocked_stickman_legs,
                stickman_suit=self.stickman_suit,
                stickman_suits=self.unlocked_stickman_suits,
                stickman_object=self.stickman_object,
                stickman_objects=self.unlocked_stickman_objects,
            )
        return True

    def draw_developer_stickman(self, surface):
        if not self.developer_stickman_active:
            return
        x = int(self.developer_stickman_x)
        y = int(self.developer_stickman_y)
        step = math.sin(self.developer_stickman_time * 10) * 7
        facing = 1 if self.developer_stickman_vx >= 0 else -1
        for flame in self.jetpack_flames:
            flame_x = round(flame["x"])
            flame_y = round(flame["y"])
            velocity_length = max(1, math.hypot(flame["vx"], flame["vy"]))
            direction_x = flame["vx"] / velocity_length
            direction_y = flame["vy"] / velocity_length
            perpendicular_x = -direction_y
            perpendicular_y = direction_x
            size = max(1, round(flame["size"] * min(1, flame["life"] / 0.2)))
            tip = (round(flame_x + direction_x * size * 2), round(flame_y + direction_y * size * 2))
            base_left = (round(flame_x - perpendicular_x * size), round(flame_y - perpendicular_y * size))
            base_right = (round(flame_x + perpendicular_x * size), round(flame_y + perpendicular_y * size))
            pygame.draw.polygon(surface, flame["color"], [tip, base_left, base_right])
            inner_tip = (round(flame_x + direction_x * size), round(flame_y + direction_y * size))
            pygame.draw.polygon(surface, (255, 235, 120), [inner_tip, (flame_x, flame_y), base_right])
        costume = STICKMAN_COSTUMES.get(self.equipped_stickman_costume, STICKMAN_COSTUMES["classic"])
        ink = (250, 250, 250)
        accent = costume["accent"]
        body = costume["body"]
        shirt = costume["shirt"]
        hat_color = costume["hat"]
        pygame.draw.circle(surface, accent, (x, y - 22), 9)
        pygame.draw.circle(surface, ink, (x, y - 22), 9, 2)
        if self.stickman_hat == "loser":
            pygame.draw.polygon(surface, (125, 125, 135), [(x - 11, y - 32), (x + 11, y - 32), (x, y - 52)])
            pygame.draw.ellipse(surface, (80, 80, 90), (x - 14, y - 36, 28, 7))
            rendered_hat_text = pygame.font.SysFont("arial", 8, bold=True).render("L", True, (230, 230, 240))
            surface.blit(rendered_hat_text, (x - rendered_hat_text.get_width() // 2, y - 43))
        elif self.stickman_hat == "war":
            pygame.draw.ellipse(surface, (85, 95, 110), (x - 16, y - 39, 32, 17))
            pygame.draw.rect(surface, (125, 135, 150), (x - 18, y - 34, 36, 6), border_radius=3)
            pygame.draw.polygon(surface, (210, 70, 70), [(x - 3, y - 39), (x, y - 49), (x + 3, y - 39)])
        elif self.stickman_hat == "wizard":
            pygame.draw.polygon(surface, (75, 45, 125), [(x - 11, y - 33), (x + 11, y - 33), (x + 2, y - 57), (x - 3, y - 57)])
            pygame.draw.ellipse(surface, (45, 25, 80), (x - 14, y - 37, 28, 7))
            pygame.draw.circle(surface, (245, 220, 90), (x - 4, y - 42), 2)
        elif self.stickman_hat == "headphones":
            pygame.draw.arc(surface, (70, 190, 220), (x - 14, y - 39, 28, 25), 0, math.pi, 3)
            pygame.draw.rect(surface, (70, 190, 220), (x - 16, y - 29, 5, 11), border_radius=2)
            pygame.draw.rect(surface, (70, 190, 220), (x + 11, y - 29, 5, 11), border_radius=2)
        elif self.stickman_hat == "graduation":
            pygame.draw.polygon(surface, (35, 35, 45), [(x - 15, y - 37), (x, y - 44), (x + 15, y - 37), (x, y - 30)])
            pygame.draw.rect(surface, (55, 55, 65), (x - 9, y - 34, 18, 6))
            pygame.draw.line(surface, (245, 210, 80), (x + 10, y - 37), (x + 13, y - 25), 1)
            pygame.draw.circle(surface, (245, 210, 80), (x + 13, y - 24), 2)
        elif self.stickman_hat == "bicycle":
            pygame.draw.ellipse(surface, (235, 70, 55), (x - 14, y - 40, 28, 16))
            pygame.draw.rect(surface, (245, 220, 90), (x - 15, y - 34, 30, 5), border_radius=2)
            pygame.draw.line(surface, (170, 40, 35), (x - 6, y - 40), (x - 9, y - 34), 2)
            pygame.draw.line(surface, (170, 40, 35), (x + 2, y - 40), (x + 5, y - 34), 2)
        elif self.stickman_hat == "cardboard":
            pygame.draw.rect(surface, (170, 115, 55), (x - 14, y - 44, 28, 16), border_radius=1)
            pygame.draw.line(surface, (115, 75, 35), (x, y - 44), (x, y - 28), 1)
            pygame.draw.line(surface, (115, 75, 35), (x - 14, y - 36), (x + 14, y - 36), 1)
        elif self.stickman_hat == "powder":
            pygame.draw.circle(surface, (245, 245, 240), (x - 9, y - 36), 8)
            pygame.draw.circle(surface, (245, 245, 240), (x, y - 40), 9)
            pygame.draw.circle(surface, (245, 245, 240), (x + 9, y - 36), 8)
            pygame.draw.ellipse(surface, (225, 225, 220), (x - 15, y - 37, 30, 7))
        else:
            pygame.draw.ellipse(surface, (25, 25, 35), (x - 18, y - 35, 36, 7))
            pygame.draw.rect(surface, body, (x - 15, y - 48, 30, 15), border_radius=3)
            pygame.draw.rect(surface, shirt, (x - 15, y - 37, 30, 5))
            rendered_hat_text = pygame.font.SysFont("arial", 7, bold=True).render(self.stickman_hat_text, True, hat_color)
            surface.blit(rendered_hat_text, (x - rendered_hat_text.get_width() // 2, y - 38))
        pygame.draw.line(surface, ink, (x, y - 13), (x, y + 12), 3)
        pygame.draw.line(surface, ink, (x, y - 5), (x - facing * 13, y + 5), 3)
        pygame.draw.line(surface, ink, (x, y - 5), (x + facing * 13, y - 12), 3)
        pygame.draw.line(surface, ink, (x, y + 12), (x - facing * (10 + step), y + 29), 3)
        pygame.draw.line(surface, ink, (x, y + 12), (x + facing * (10 + step), y + 29), 3)
        if self.stickman_legs == "hermes":
            pygame.draw.ellipse(surface, (120, 95, 70), (x - 13, y + 24, 10, 5))
            pygame.draw.ellipse(surface, (120, 95, 70), (x + 4, y + 24, 10, 5))
            pygame.draw.line(surface, (120, 95, 70), (x - 10, y + 24), (x - 8, y + 12), 2)
            pygame.draw.line(surface, (120, 95, 70), (x + 10, y + 24), (x + 8, y + 12), 2)
            pygame.draw.polygon(surface, (210, 215, 255), [(x - 12, y + 16), (x - 4, y + 12), (x - 7, y + 22)])
            pygame.draw.polygon(surface, (210, 215, 255), [(x + 9, y + 16), (x + 2, y + 12), (x + 5, y + 22)])
        elif self.stickman_legs == "boots":
            pygame.draw.rect(surface, (85, 55, 45), (x - 12, y + 22, 9, 9), border_radius=2)
            pygame.draw.rect(surface, (85, 55, 45), (x + 4, y + 22, 9, 9), border_radius=2)
        if self.stickman_suit == "jetpack":
            pygame.draw.rect(surface, (110, 120, 140), (x - 11, y - 20, 22, 27), border_radius=5)
            pygame.draw.rect(surface, (255, 180, 80), (x - 5, y + 8, 4, 10), border_radius=2)
            pygame.draw.rect(surface, (255, 180, 80), (x + 1, y + 8, 4, 10), border_radius=2)
        elif self.stickman_suit == "cactus":
            pygame.draw.rect(surface, (80, 180, 90), (x - 10, y - 12, 20, 25), border_radius=5)
            for spine_x in (-6, -2, 2, 6):
                pygame.draw.line(surface, (120, 220, 110), (x + spine_x, y - 8), (x + spine_x, y + 12), 1)
        elif self.stickman_suit == "fish":
            pygame.draw.rect(surface, (80, 160, 220), (x - 9, y - 18, 18, 28), border_radius=6)
            pygame.draw.polygon(surface, (140, 220, 255), [(x + 8, y - 5), (x + 16, y - 2), (x + 8, y + 4)])
            pygame.draw.line(surface, (210, 235, 255), (x - 4, y - 5), (x + 4, y - 5), 1)
            pygame.draw.line(surface, (210, 235, 255), (x - 4, y + 5), (x + 4, y + 5), 1)
        if self.stickman_object == "magic_hat":
            hand_x = x + facing * 16
            hand_y = y - 4
            hat_x = hand_x + facing * 12
            hat_y = hand_y - 18
            pygame.draw.line(surface, (245, 235, 255), (x + facing * 8, y - 4), (hat_x, hat_y), 2)
            pygame.draw.circle(surface, (220, 140, 255), (hat_x, hat_y - 8), 10)
            pygame.draw.polygon(surface, (255, 180, 255), [(hat_x - 10, hat_y - 6), (hat_x + 10, hat_y - 6), (hat_x + 4, hat_y - 22), (hat_x - 4, hat_y - 22)])
            for spark in [(hat_x - 8, hat_y - 18), (hat_x + 4, hat_y - 20), (hat_x + 10, hat_y - 14)]:
                pygame.draw.circle(surface, (255, 255, 255), spark, 2)
        elif self.stickman_object == "sword":
            draw_sword(surface, x + facing * 13, y - 12, facing, scale=0.65)
        pygame.draw.circle(surface, accent, (x - 3, y - 24), 1)
        pygame.draw.circle(surface, accent, (x + 3, y - 24), 1)
        for particle in self.magic_hat_particles:
            particle_x = round(particle["x"])
            particle_y = round(particle["y"])
            size = particle["size"]
            shape = particle["shape"]
            color = particle["color"]
            if shape == "star":
                points = [
                    (particle_x, particle_y - size),
                    (particle_x + size // 2, particle_y - size // 2),
                    (particle_x + size, particle_y),
                    (particle_x + size // 2, particle_y + size // 2),
                    (particle_x, particle_y + size),
                    (particle_x - size // 2, particle_y + size // 2),
                    (particle_x - size, particle_y),
                    (particle_x - size // 2, particle_y - size // 2),
                ]
                pygame.draw.polygon(surface, color, points)
            elif shape == "coin":
                pygame.draw.ellipse(surface, color, (particle_x - size, particle_y - size, size * 2, size * 2))
                pygame.draw.line(surface, (255, 255, 220), (particle_x, particle_y - size // 2), (particle_x, particle_y + size // 2), 1)
            elif shape == "cube":
                pygame.draw.rect(surface, color, (particle_x - size, particle_y - size, size * 2, size * 2))
            elif shape == "house":
                pygame.draw.rect(surface, color, (particle_x - size, particle_y - size // 3, size * 2, size))
                pygame.draw.polygon(surface, (190, 75, 65), [
                    (particle_x - size - 2, particle_y - size // 3),
                    (particle_x, particle_y - size - 2),
                    (particle_x + size + 2, particle_y - size // 3),
                ])
                pygame.draw.rect(surface, (95, 65, 55), (particle_x - 2, particle_y + size // 4, 4, size // 2))
            elif shape == "hut":
                pygame.draw.rect(surface, (190, 145, 85), (particle_x - size, particle_y - size // 4, size * 2, size))
                pygame.draw.polygon(surface, (125, 85, 45), [
                    (particle_x - size - 3, particle_y - size // 4),
                    (particle_x, particle_y - size),
                    (particle_x + size + 3, particle_y - size // 4),
                ])
                pygame.draw.rect(surface, (90, 65, 45), (particle_x - 2, particle_y + size // 4, 4, size // 2))
            elif shape == "office_building":
                building_rect = pygame.Rect(particle_x - size, particle_y - size * 2, size * 2, size * 3)
                pygame.draw.rect(surface, (105, 130, 155), building_rect, border_radius=2)
                pygame.draw.rect(surface, (55, 70, 90), building_rect, 1, border_radius=2)
                for window_row in range(3):
                    for window_column in (-1, 0):
                        window_rect = pygame.Rect(
                            particle_x + window_column * size // 2 - 1,
                            particle_y - size * 2 + 3 + window_row * (size - 1),
                            max(2, size // 3),
                            max(2, size // 3),
                        )
                        pygame.draw.rect(surface, (255, 225, 125), window_rect)
                pygame.draw.line(surface, (75, 95, 120), (particle_x, particle_y - size * 2), (particle_x, particle_y - size * 2 - 3), 2)
            elif shape == "dancing_cat":
                phase = particle["dance_phase"]
                bob = round(math.sin(phase) * 2)
                head_y = particle_y - size + bob
                radius = max(3, size // 2)
                leg_swing = round(math.sin(phase) * size / 2)
                pygame.draw.lines(surface, color, False, [
                    (particle_x + size // 2, particle_y + bob),
                    (particle_x + size, particle_y - size // 2 + bob),
                    (particle_x + size + leg_swing, particle_y - size + bob),
                ], max(1, size // 5))
                pygame.draw.ellipse(surface, color, (particle_x - size // 2, particle_y - size // 2 + bob, size, size))
                pygame.draw.line(surface, color, (particle_x - size // 3, particle_y + bob), (particle_x - size, particle_y - size // 2 + bob - leg_swing), max(1, size // 4))
                pygame.draw.line(surface, color, (particle_x + size // 3, particle_y + bob), (particle_x + size, particle_y - size // 2 + bob + leg_swing), max(1, size // 4))
                pygame.draw.line(surface, color, (particle_x - 2, particle_y + size // 3 + bob), (particle_x - size // 2 - leg_swing, particle_y + size + bob), max(1, size // 4))
                pygame.draw.line(surface, color, (particle_x + 2, particle_y + size // 3 + bob), (particle_x + size // 2 + leg_swing, particle_y + size + bob), max(1, size // 4))
                pygame.draw.circle(surface, color, (particle_x, head_y), radius)
                pygame.draw.polygon(surface, color, [
                    (particle_x - radius, head_y - radius // 2),
                    (particle_x - radius, head_y - radius * 2),
                    (particle_x - radius // 3, head_y - radius),
                ])
                pygame.draw.polygon(surface, color, [
                    (particle_x + radius, head_y - radius // 2),
                    (particle_x + radius, head_y - radius * 2),
                    (particle_x + radius // 3, head_y - radius),
                ])
                pygame.draw.circle(surface, (35, 35, 45), (particle_x - 2, head_y), 1)
                pygame.draw.circle(surface, (35, 35, 45), (particle_x + 2, head_y), 1)
                pygame.draw.circle(surface, (245, 130, 155), (particle_x, head_y + 2), 1)
            else:
                pygame.draw.circle(surface, color, (particle_x, particle_y), size)

    def can_buy_win_tower(self, tower_type):
        tower_info = TOWER_TYPES.get(tower_type, {})
        win_cost = tower_info.get("win_cost", 0)
        if win_cost <= 0:
            return False
        return self.win_coins >= win_cost

    def buy_stickman_costume(self, costume_id):
        if costume_id not in STICKMAN_COSTUMES:
            return False
        costume_info = STICKMAN_COSTUMES[costume_id]
        if costume_id in self.unlocked_stickman_costumes:
            self.equipped_stickman_costume = costume_id
            if not self.sandbox:
                save_unlocks(
                    self.unlocked_towers,
                    self.win_coins,
                    load_unlocked_maps(),
                    highest_cleared_wave=self.highest_cleared_wave,
                    stickman_costumes=self.unlocked_stickman_costumes,
                    equipped_stickman_costume=self.equipped_stickman_costume,
                )
            return True
        if self.sandbox:
            self.unlocked_stickman_costumes.add(costume_id)
            self.equipped_stickman_costume = costume_id
            return True
        if self.win_coins < costume_info["price"]:
            return False
        self.win_coins -= costume_info["price"]
        self.unlocked_stickman_costumes.add(costume_id)
        self.equipped_stickman_costume = costume_id
        save_unlocks(
            self.unlocked_towers,
            self.win_coins,
            load_unlocked_maps(),
            highest_cleared_wave=self.highest_cleared_wave,
            stickman_costumes=self.unlocked_stickman_costumes,
            equipped_stickman_costume=self.equipped_stickman_costume,
        )
        return True

    def start_next_wave(self):
        if self.game_over or self.wave_index + 1 >= len(WAVES):
            return
        self.wave_index += 1
        self.spawned = 0
        self.next_spawn = 0.0
        self.wave_ready = False

    def spawn_enemy(self):
        wave = WAVES[self.wave_index]
        enemy_type = "ground"
        if self.wave_index >= 1 and (self.spawned + 1) % 6 == 0:
            enemy_type = "flyer"
        elif self.wave_index >= 2 and (self.spawned + 1) % 5 == 0:
            enemy_type = "shooter"
        speed = wave["speed"] * (1.2 if enemy_type == "flyer" else 1.0)
        hp = int(wave["hp"] * (0.9 if enemy_type == "flyer" else 1.0))
        reward = wave["reward"] + (8 if enemy_type == "flyer" else 0) + (10 if enemy_type == "shooter" else 0)
        enemy = Enemy(self.path_points, speed=speed, hp=hp, reward=reward, enemy_type=enemy_type)
        self.enemies.append(enemy)
        self.spawned += 1

    def separate_enemies(self):
        alive_enemies = [enemy for enemy in self.enemies if not enemy.is_dead() and not enemy.reached_goal()]
        for index, enemy_a in enumerate(alive_enemies):
            for enemy_b in alive_enemies[index + 1 :]:
                dx = enemy_a.x - enemy_b.x
                dy = enemy_a.y - enemy_b.y
                distance = math.hypot(dx, dy)
                if distance == 0:
                    dx, dy = 1.0, 0.0
                    distance = 1.0
                min_distance = 20.0
                if distance < min_distance:
                    push_amount = (min_distance - distance) / min_distance * 14.0
                    push_x = (dx / distance) * push_amount
                    push_y = (dy / distance) * push_amount
                    enemy_a.x += push_x
                    enemy_a.y += push_y
                    enemy_b.x -= push_x
                    enemy_b.y -= push_y
                    enemy_a.x = clamp(enemy_a.x, 0, WIDTH)
                    enemy_a.y = clamp(enemy_a.y, 0, HEIGHT)
                    enemy_b.x = clamp(enemy_b.x, 0, WIDTH)
                    enemy_b.y = clamp(enemy_b.y, 0, HEIGHT)

    def update(self, dt):
        if self.game_over:
            return

        self.update_developer_stickman(dt)
        self.unlock_towers()

        if self.wave_index < len(WAVES) and not self.enemies_paused:
            wave = WAVES[self.wave_index]
            if not self.wave_ready:
                self.wave_timer += dt
                self.next_spawn -= dt
                if self.spawned < wave["count"] and self.next_spawn <= 0:
                    self.spawn_enemy()
                    self.next_spawn = 0.8
                if self.spawned >= wave["count"] and all(e.is_dead() or e.reached_goal() for e in self.enemies):
                    self.complete_wave_unlocks()
                    if self.wave_index + 1 < len(WAVES):
                        self.wave_ready = True
                    else:
                        self.wave_index += 1
                        self.next_spawn = 0.0

        if not self.enemies_paused:
            self.separate_enemies()

        if not self.enemies_paused:
            for enemy in list(self.enemies):
                enemy.update(dt, self.towers)
                if enemy.dodged_tower:
                    enemy.dodged_tower = False
                    if not self.sandbox:
                        self.unlock_achievement("matrix_dodge")
                if enemy.reached_goal() and not enemy.is_dead():
                    self.lives -= 1
                    self.enemies.remove(enemy)
                elif enemy.is_dead():
                    self.money += enemy.reward
                    self.enemies.remove(enemy)

            for enemy in self.enemies:
                if enemy.type == "shooter":
                    for projectile in list(enemy.projectiles):
                        if not projectile.update(dt):
                            enemy.projectiles.remove(projectile)

            self.tag_touched_enemies()

        for tower in list(self.towers):
            if tower.health <= 0:
                self.towers.remove(tower)

        for tower in self.towers:
            shot = tower.update(dt, self.enemies)
            if shot == "spawn_walker":
                self.walkers.append(Walker(tower.x, tower.y, self.path_points))
            elif shot:
                self.projectiles.append(shot)
        for mine in list(self.mines):
            if mine.update(self.enemies):
                self.mines.remove(mine)

        for walker in list(self.walkers):
            if not walker.update(dt, self.enemies):
                self.walkers.remove(walker)

        for projectile in list(self.projectiles):
            if not projectile.update(dt):
                if getattr(projectile, "explosion", None) is not None:
                    self.explosions.append(projectile.explosion)
                self.projectiles.remove(projectile)

        for explosion in list(self.explosions):
            if not explosion.update(dt):
                self.explosions.remove(explosion)

        if self.lives <= 0:
            if self.sandbox:
                self.lives = max(self.lives, 1)
            else:
                self.game_over = True
        elif self.wave_index >= len(WAVES) and not self.enemies:
            if not self.victory_coins_awarded:
                self.win_coins += 5
                self.victory_coins_awarded = True
            self.victory = True
            self.game_over = True

        if not self.sandbox:
            save_unlocks(self.unlocked_towers, self.win_coins, highest_cleared_wave=self.highest_cleared_wave)
        if self.game_over:
            check_achievements(self)

    def place_tower(self, mouse_pos):
        grid_x = clamp(round(mouse_pos[0] / GRID_SIZE) * GRID_SIZE, GRID_SIZE // 2, WIDTH - GRID_SIZE // 2)
        grid_y = clamp(round(mouse_pos[1] / GRID_SIZE) * GRID_SIZE, GRID_SIZE // 2, HEIGHT - GRID_SIZE // 2)
        if self.selected_tower == "mine":
            if not self.is_tower_unlocked("mine"):
                return
            if self.money < MINE_COST:
                return
            if not self.can_place_mine(grid_x, grid_y):
                return
            self.mines.append(Mine(grid_x, grid_y))
            self.record_tower_placement()
            self.money -= MINE_COST
            return
        if self.selected_tower == "walker":
            if not self.is_tower_unlocked("walker"):
                return
            if self.money < WALKER_COST:
                return
            if not self.can_place_mine(grid_x, grid_y):
                return
            self.walkers.append(Walker(grid_x, grid_y, self.path_points))
            self.record_tower_placement()
            self.money -= WALKER_COST
            return
        if self.selected_tower == "gunner":
            if not self.is_tower_unlocked("gunner"):
                return
            gunner_cost = TOWER_TYPES["gunner"]["cost"]
            if self.money < gunner_cost:
                return
            if not self.can_place_mine(grid_x, grid_y):
                return
            self.towers.append(Tower(grid_x, grid_y, "gunner", self.path_points))
            self.record_tower_placement()
            self.money -= gunner_cost
            return
        if self.selected_tower in TOWER_TYPES and TOWER_TYPES[self.selected_tower].get("win_cost"):
            if not self.can_buy_win_tower(self.selected_tower):
                return
            if grid_x > WIDTH - 140:
                return
            if not self.can_place(grid_x, grid_y):
                return
            self.towers.append(Tower(grid_x, grid_y, self.selected_tower))
            self.record_tower_placement()
            self.win_coins -= TOWER_TYPES[self.selected_tower]["win_cost"]
            if self.selected_tower == "basic":
                self.unlock_mine_tower_if_ready()
            if not self.sandbox:
                save_unlocks(self.unlocked_towers, self.win_coins, highest_cleared_wave=self.highest_cleared_wave)
            return
        if not self.is_tower_unlocked(self.selected_tower):
            return
        if grid_x > WIDTH - 140:
            return
        if not self.can_place(grid_x, grid_y):
            return
        tower_info = TOWER_TYPES[self.selected_tower]
        if self.money < tower_info["cost"]:
            return
        self.towers.append(Tower(grid_x, grid_y, self.selected_tower))
        self.record_tower_placement()
        self.money -= tower_info["cost"]
        if self.selected_tower == "basic":
            self.unlock_mine_tower_if_ready()

    def record_tower_placement(self):
        if not self.sandbox:
            self.unlock_achievement("the_beginning")

    def can_place(self, x, y):
        for px, py in self.path_points:
            if abs(px - x) < GRID_SIZE and abs(py - y) < GRID_SIZE:
                return False
        for tower in self.towers:
            if abs(tower.x - x) < GRID_SIZE and abs(tower.y - y) < GRID_SIZE:
                return False
        return True

    def can_place_mine(self, x, y):
        if x > WIDTH - 140:
            return False
        path_half = PATH_WIDTH / 2 + 8
        on_path = False
        for i in range(len(self.path_points) - 1):
            x1, y1 = self.path_points[i]
            x2, y2 = self.path_points[i + 1]
            if self._distance_to_segment(x, y, x1, y1, x2, y2) <= path_half:
                on_path = True
                break
        if not on_path:
            return False
        for tower in self.towers:
            if abs(tower.x - x) < GRID_SIZE and abs(tower.y - y) < GRID_SIZE:
                return False
        for mine in self.mines:
            if abs(mine.x - x) < GRID_SIZE and abs(mine.y - y) < GRID_SIZE:
                return False
        for walker in self.walkers:
            if abs(walker.x - x) < GRID_SIZE and abs(walker.y - y) < GRID_SIZE:
                return False
        return True

    def _distance_to_segment(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.hypot(px - proj_x, py - proj_y)

    def draw_path(self, surface):
        for i in range(len(self.path_points) - 1):
            start_x, start_y = self.path_points[i]
            end_x, end_y = self.path_points[i + 1]
            pygame.draw.line(surface, (180, 140, 80), (start_x, start_y), (end_x, end_y), PATH_WIDTH)

            dx = end_x - start_x
            dy = end_y - start_y
            segment_length = math.hypot(dx, dy)
            if segment_length == 0:
                continue
            direction_x = dx / segment_length
            direction_y = dy / segment_length
            perpendicular_x = -direction_y
            perpendicular_y = direction_x
            for distance in range(48, int(segment_length), 72):
                center_x = start_x + direction_x * distance
                center_y = start_y + direction_y * distance
                tip = (center_x + direction_x * 12, center_y + direction_y * 12)
                left = (
                    center_x - direction_x * 8 + perpendicular_x * 8,
                    center_y - direction_y * 8 + perpendicular_y * 8,
                )
                right = (
                    center_x - direction_x * 8 - perpendicular_x * 8,
                    center_y - direction_y * 8 - perpendicular_y * 8,
                )
                pygame.draw.polygon(surface, (90, 65, 40), [tip, left, right])
                inner_tip = (center_x + direction_x * 9, center_y + direction_y * 9)
                inner_left = (
                    center_x - direction_x * 6 + perpendicular_x * 5,
                    center_y - direction_y * 6 + perpendicular_y * 5,
                )
                inner_right = (
                    center_x - direction_x * 6 - perpendicular_x * 5,
                    center_y - direction_y * 6 - perpendicular_y * 5,
                )
                pygame.draw.polygon(surface, (245, 210, 125), [inner_tip, inner_left, inner_right])

    def draw_grid(self, surface):
        if self.map_name == "Spiral":
            return
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(surface, (40, 40, 40), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(surface, (40, 40, 40), (0, y), (WIDTH, y))

    def draw_grass_texture(self, surface):
        if self.map_name != "Spiral":
            return
        for x in range(16, WIDTH, 34):
            for y in range(12, HEIGHT, 32):
                if (x + y * 3) % 9 == 0:
                    continue
                offset_x = ((x * 13 + y * 7) % 17) - 8
                offset_y = ((x * 9 + y * 11) % 15) - 7
                plant_x = x + offset_x
                plant_y = y + offset_y
                if any(
                    self._distance_to_segment(plant_x, plant_y, start_x, start_y, end_x, end_y)
                    < PATH_WIDTH / 2 + 16
                    for (start_x, start_y), (end_x, end_y) in zip(
                        self.path_points, self.path_points[1:]
                    )
                ):
                    continue
                stem_len = 10 + ((x * 5 + y * 3) % 14)
                stem_color = (35, 90, 45)
                pygame.draw.line(surface, stem_color, (plant_x, plant_y + 8), (plant_x, plant_y - stem_len), 2)
                for leaf_index in range(4):
                    leaf_angle = (leaf_index / 4) * math.tau + ((x * 7 + y) % 7) * 0.3
                    leaf_x = plant_x + math.cos(leaf_angle) * (5 + (x % 5))
                    leaf_y = plant_y - stem_len * 0.6 + math.sin(leaf_angle) * (5 + (y % 5))
                    leaf_len = 10 + ((x * 3 + y * 5) % 12)
                    pygame.draw.ellipse(surface, (65, 145, 80), (leaf_x, leaf_y, leaf_len, 5))
                flower_size = 5 + ((x + y) % 4)
                pygame.draw.circle(surface, (190, 210, 110), (plant_x, plant_y - stem_len - 3), flower_size)
                pygame.draw.circle(surface, (120, 170, 90), (plant_x, plant_y - stem_len - 3), max(2, flower_size // 2))

    def draw_placement_preview(self, surface, mouse_pos):
        if self.game_over:
            return False

        grid_x = clamp(round(mouse_pos[0] / GRID_SIZE) * GRID_SIZE, GRID_SIZE // 2, WIDTH - GRID_SIZE // 2)
        grid_y = clamp(round(mouse_pos[1] / GRID_SIZE) * GRID_SIZE, GRID_SIZE // 2, HEIGHT - GRID_SIZE // 2)
        selected = self.selected_tower
        if selected == "mine":
            valid = self.is_tower_unlocked(selected) and self.money >= MINE_COST and self.can_place_mine(grid_x, grid_y)
        elif selected == "walker":
            valid = self.is_tower_unlocked(selected) and self.money >= WALKER_COST and self.can_place_mine(grid_x, grid_y)
        elif selected == "gunner":
            valid = self.is_tower_unlocked(selected) and self.money >= TOWER_TYPES[selected]["cost"] and self.can_place_mine(grid_x, grid_y)
        elif selected in TOWER_TYPES and TOWER_TYPES[selected].get("win_cost"):
            valid = self.can_buy_win_tower(selected) and grid_x <= WIDTH - 140 and self.can_place(grid_x, grid_y)
        elif selected in TOWER_TYPES:
            valid = (
                self.is_tower_unlocked(selected)
                and self.money >= TOWER_TYPES[selected]["cost"]
                and grid_x <= WIDTH - 140
                and self.can_place(grid_x, grid_y)
            )
        else:
            return False

        preview = pygame.Surface((64, 64), pygame.SRCALPHA)
        preview_center = (32, 32)
        if selected == "mine":
            Mine(*preview_center).draw(preview)
        elif selected == "walker":
            Walker(*preview_center, self.path_points).draw(preview)
        else:
            Tower(*preview_center, selected).draw(preview, show_range=False)
        preview.set_alpha(135 if valid else 170)
        surface.blit(preview, (grid_x - 32, grid_y - 32))

        outline_color = (100, 245, 165) if valid else (255, 90, 90)
        pygame.draw.rect(surface, outline_color, (grid_x - 20, grid_y - 20, GRID_SIZE, GRID_SIZE), 2)
        return valid

    def handle_developer_spawn_click(self, mouse_pos):
        if not self.developer_mode:
            return False
        for key, rect in self.developer_spawn_rects.items():
            if rect.collidepoint(mouse_pos):
                if key == "spawn":
                    self.developer_spawn_enemy()
                else:
                    self.set_developer_spawn_type(key)
                return True
        return False

    def draw(self, surface):
        surface.fill(self.background_color)
        self.draw_grid(surface)
        self.draw_path(surface)
        if self.map_name == "Spiral":
            self.draw_grass_texture(surface)

        for tower in self.towers:
            tower.draw(surface)

        for mine in self.mines:
            mine.draw(surface)

        for walker in self.walkers:
            walker.draw(surface)

        for projectile in self.projectiles:
            projectile.draw(surface)

        for explosion in self.explosions:
            explosion.draw(surface)

        for enemy in self.enemies:
            enemy.draw(surface)

        if self.map_name == "Spiral":
            self.draw_grass_texture(surface)

        self.draw_developer_stickman(surface)
        self.draw_placement_preview(surface, pygame.mouse.get_pos())

        tower_info = TOWER_TYPES.get(self.selected_tower)
        if self.selected_tower == "mine":
            selected_label = "Hidden" if not self.is_tower_unlocked("mine") else f"Mine (${MINE_COST})"
        elif self.selected_tower == "walker":
            selected_label = "Hidden" if not self.is_tower_unlocked("walker") else f"Walker (${WALKER_COST})"
        elif self.selected_tower in TOWER_TYPES:
            if "win_cost" in tower_info:
                selected_label = f"{tower_info['name']} ({tower_info['win_cost']} win)"
            elif self.selected_tower == "mine_tower":
                selected_label = f"Mine Tower (${TOWER_TYPES[self.selected_tower]['cost']})"
            else:
                selected_label = "Hidden" if not self.is_tower_unlocked(self.selected_tower) else f"{tower_info['name']} (${tower_info['cost']})"
        else:
            selected_label = "Unknown"
        rapid_label = "Rapid" if self.is_tower_unlocked("rapid") else "Hidden"
        sniper_label = "Sniper" if self.is_tower_unlocked("sniper") else "Hidden"
        mine_label = "Mine" if self.is_tower_unlocked("mine") else "Hidden"
        freeze_label = "Freeze" if self.is_tower_unlocked("freeze") else "Hidden"
        boinger_label = "Boinger" if self.is_tower_unlocked("boinger") else "Hidden"
        walker_label = "Walker" if self.is_tower_unlocked("walker") else "Hidden"
        gunner_label = "Runny Pew-Pew" if self.is_tower_unlocked("gunner") else "Hidden"
        mine_tower_label = "Mine Tower" if self.is_tower_unlocked("mine_tower") else "Hidden"
        warden_label = "Warden"
        nova_label = "Nova"
        spawner_label = "Spawner"
        status = [
            f"Money: {self.money}",
            f"Win coins: {self.win_coins}{' (sandbox run)' if self.sandbox else ''}",
            f"Lives: {self.lives}",
            f"Wave: {min(self.wave_index + 1, len(WAVES))}/{len(WAVES)}",
            f"Selected: {selected_label}",
            "Sandbox mode" if self.sandbox else "Basic unlocked. New towers unlock by wave.",
            "Enemies paused (Space to resume)" if self.enemies_paused else "Enemies running (Space to pause)" if self.developer_mode else "",
            "Arrow keys move enemies" if self.developer_mode else "",
            "Drag enemies with mouse" if self.developer_mode else "",
            "Click dev buttons to spawn" if self.developer_mode else "",
            f"Press 1=Basic 2={rapid_label} 3={sniper_label}",
            f"Press 4={mine_label} 5={freeze_label} 6={boinger_label} 7={walker_label}",
            f"Press 8={mine_tower_label} 9={warden_label} 0={nova_label}",
            f"Press A={spawner_label} B={gunner_label}",
            "Click tower to upgrade (+$80)",
        ]
        if self.developer_mode:
            developer_text = FONT.render("DEVELOPER MODE", True, (255, 220, 110))
            surface.blit(developer_text, (20, 12))
            spawn_button_y = 36
            self.developer_spawn_rects = {}
            enemy_types = [("ground", "Ground"), ("flyer", "Flyer"), ("shooter", "Shooter")]
            for index, (enemy_type, label) in enumerate(enemy_types):
                rect = pygame.Rect(20 + index * 110, spawn_button_y, 100, 28)
                self.developer_spawn_rects[enemy_type] = rect
                color = (110, 170, 90) if self.developer_spawn_type == enemy_type else (70, 80, 95)
                pygame.draw.rect(surface, color, rect, border_radius=6)
                pygame.draw.rect(surface, (180, 220, 200), rect, 2, border_radius=6)
                button_text = FONT.render(label, True, (255, 255, 255))
                surface.blit(button_text, (rect.x + 12, rect.y + 6))

            spawn_rect = pygame.Rect(20, spawn_button_y + 36, 150, 30)
            self.developer_spawn_rects["spawn"] = spawn_rect
            pygame.draw.rect(surface, (140, 90, 60), spawn_rect, border_radius=6)
            pygame.draw.rect(surface, (250, 200, 180), spawn_rect, 2, border_radius=6)
            spawn_text = FONT.render(f"Spawn {self.developer_spawn_type.title()}", True, (255, 255, 255))
            surface.blit(spawn_text, (spawn_rect.x + 10, spawn_rect.y + 6))
        for i, line in enumerate(status):
            text = FONT.render(line, True, (240, 240, 240))
            surface.blit(text, (WIDTH - 20 - text.get_width(), 12 + i * 20))

        button_color = (70, 130, 190) if self.wave_index + 1 < len(WAVES) else (90, 90, 90)
        border_color = (170, 210, 255) if self.wave_index + 1 < len(WAVES) else (130, 130, 130)
        pygame.draw.rect(surface, button_color, self.wave_button_rect, border_radius=8)
        pygame.draw.rect(surface, border_color, self.wave_button_rect, 2, border_radius=8)
        if self.wave_index + 1 < len(WAVES):
            button_label = f"Send Wave {self.wave_index + 2}"
        else:
            button_label = "No more waves"
        button_text = FONT.render(button_label, True, (255, 255, 255))
        surface.blit(
            button_text,
            (
                self.wave_button_rect.x + (self.wave_button_rect.width - button_text.get_width()) // 2,
                self.wave_button_rect.y + (self.wave_button_rect.height - button_text.get_height()) // 2,
            ),
        )
        if self.wave_index + 1 < len(WAVES):
            hint_text = FONT.render("Click to launch the next wave", True, (200, 230, 255))
            surface.blit(hint_text, (self.wave_button_rect.x + 10, self.wave_button_rect.y + self.wave_button_rect.height + 8))

        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            if self.victory:
                message = "VICTORY! All waves defeated."
            else:
                message = "GAME OVER! You have been overwhelmed."
            msg_surface = FONT.render(message, True, (255, 255, 255))
            surface.blit(msg_surface, (WIDTH // 2 - msg_surface.get_width() // 2, HEIGHT // 2 - 10))
            restart_surface = FONT.render("Press R to restart.", True, (255, 255, 255))
            surface.blit(restart_surface, (WIDTH // 2 - restart_surface.get_width() // 2, HEIGHT // 2 + 20))


def draw_achievement_icon(surface, achievement_id, center):
    center_x, center_y = center
    if achievement_id == "developer_mode":
        pygame.draw.rect(surface, (45, 55, 65), (center_x - 10, center_y - 13, 20, 5))
        pygame.draw.rect(surface, (210, 75, 65), (center_x - 7, center_y - 19, 14, 7))
        pygame.draw.circle(surface, (245, 205, 155), (center_x, center_y - 3), 6)
        pygame.draw.line(surface, (240, 240, 240), (center_x, center_y + 3), (center_x, center_y + 13), 3)
        pygame.draw.line(surface, (240, 240, 240), (center_x, center_y + 6), (center_x - 8, center_y + 11), 3)
        pygame.draw.line(surface, (240, 240, 240), (center_x, center_y + 6), (center_x + 8, center_y + 11), 3)
    elif achievement_id == "first_wave":
        pygame.draw.line(surface, (225, 225, 220), (center_x - 8, center_y - 14), (center_x - 8, center_y + 14), 3)
        pygame.draw.polygon(surface, (80, 205, 125), [(center_x - 6, center_y - 13), (center_x + 11, center_y - 8), (center_x - 6, center_y - 2)])
        pygame.draw.circle(surface, (255, 220, 90), (center_x + 1, center_y - 8), 2)
    elif achievement_id == "the_beginning":
        for offset in (-10, 0, 10):
            pygame.draw.line(surface, (255, 220, 115), (center_x + offset, center_y - 14), (center_x + offset, center_y - 10), 2)
        pygame.draw.circle(surface, (255, 195, 70), (center_x, center_y), 8)
        pygame.draw.rect(surface, (57, 105, 77), (center_x - 10, center_y + 2, 20, 10))
        pygame.draw.line(surface, (235, 240, 215), (center_x - 12, center_y + 3), (center_x + 12, center_y + 3), 2)
    elif achievement_id == "code_rain":
        for column, lengths in enumerate(((5, 8, 4), (8, 5, 7), (4, 7, 5))):
            x = center_x - 9 + column * 9
            for row, length in enumerate(lengths):
                y = center_y - 13 + row * 9 + column * 2
                pygame.draw.rect(surface, (75, 255 - row * 35, 115), (x, y, 4, length), border_radius=1)
    elif achievement_id == "bullet_time":
        pygame.draw.circle(surface, (100, 235, 160), center, 12, 2)
        pygame.draw.line(surface, (245, 245, 225), (center_x, center_y - 8), (center_x + 5, center_y + 1), 3)
        pygame.draw.circle(surface, (255, 215, 90), (center_x + 5, center_y + 1), 3)
        pygame.draw.line(surface, (80, 215, 140), (center_x - 14, center_y - 8), (center_x - 10, center_y - 8), 2)
        pygame.draw.line(surface, (80, 215, 140), (center_x - 14, center_y), (center_x - 10, center_y), 2)
    elif achievement_id == "matrix_dodge":
        pygame.draw.line(surface, (80, 245, 145), (center_x - 15, center_y - 10), (center_x - 3, center_y - 10), 2)
        pygame.draw.line(surface, (80, 245, 145), (center_x - 15, center_y), (center_x - 7, center_y), 2)
        pygame.draw.circle(surface, (240, 245, 225), (center_x + 5, center_y - 8), 4)
        pygame.draw.line(surface, (240, 245, 225), (center_x + 3, center_y - 3), (center_x - 4, center_y + 5), 3)
        pygame.draw.line(surface, (240, 245, 225), (center_x, center_y), (center_x + 10, center_y + 4), 2)
        pygame.draw.line(surface, (240, 245, 225), (center_x - 3, center_y + 4), (center_x - 9, center_y + 11), 2)
        pygame.draw.line(surface, (240, 245, 225), (center_x - 3, center_y + 4), (center_x + 3, center_y + 12), 2)
    elif achievement_id == "exit_construct":
        pygame.draw.rect(surface, (80, 235, 145), (center_x - 10, center_y - 14, 20, 28), 2)
        pygame.draw.rect(surface, (190, 255, 215), (center_x - 4, center_y - 8, 9, 22), 1)
        pygame.draw.line(surface, (255, 225, 100), (center_x + 1, center_y + 3), (center_x + 8, center_y + 3), 2)
        pygame.draw.polygon(surface, (255, 225, 100), [(center_x + 8, center_y), (center_x + 12, center_y + 3), (center_x + 8, center_y + 6)])
    elif achievement_id == "wave_six":
        pygame.draw.polygon(surface, (90, 165, 240), [(center_x - 10, center_y - 12), (center_x - 3, center_y - 8), (center_x - 6, center_y + 3), (center_x - 11, center_y - 2)])
        pygame.draw.polygon(surface, (90, 165, 240), [(center_x + 10, center_y - 12), (center_x + 3, center_y - 8), (center_x + 6, center_y + 3), (center_x + 11, center_y - 2)])
        pygame.draw.circle(surface, (255, 205, 70), center, 10)
        pygame.draw.circle(surface, (255, 240, 170), center, 7, 2)
        number = FONT.render("6", True, (90, 65, 30))
        surface.blit(number, (center_x - number.get_width() // 2, center_y - number.get_height() // 2))
    elif achievement_id == "spiral_map":
        points = []
        for step in range(48):
            angle = step * math.tau / 24
            radius = 1 + step * 0.25
            points.append((round(center_x + math.cos(angle) * radius), round(center_y + math.sin(angle) * radius)))
        pygame.draw.lines(surface, (100, 225, 145), False, points, 3)
        pygame.draw.circle(surface, (245, 220, 115), points[-1], 3)
    elif achievement_id == "first_costume":
        pygame.draw.polygon(surface, (110, 190, 245), [(center_x - 8, center_y - 8), (center_x - 14, center_y - 2), (center_x - 10, center_y + 3), (center_x - 7, center_y + 1), (center_x - 7, center_y + 13), (center_x + 7, center_y + 13), (center_x + 7, center_y + 1), (center_x + 10, center_y + 3), (center_x + 14, center_y - 2), (center_x + 8, center_y - 8)])
        pygame.draw.circle(surface, (255, 225, 100), (center_x, center_y - 3), 2)
        pygame.draw.circle(surface, (255, 225, 100), (center_x, center_y + 4), 2)


def draw_achievement_popups(surface):
    for index, popup in enumerate(ACHIEVEMENT_POPUPS):
        achievement_id = popup["achievement_id"]
        info = ACHIEVEMENTS[achievement_id]
        rect = pygame.Rect(WIDTH - 310, HEIGHT - 76 - index * 64, 290, 58)
        pygame.draw.rect(surface, (27, 36, 43), rect, border_radius=6)
        pygame.draw.rect(surface, (245, 200, 95), rect, 2, border_radius=6)
        draw_achievement_icon(surface, achievement_id, (rect.x + 27, rect.centery))
        heading = FONT.render("Achievement unlocked!", True, (255, 220, 130))
        name = FONT.render(info["name"], True, (255, 255, 255))
        surface.blit(heading, (rect.x + 54, rect.y + 5))
        surface.blit(name, (rect.x + 54, rect.y + 29))


def draw_achievements_window(surface, achievements):
    surface.fill((18, 24, 36))
    title = FONT.render("Achievements", True, (255, 225, 145))
    surface.blit(title, (32, 24))
    unlocked_count = len(achievements & ACHIEVEMENTS.keys())
    progress = FONT.render(f"Unlocked: {unlocked_count}/{len(ACHIEVEMENTS)}", True, (190, 210, 225))
    surface.blit(progress, (32, 58))
    for index, (achievement_id, info) in enumerate(ACHIEVEMENTS.items()):
        unlocked = achievement_id in achievements
        rect = pygame.Rect(32, 92 + index * 45, 536, 40)
        pygame.draw.rect(surface, (57, 105, 77) if unlocked else (48, 58, 72), rect, border_radius=5)
        pygame.draw.rect(surface, (145, 185, 160) if unlocked else (105, 120, 140), rect, 1, border_radius=5)
        name = FONT.render(info["name"], True, (255, 255, 255))
        description = FONT.render(info["description"], True, (205, 215, 225))
        if unlocked:
            draw_achievement_icon(surface, achievement_id, (rect.x + 26, rect.centery))
        surface.blit(name, (rect.x + 58, rect.y + 1))
        surface.blit(description, (rect.x + 58, rect.y + 20))
        status = FONT.render("Unlocked" if unlocked else "Locked", True, (185, 245, 195) if unlocked else (165, 175, 190))
        surface.blit(status, (rect.right - status.get_width() - 12, rect.y + 14))


def run_achievements_window():
    surface = pygame.display.set_mode((600, 560))
    pygame.display.set_caption("Achievements")
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
        draw_achievements_window(surface, load_achievements())
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


def open_achievements_window():
    return subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "--achievements"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )


def draw_achievements_button(surface):
    pygame.draw.rect(surface, (85, 105, 145), ACHIEVEMENTS_BUTTON_RECT, border_radius=7)
    pygame.draw.rect(surface, (180, 205, 245), ACHIEVEMENTS_BUTTON_RECT, 2, border_radius=7)
    label = FONT.render("Achievements", True, (255, 255, 255))
    surface.blit(
        label,
        (
            ACHIEVEMENTS_BUTTON_RECT.centerx - label.get_width() // 2,
            ACHIEVEMENTS_BUTTON_RECT.centery - label.get_height() // 2,
        ),
    )


def draw_map_selection(
    surface,
    selected_map,
    sandbox_mode,
    unlocked_maps,
    win_coins,
    unlocked_costumes,
    equipped_costume,
    developer_mode_opened=False,
    costume_window_open=False,
    preview_costume=None,
    hat_text_value="sick-man",
    hat_text_editing=False,
    hat_text_input="sick-man",
    hat_id="classic",
    unlocked_hats=None,
    leg_id="classic",
    unlocked_legs=None,
    suit_id="classic",
    unlocked_suits=None,
    object_id="none",
    unlocked_objects=None,
    achievements=None,
):
    unlocked_hats = set(unlocked_hats or {"classic"})
    surface.fill((18, 24, 36))
    title = FONT.render("Select a map before starting:", True, (255, 255, 255))
    surface.blit(title, (40, 40))
    costume_buttons = {}
    for index, map_name in enumerate(MAPS.keys(), start=1):
        prefix = "> " if map_name == selected_map else "  "
        if map_name in unlocked_maps:
            map_label = map_name
        else:
            map_label = f"{map_name} ({MAP_UNLOCK_COST} win coins)"
        label = FONT.render(f"{prefix}{index}. {map_label}", True, (220, 220, 220))
        surface.blit(label, (60, 80 + index * 30))
        if map_name == "Spiral" and map_name not in unlocked_maps:
            pygame.draw.rect(surface, (80, 150, 95), SPIRAL_BUY_RECT, border_radius=5)
            pygame.draw.rect(surface, (160, 230, 170), SPIRAL_BUY_RECT, 2, border_radius=5)
            buy_text = FONT.render("BUY", True, (255, 255, 255))
            surface.blit(
                buy_text,
                (
                    SPIRAL_BUY_RECT.x + (SPIRAL_BUY_RECT.width - buy_text.get_width()) // 2,
                    SPIRAL_BUY_RECT.y + (SPIRAL_BUY_RECT.height - buy_text.get_height()) // 2,
                ),
            )

    sandbox_text = FONT.render(f"Sandbox mode: {'ON' if sandbox_mode else 'OFF'} (Press S)", True, (180, 255, 180) if sandbox_mode else (220, 220, 220))
    surface.blit(sandbox_text, (40, 230))

    unlock_title = FONT.render("Tower unlocks:", True, (255, 255, 255))
    surface.blit(unlock_title, (440, 40))
    unlock_rules = [
        "Basic: start",
        "Rapid: wave 2",
        "Mine: wave 2",
        "Sniper: wave 3",
        "Freeze: wave 4",
        "Boinger: wave 5",
        "Walker: wave 6",
        "Runny Pew-Pew: wave 6",
        "  Mine Tower: ???",

    ]
    for index, rule in enumerate(unlock_rules):
        text = FONT.render(rule, True, (220, 220, 220))
        surface.blit(text, (440, 70 + index * 22))

    if developer_mode_opened:
        pygame.draw.rect(surface, (85, 105, 145), HOME_COSTUMES_RECT, border_radius=7)
        pygame.draw.rect(surface, (180, 205, 245), HOME_COSTUMES_RECT, 2, border_radius=7)
        costumes_text = FONT.render("COSTUMES", True, (255, 255, 255))
        surface.blit(
            costumes_text,
            (
                HOME_COSTUMES_RECT.x + (HOME_COSTUMES_RECT.width - costumes_text.get_width()) // 2,
                HOME_COSTUMES_RECT.y + (HOME_COSTUMES_RECT.height - costumes_text.get_height()) // 2,
            ),
        )
        if costume_window_open:
            pygame.draw.rect(surface, (20, 27, 42), HOME_COSTUME_WINDOW_RECT, border_radius=10)
            pygame.draw.rect(surface, (185, 210, 245), HOME_COSTUME_WINDOW_RECT, 2, border_radius=10)
            title = FONT.render("Stickman costumes", True, (255, 255, 255))
            surface.blit(title, (HOME_COSTUME_WINDOW_RECT.x + 24, HOME_COSTUME_WINDOW_RECT.y + 18))
            pygame.draw.rect(surface, (115, 82, 82), HOME_COSTUME_CLOSE_RECT, border_radius=5)
            pygame.draw.rect(surface, (210, 160, 160), HOME_COSTUME_CLOSE_RECT, 2, border_radius=5)
            close_text = FONT.render("Close", True, (255, 255, 255))
            surface.blit(close_text, (HOME_COSTUME_CLOSE_RECT.x + 8, HOME_COSTUME_CLOSE_RECT.y + 3))
            preview_id = preview_costume or equipped_costume
            preview_name = FONT.render(STICKMAN_COSTUMES[preview_id]["name"], True, (255, 225, 145))
            surface.blit(preview_name, (HOME_COSTUME_WINDOW_RECT.x + 330, HOME_COSTUME_WINDOW_RECT.y + 62))
            draw_stickman_preview(
                surface,
                HOME_COSTUME_WINDOW_RECT.x + 430,
                HOME_COSTUME_WINDOW_RECT.y + 165,
                preview_id,
                hat_id=hat_id,
                hat_text=hat_text_value,
                leg_id=leg_id,
                suit_id=suit_id,
                object_id=object_id,
            )
            costumes_section = FONT.render("Costumes", True, (170, 200, 235))
            surface.blit(costumes_section, (HOME_COSTUME_WINDOW_RECT.x + 24, HOME_COSTUME_WINDOW_RECT.y + 42))
            rect = pygame.Rect(HOME_COSTUME_WINDOW_RECT.x + 24, HOME_COSTUME_WINDOW_RECT.y + 62, 250, 28)
            costume_buttons["classic"] = rect
            color = (75, 110, 85) if preview_id == "classic" else (70, 90, 100)
            pygame.draw.rect(surface, color, rect, border_radius=5)
            pygame.draw.rect(surface, (200, 220, 240), rect, 1, border_radius=5)
            label = "Classic (equipped)" if equipped_costume == "classic" else "Classic"
            text = FONT.render(label, True, (240, 240, 240))
            surface.blit(text, (rect.x + 8, rect.y + 5))
            hats_section = FONT.render("Hats", True, (240, 210, 150))
            surface.blit(hats_section, (HOME_COSTUME_WINDOW_RECT.x + 24, HOME_COSTUME_WINDOW_RECT.y + 102))
            hat_text_rect = pygame.Rect(HOME_COSTUME_WINDOW_RECT.x + 24, HOME_COSTUME_WINDOW_RECT.y + 126, 250, 28)
            costume_buttons["hat_text"] = hat_text_rect
            fill_color = (120, 100, 80) if hat_text_editing else (95, 86, 62)
            pygame.draw.rect(surface, fill_color, hat_text_rect, border_radius=5)
            pygame.draw.rect(surface, (240, 216, 180), hat_text_rect, 1, border_radius=5)
            button_label = "Press Enter to save" if hat_text_editing else "Edit hat text (5 win)"
            hat_label = FONT.render(button_label, True, (255, 255, 255))
            surface.blit(hat_label, (hat_text_rect.x + 8, hat_text_rect.y + 5))
            hat_options = [
                "classic",
                "loser",
                "war",
                "wizard",
                "headphones",
                "graduation",
                "bicycle",
                "cardboard",
                "powder",
            ]
            for index, option_id in enumerate(hat_options):
                option_rect = pygame.Rect(
                    HOME_COSTUME_WINDOW_RECT.x + 24,
                    HOME_COSTUME_WINDOW_RECT.y + 160 + index * 34,
                    250,
                    28,
                )
                button_id = f"hat_{option_id}"
                costume_buttons[button_id] = option_rect
                is_equipped = hat_id == option_id
                is_unlocked = option_id in unlocked_hats
                pygame.draw.rect(
                    surface,
                    (75, 110, 85) if is_equipped else (70, 90, 100) if is_unlocked else (95, 86, 62),
                    option_rect,
                    border_radius=5,
                )
                pygame.draw.rect(surface, (200, 220, 240), option_rect, 1, border_radius=5)
                hat_info = STICKMAN_HATS[option_id]
                if is_equipped:
                    option_label = f"{hat_info['name']} (equipped)"
                elif is_unlocked:
                    option_label = hat_info["name"]
                elif hat_info["price"]:
                    option_label = f"{hat_info['name']} ({hat_info['price']} win)"
                else:
                    option_label = hat_info["name"]
                option_surface = FONT.render(option_label, True, (255, 255, 255))
                surface.blit(option_surface, (option_rect.x + 8, option_rect.y + 5))
            hat_text_value_surface = FONT.render(f"Current text: {hat_text_value}", True, (255, 245, 180))
            surface.blit(hat_text_value_surface, (HOME_COSTUME_WINDOW_RECT.x + 330, HOME_COSTUME_WINDOW_RECT.y + 210))
            if hat_text_editing:
                input_rect = pygame.Rect(HOME_COSTUME_WINDOW_RECT.x + 330, HOME_COSTUME_WINDOW_RECT.y + 236, 220, 28)
                pygame.draw.rect(surface, (70, 90, 105), input_rect, border_radius=5)
                pygame.draw.rect(surface, (200, 220, 245), input_rect, 1, border_radius=5)
                input_surface = FONT.render(hat_text_input, True, (255, 255, 255))
                surface.blit(input_surface, (input_rect.x + 8, input_rect.y + 5))
            legs_section = FONT.render("Legs", True, (180, 245, 200))
            surface.blit(legs_section, (HOME_COSTUME_WINDOW_RECT.x + 330, HOME_COSTUME_WINDOW_RECT.y + 240))
            leg_options = ["classic", "hermes", "boots"]
            for index, option_id in enumerate(leg_options):
                leg_rect = pygame.Rect(HOME_COSTUME_WINDOW_RECT.x + 330, HOME_COSTUME_WINDOW_RECT.y + 262 + index * 34, 180, 28)
                option_key = f"leg_{option_id}"
                costume_buttons[option_key] = leg_rect
                is_equipped = leg_id == option_id
                is_unlocked = unlocked_legs is not None and option_id in unlocked_legs
                pygame.draw.rect(surface, (75, 110, 85) if is_equipped else (70, 90, 100) if is_unlocked else (95, 86, 62), leg_rect, border_radius=5)
                pygame.draw.rect(surface, (200, 220, 240), leg_rect, 1, border_radius=5)
                info_name = STICKMAN_LEGS[option_id]["name"]
                label_text = f"{info_name} (equipped)" if is_equipped else info_name if is_unlocked else f"{info_name} ({STICKMAN_LEGS[option_id]['price']} win)"
                leg_label = FONT.render(label_text, True, (255, 255, 255))
                surface.blit(leg_label, (leg_rect.x + 8, leg_rect.y + 5))
            suits_section = FONT.render("Suits", True, (200, 175, 255))
            surface.blit(suits_section, (HOME_COSTUME_WINDOW_RECT.x + 330, HOME_COSTUME_WINDOW_RECT.y + 350))
            suit_options = ["classic", "fish", "cactus", "jetpack"]
            for index, option_id in enumerate(suit_options):
                suit_rect = pygame.Rect(HOME_COSTUME_WINDOW_RECT.x + 330, HOME_COSTUME_WINDOW_RECT.y + 372 + index * 34, 180, 28)
                option_key = f"suit_{option_id}"
                costume_buttons[option_key] = suit_rect
                is_equipped = suit_id == option_id
                is_unlocked = unlocked_suits is not None and option_id in unlocked_suits
                pygame.draw.rect(surface, (75, 110, 85) if is_equipped else (70, 90, 100) if is_unlocked else (95, 86, 62), suit_rect, border_radius=5)
                pygame.draw.rect(surface, (200, 220, 240), suit_rect, 1, border_radius=5)
                info_name = STICKMAN_SUITS[option_id]["name"]
                label_text = f"{info_name} (equipped)" if is_equipped else info_name if is_unlocked else f"{info_name} ({STICKMAN_SUITS[option_id]['price']} win)"
                suit_label = FONT.render(label_text, True, (255, 255, 255))
                surface.blit(suit_label, (suit_rect.x + 8, suit_rect.y + 5))
            objects_section = FONT.render("Objects", True, (255, 185, 220))
            surface.blit(objects_section, (HOME_COSTUME_WINDOW_RECT.x + 470, HOME_COSTUME_WINDOW_RECT.y + 442))
            object_options = ["none", "magic_hat", "sword"]
            for index, option_id in enumerate(object_options):
                object_rect = pygame.Rect(HOME_COSTUME_WINDOW_RECT.x + 470, HOME_COSTUME_WINDOW_RECT.y + 462 + index * 24, 180, 22)
                option_key = f"object_{option_id}"
                costume_buttons[option_key] = object_rect
                is_equipped = object_id == option_id
                is_unlocked = unlocked_objects is not None and option_id in unlocked_objects
                pygame.draw.rect(surface, (75, 110, 85) if is_equipped else (70, 90, 100) if is_unlocked else (95, 86, 62), object_rect, border_radius=5)
                pygame.draw.rect(surface, (200, 220, 240), object_rect, 1, border_radius=5)
                info_name = STICKMAN_OBJECTS[option_id]["name"]
                label_text = f"{info_name} (equipped)" if is_equipped else info_name if is_unlocked else f"{info_name} ({STICKMAN_OBJECTS[option_id]['price']} win)"
                object_label = FONT.render(label_text, True, (255, 255, 255))
                surface.blit(object_label, (object_rect.x + 6, object_rect.y + 3))

    if not costume_window_open:
        info = FONT.render("Press Enter to start. Use keys 1-4 to choose a map.", True, (180, 180, 180))
        surface.blit(info, (40, 270))
        note = FONT.render("You can change tower types after the game starts.", True, (180, 180, 180))
        surface.blit(note, (40, 310))
        coins = FONT.render(f"Win coins: {win_coins}", True, (255, 220, 120))
        surface.blit(coins, (40, 350))

        pygame.draw.rect(surface, (85, 105, 145), BACKSTORY_RECT, border_radius=7)
        pygame.draw.rect(surface, (180, 205, 245), BACKSTORY_RECT, 2, border_radius=7)
        backstory_text = FONT.render("VIEW BACKSTORY", True, (255, 255, 255))
        surface.blit(
            backstory_text,
            (
                BACKSTORY_RECT.x + (BACKSTORY_RECT.width - backstory_text.get_width()) // 2,
                BACKSTORY_RECT.y + (BACKSTORY_RECT.height - backstory_text.get_height()) // 2,
            ),
        )
        draw_achievements_button(surface)
    return costume_buttons


def draw_backstory(surface):
    surface.fill((22, 28, 42))
    title = FONT.render("The Monster Roads", True, (255, 225, 145))
    surface.blit(title, (40, 44))
    story_lines = [
        "Another great war has occured, and the only survivors are",
        "You and, sick-man stickman?!? Anyway, with the enemies",
        "marching in, you have to stop them. Or else, they will",
        "quickly end you. Let's hope sick-man stickman can help!",
    ]
    for index, line in enumerate(story_lines):
        text = FONT.render(line, True, (225, 230, 240))
        surface.blit(text, (50, 105 + index * 30))

    controls = FONT.render("Click anywhere or press Escape to return", True, (180, 200, 225))
    surface.blit(controls, (50, 370))


def main():
    check_achievements()
    selected_map = DEFAULT_MAP
    sandbox_mode = False
    unlocked_maps = load_unlocked_maps()
    _, menu_win_coins = load_progress()
    menu_developer_mode_opened = load_developer_mode_state()
    menu_stickman_costumes, menu_equipped_costume = load_stickman_costumes()
    menu_stickman_hat_text = load_stickman_hat_text()
    menu_stickman_hat = load_stickman_hat()
    menu_stickman_hats = load_stickman_hats()
    menu_stickman_legs = load_stickman_legs_unlocked()
    menu_stickman_leg = load_stickman_legs()
    menu_stickman_suits = load_stickman_suits()
    menu_stickman_suit = load_stickman_suit()
    menu_stickman_objects = load_stickman_objects()
    menu_stickman_object = "none"
    menu_hat_text_editing = False
    menu_hat_text_input = menu_stickman_hat_text
    game = None
    in_menu = True
    show_backstory = False
    show_costume_window = False
    preview_costume = menu_equipped_costume
    running = True
    menu_costume_buttons = {}
    achievements_process = None
    achievement_check_timer = 0.0

    while running:
        dt = CLOCK.tick(FPS) / 1000.0
        achievement_check_timer = update_achievement_check_timer(achievement_check_timer, dt, game)
        update_achievement_popups(dt)
        if in_menu:
            menu_developer_mode_opened = load_developer_mode_state()
            menu_stickman_costumes, menu_equipped_costume = load_stickman_costumes()
            menu_stickman_hat_text = load_stickman_hat_text()
            menu_stickman_hat = load_stickman_hat()
            menu_stickman_hats = load_stickman_hats()
            menu_stickman_legs = load_stickman_legs_unlocked()
            menu_stickman_leg = load_stickman_legs()
            menu_stickman_suit = load_stickman_suit()
            menu_stickman_object = load_stickman_object()
            preview_costume = menu_equipped_costume
            if not menu_hat_text_editing:
                menu_hat_text_input = menu_stickman_hat_text

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if in_menu:
                    if show_backstory:
                        if event.key == pygame.K_ESCAPE:
                            show_backstory = False
                        continue
                    if show_costume_window and menu_hat_text_editing:
                        if event.key == pygame.K_ESCAPE:
                            menu_hat_text_editing = False
                            menu_hat_text_input = menu_stickman_hat_text
                        elif event.key == pygame.K_RETURN:
                            candidate = menu_hat_text_input.strip()[:16]
                            if candidate:
                                if sandbox_mode:
                                    menu_stickman_hat_text = candidate
                                elif menu_win_coins >= 5:
                                    menu_win_coins -= 5
                                    menu_stickman_hat_text = candidate
                                    save_unlocks(
                                        load_unlocks(),
                                        menu_win_coins,
                                        unlocked_maps,
                                        highest_cleared_wave=load_highest_cleared_wave(),
                                        stickman_costumes=menu_stickman_costumes,
                                        equipped_stickman_costume=menu_equipped_costume,
                                        developer_mode_opened=menu_developer_mode_opened,
                                        stickman_hat_text=menu_stickman_hat_text,
                                    )
                                else:
                                    candidate = menu_stickman_hat_text
                            menu_hat_text_input = menu_stickman_hat_text
                            menu_hat_text_editing = False
                        elif event.key == pygame.K_BACKSPACE:
                            menu_hat_text_input = menu_hat_text_input[:-1]
                        elif event.unicode and event.unicode.isprintable():
                            if len(menu_hat_text_input) < 16:
                                menu_hat_text_input += event.unicode
                        continue
                    if show_costume_window and event.key == pygame.K_ESCAPE:
                        show_costume_window = False
                        continue
                    if event.unicode and event.unicode.isprintable():
                        if game is not None:
                            game.register_key(event.unicode)
                    if event.key == pygame.K_RETURN:
                        game = Game(MAPS[selected_map], sandbox=sandbox_mode, map_name=selected_map)
                        in_menu = False
                    elif event.key == pygame.K_s:
                        sandbox_mode = not sandbox_mode
                    elif event.key == pygame.K_1:
                        selected_map = list(MAPS.keys())[0]
                    elif event.key == pygame.K_2:
                        selected_map = list(MAPS.keys())[1]
                    elif event.key == pygame.K_3:
                        selected_map = list(MAPS.keys())[2]
                    elif event.key == pygame.K_4:
                        map_name = list(MAPS.keys())[3]
                        if map_name in unlocked_maps:
                            selected_map = map_name
                else:
                    if event.unicode and event.unicode.isprintable():
                        game.register_key(event.unicode)
                    if not game.game_over and event.unicode and event.unicode.isprintable():
                        game.key_buffer += event.unicode
                        if len(game.key_buffer) > 12:
                            game.key_buffer = game.key_buffer[-12:]
                        if "soft&ball" in game.key_buffer.lower():
                            game.upgrade_all_towers()
                            game.key_buffer = ""

                    if event.key == pygame.K_r and game.game_over:
                        game = Game(MAPS[selected_map], sandbox=game.sandbox, map_name=selected_map)
                    elif event.key == pygame.K_SPACE:
                        game.toggle_enemy_pause()
                    elif event.key == pygame.K_UP:
                        game.move_enemies(0, -20)
                    elif event.key == pygame.K_DOWN:
                        game.move_enemies(0, 20)
                    elif event.key == pygame.K_LEFT:
                        game.move_enemies(-20, 0)
                    elif event.key == pygame.K_RIGHT:
                        game.move_enemies(20, 0)
                    elif event.key == pygame.K_1:
                        game.selected_tower = "basic"
                    elif event.key == pygame.K_2:
                        if game.is_tower_unlocked("rapid"):
                            game.selected_tower = "rapid"
                    elif event.key == pygame.K_3:
                        if game.is_tower_unlocked("sniper"):
                            game.selected_tower = "sniper"
                    elif event.key == pygame.K_4:
                        if game.is_tower_unlocked("mine"):
                            game.selected_tower = "mine"
                    elif event.key == pygame.K_5:
                        if game.is_tower_unlocked("freeze"):
                            game.selected_tower = "freeze"
                    elif event.key == pygame.K_6:
                        if game.is_tower_unlocked("boinger"):
                            game.selected_tower = "boinger"
                    elif event.key == pygame.K_7:
                        if game.is_tower_unlocked("walker"):
                            game.selected_tower = "walker"
                    elif event.key == pygame.K_8:
                        if game.is_tower_unlocked("mine_tower"):
                            game.selected_tower = "mine_tower"
                    elif event.key == pygame.K_9:
                        if game.can_buy_win_tower("warden"):
                            game.selected_tower = "warden"
                    elif event.key == pygame.K_0:
                        if game.can_buy_win_tower("nova"):
                            game.selected_tower = "nova"
                    elif event.key == pygame.K_a:
                        if game.can_buy_win_tower("spawner"):
                            game.selected_tower = "spawner"
                    elif event.key == pygame.K_b:
                        if game.is_tower_unlocked("gunner"):
                            game.selected_tower = "gunner"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if in_menu:
                    if show_backstory:
                        show_backstory = False
                    elif show_costume_window:
                        if HOME_COSTUME_CLOSE_RECT.collidepoint(event.pos):
                            show_costume_window = False
                        else:
                            for costume_id, rect in menu_costume_buttons.items():
                                if rect.collidepoint(event.pos):
                                    if costume_id == "hat_text":
                                        menu_hat_text_editing = True
                                        menu_hat_text_input = menu_stickman_hat_text
                                        break
                                    if costume_id.startswith("hat_"):
                                        selected_hat = costume_id[4:]
                                        if selected_hat not in menu_stickman_hats:
                                            hat_price = STICKMAN_HATS[selected_hat]["price"]
                                            if not sandbox_mode and menu_win_coins < hat_price:
                                                break
                                            if not sandbox_mode:
                                                menu_win_coins -= hat_price
                                            menu_stickman_hats.add(selected_hat)
                                        menu_stickman_hat = selected_hat
                                        if selected_hat != "classic":
                                            achievements = load_achievements()
                                            if not sandbox_mode:
                                                award_achievement(achievements, "first_costume")
                                                save_unlocks(
                                                    load_unlocks(),
                                                    menu_win_coins,
                                                    unlocked_maps,
                                                    stickman_costumes=menu_stickman_costumes,
                                                    equipped_stickman_costume=menu_equipped_costume,
                                                    developer_mode_opened=menu_developer_mode_opened,
                                                    stickman_hat_text=menu_stickman_hat_text,
                                                    stickman_hat=menu_stickman_hat,
                                                    stickman_hats=menu_stickman_hats,
                                                    stickman_legs=menu_stickman_leg,
                                                    stickman_legs_unlocked=menu_stickman_legs,
                                                    stickman_suit=menu_stickman_suit,
                                                    stickman_suits=menu_stickman_suits,
                                                    stickman_object=menu_stickman_object,
                                                    stickman_objects=menu_stickman_objects,
                                                    achievements=achievements,
                                                )
                                    elif costume_id.startswith("leg_"):
                                        selected_leg = costume_id[4:]
                                        if selected_leg not in menu_stickman_legs:
                                            leg_price = STICKMAN_LEGS[selected_leg]["price"]
                                            if not sandbox_mode and menu_win_coins < leg_price:
                                                break
                                            if not sandbox_mode:
                                                menu_win_coins -= leg_price
                                            menu_stickman_legs.add(selected_leg)
                                        menu_stickman_leg = selected_leg
                                        if selected_leg != "classic":
                                            achievements = load_achievements()
                                            if not sandbox_mode:
                                                award_achievement(achievements, "first_costume")
                                                save_unlocks(
                                                    load_unlocks(),
                                                    menu_win_coins,
                                                    unlocked_maps,
                                                    stickman_costumes=menu_stickman_costumes,
                                                    equipped_stickman_costume=menu_equipped_costume,
                                                    developer_mode_opened=menu_developer_mode_opened,
                                                    stickman_hat_text=menu_stickman_hat_text,
                                                    stickman_hat=menu_stickman_hat,
                                                    stickman_hats=menu_stickman_hats,
                                                    stickman_legs=menu_stickman_leg,
                                                    stickman_legs_unlocked=menu_stickman_legs,
                                                    stickman_suit=menu_stickman_suit,
                                                    stickman_suits=menu_stickman_suits,
                                                    stickman_object=menu_stickman_object,
                                                    stickman_objects=menu_stickman_objects,
                                                    achievements=achievements,
                                                )
                                    elif costume_id.startswith("suit_"):
                                        selected_suit = costume_id[5:]
                                        if selected_suit not in menu_stickman_suits:
                                            suit_price = STICKMAN_SUITS[selected_suit]["price"]
                                            if not sandbox_mode and menu_win_coins < suit_price:
                                                break
                                            if not sandbox_mode:
                                                menu_win_coins -= suit_price
                                            menu_stickman_suits.add(selected_suit)
                                        menu_stickman_suit = selected_suit
                                        if selected_suit != "classic":
                                            achievements = load_achievements()
                                            if not sandbox_mode:
                                                award_achievement(achievements, "first_costume")
                                                save_unlocks(
                                                    load_unlocks(),
                                                    menu_win_coins,
                                                    unlocked_maps,
                                                    stickman_costumes=menu_stickman_costumes,
                                                    equipped_stickman_costume=menu_equipped_costume,
                                                    developer_mode_opened=menu_developer_mode_opened,
                                                    stickman_hat_text=menu_stickman_hat_text,
                                                    stickman_hat=menu_stickman_hat,
                                                    stickman_hats=menu_stickman_hats,
                                                    stickman_legs=menu_stickman_leg,
                                                    stickman_legs_unlocked=menu_stickman_legs,
                                                    stickman_suit=menu_stickman_suit,
                                                    stickman_suits=menu_stickman_suits,
                                                    stickman_object=menu_stickman_object,
                                                    stickman_objects=menu_stickman_objects,
                                                    achievements=achievements,
                                                )
                                    elif costume_id.startswith("object_"):
                                        selected_object = costume_id[7:]
                                        if selected_object not in menu_stickman_objects:
                                            object_price = STICKMAN_OBJECTS[selected_object]["price"]
                                            if not sandbox_mode and menu_win_coins < object_price:
                                                break
                                            if not sandbox_mode:
                                                menu_win_coins -= object_price
                                            menu_stickman_objects.add(selected_object)
                                        menu_stickman_object = selected_object
                                        if selected_object != "none":
                                            achievements = load_achievements()
                                            if not sandbox_mode:
                                                award_achievement(achievements, "first_costume")
                                                save_unlocks(
                                                    load_unlocks(),
                                                    menu_win_coins,
                                                    unlocked_maps,
                                                    stickman_costumes=menu_stickman_costumes,
                                                    equipped_stickman_costume=menu_equipped_costume,
                                                    developer_mode_opened=menu_developer_mode_opened,
                                                    stickman_hat_text=menu_stickman_hat_text,
                                                    stickman_hat=menu_stickman_hat,
                                                    stickman_hats=menu_stickman_hats,
                                                    stickman_legs=menu_stickman_leg,
                                                    stickman_legs_unlocked=menu_stickman_legs,
                                                    stickman_suit=menu_stickman_suit,
                                                    stickman_suits=menu_stickman_suits,
                                                    stickman_object=menu_stickman_object,
                                                    stickman_objects=menu_stickman_objects,
                                                    achievements=achievements,
                                                )
                                    else:
                                        preview_costume = costume_id
                                        menu_equipped_costume = costume_id
                                    if not sandbox_mode:
                                        save_unlocks(
                                            load_unlocks(),
                                            menu_win_coins,
                                            unlocked_maps,
                                            stickman_costumes=menu_stickman_costumes,
                                            equipped_stickman_costume=menu_equipped_costume,
                                            developer_mode_opened=menu_developer_mode_opened,
                                            stickman_hat_text=menu_stickman_hat_text,
                                            stickman_hat=menu_stickman_hat,
                                            stickman_hats=menu_stickman_hats,
                                            stickman_legs=menu_stickman_leg,
                                            stickman_legs_unlocked=menu_stickman_legs,
                                            stickman_suit=menu_stickman_suit,
                                            stickman_suits=menu_stickman_suits,
                                            stickman_object=menu_stickman_object,
                                            stickman_objects=menu_stickman_objects,
                                        )
                                    break
                    elif BACKSTORY_RECT.collidepoint(event.pos):
                        show_backstory = True
                    elif ACHIEVEMENTS_BUTTON_RECT.collidepoint(event.pos):
                        if achievements_process is None or achievements_process.poll() is not None:
                            achievements_process = open_achievements_window()
                    elif menu_developer_mode_opened and HOME_COSTUMES_RECT.collidepoint(event.pos):
                        show_costume_window = True
                    elif SPIRAL_BUY_RECT.collidepoint(event.pos) and "Spiral" not in unlocked_maps:
                        if menu_win_coins >= MAP_UNLOCK_COST:
                            menu_win_coins -= MAP_UNLOCK_COST
                            unlocked_maps.add("Spiral")
                            selected_map = "Spiral"
                            if not sandbox_mode:
                                achievements = load_achievements()
                                award_achievement(achievements, "spiral_map")
                                save_unlocks(load_unlocks(), menu_win_coins, unlocked_maps, achievements=achievements)
                elif not game.game_over:
                    if game.developer_mode and game.handle_developer_spawn_click(event.pos):
                        pass
                    elif game.begin_enemy_drag(event.pos):
                        pass
                    elif game.wave_index + 1 < len(WAVES) and game.wave_button_rect.collidepoint(event.pos):
                        game.start_next_wave()
                    elif not game.upgrade_tower(event.pos):
                        game.place_tower(event.pos)
            elif event.type == pygame.MOUSEMOTION and not in_menu:
                game.drag_enemy(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and not in_menu:
                game.end_enemy_drag()

        if in_menu:
            if show_backstory:
                draw_backstory(SCREEN)
            else:
                menu_costume_buttons = draw_map_selection(
                    SCREEN,
                    selected_map,
                    sandbox_mode,
                    unlocked_maps,
                    menu_win_coins,
                    menu_stickman_costumes,
                    menu_equipped_costume,
                    menu_developer_mode_opened,
                    show_costume_window,
                    preview_costume,
                    menu_stickman_hat_text,
                    menu_hat_text_editing,
                    menu_hat_text_input,
                    menu_stickman_hat,
                    menu_stickman_hats,
                    menu_stickman_leg,
                    menu_stickman_legs,
                    menu_stickman_suit,
                    menu_stickman_suits,
                    menu_stickman_object,
                    menu_stickman_objects,
                    load_achievements(),
                )
        else:
            game.update(dt)
            game.draw(SCREEN)

        draw_achievement_popups(SCREEN)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    if "--achievements" in sys.argv:
        run_achievements_window()
    else:
        main()
