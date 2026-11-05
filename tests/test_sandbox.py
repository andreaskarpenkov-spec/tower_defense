import json
import os
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

import pygame

import main
import wiki_sync
from main import Enemy, Game, MAPS, MAP_UNLOCK_COST, TOWER_UNLOCK_WAVES, Tower, WAVES, load_unlocked_maps, save_unlocks


class SandboxModeTest(unittest.TestCase):
    def test_seasonal_map_availability_uses_inclusive_annual_date_ranges(self):
        seasonal_map = {
            "path": [(0, 100), (840, 100)],
            "holiday": "Winter holiday",
            "start": (12, 24),
            "end": (1, 2),
            "background": (15, 25, 45),
        }
        with patch.dict(main.SEASONAL_MAPS, {"Winter map": seasonal_map}):
            self.assertTrue(main.is_seasonal_map_available("Winter map", date(2026, 12, 24)))
            self.assertTrue(main.is_seasonal_map_available("Winter map", date(2027, 1, 2)))
            self.assertFalse(main.is_seasonal_map_available("Winter map", date(2027, 1, 3)))
            self.assertFalse(main.is_seasonal_map_available("Winter map", date(2027, 6, 1)))
            self.assertTrue(main.is_map_available_for_play("Winter map", date(2026, 12, 25)))
            self.assertFalse(main.is_map_available_for_play("Winter map", date(2026, 12, 23)))
            self.assertEqual(main.get_map_path("Winter map"), seasonal_map["path"])

    def test_present_maze_is_only_available_christmas_eve_through_boxing_day(self):
        map_name = "present maze"
        self.assertTrue(main.is_seasonal_map_available(map_name, date(2026, 12, 24)))
        self.assertTrue(main.is_seasonal_map_available(map_name, date(2026, 12, 25)))
        self.assertTrue(main.is_seasonal_map_available(map_name, date(2026, 12, 26)))
        self.assertFalse(main.is_seasonal_map_available(map_name, date(2026, 12, 23)))
        self.assertFalse(main.is_seasonal_map_available(map_name, date(2026, 12, 27)))
        self.assertFalse(main.is_seasonal_map_available(map_name, date(2027, 1, 1)))

    def test_gobble_gobble_is_available_during_us_thanksgiving_week(self):
        map_name = "Gobble Gobble"
        thanksgiving_dates = {
            2025: date(2025, 11, 27),
            2026: date(2026, 11, 26),
            2027: date(2027, 11, 25),
        }
        for year, thanksgiving in thanksgiving_dates.items():
            with self.subTest(year=year):
                self.assertEqual(main.thanksgiving_date(year), thanksgiving)
                self.assertTrue(main.is_seasonal_map_available(map_name, thanksgiving - main.timedelta(days=3)))
                self.assertTrue(main.is_seasonal_map_available(map_name, thanksgiving + main.timedelta(days=3)))
                self.assertFalse(main.is_seasonal_map_available(map_name, thanksgiving - main.timedelta(days=4)))
                self.assertFalse(main.is_seasonal_map_available(map_name, thanksgiving + main.timedelta(days=4)))

    def test_paint_dash_is_available_on_holi_day(self):
        map_name = "paint dash"
        holi_dates = {
            2025: date(2025, 3, 14),
            2026: date(2026, 3, 4),
            2027: date(2027, 3, 22),
            2028: date(2028, 3, 11),
        }
        for year, holi in holi_dates.items():
            with self.subTest(year=year):
                self.assertEqual(main.holi_date(year), holi)
                self.assertTrue(main.is_seasonal_map_available(map_name, holi))
                self.assertFalse(main.is_seasonal_map_available(map_name, holi - main.timedelta(days=1)))
                self.assertFalse(main.is_seasonal_map_available(map_name, holi + main.timedelta(days=1)))

    def test_paint_dash_shoots_closest_living_enemy_every_twenty_seconds(self):
        map_name = "paint dash"
        game = Game(main.get_map_path(map_name), map_name=map_name)
        shooter = game.paint_dash
        farther_enemy = Enemy(MAPS["Classic"], speed=0, hp=100, reward=1)
        closest_enemy = Enemy(MAPS["Classic"], speed=0, hp=100, reward=1)
        dead_enemy = Enemy(MAPS["Classic"], speed=0, hp=100, reward=1)
        farther_enemy.x, farther_enemy.y = 700, 500
        closest_enemy.x, closest_enemy.y = 150, 100
        dead_enemy.x, dead_enemy.y = 110, 110
        dead_enemy.hp = 0
        game.enemies = [farther_enemy, closest_enemy, dead_enemy]
        game.enemies_paused = True

        with patch.object(main.random, "uniform", side_effect=[100, 100]):
            game.update(19.9)
            self.assertFalse(game.paint_dash.visible_timer)
            game.update(0.11)

        self.assertEqual(shooter.visible_timer, 2.0)
        self.assertEqual(len(game.projectiles), 1)
        self.assertIsInstance(game.projectiles[0], main.PaintballProjectile)
        self.assertIs(game.projectiles[0].target, closest_enemy)
        self.assertEqual(game.projectiles[0].damage, 30)

    def test_paint_dash_uses_classic_path_and_only_appears_on_its_map(self):
        paint_dash = Game(main.get_map_path("paint dash"), map_name="paint dash")
        classic = Game(MAPS["Classic"])
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        self.assertEqual(paint_dash.path_points, MAPS["Classic"])
        self.assertIsNotNone(paint_dash.paint_dash)
        self.assertIsNone(classic.paint_dash)
        paint_dash.paint_dash.visible_timer = 1.0
        paint_dash.draw(surface)

        self.assertEqual(paint_dash.background_color, (72, 48, 62))

    def test_paint_dash_draws_holi_decorations_away_from_path(self):
        paint_dash = Game(main.get_map_path("paint dash"), map_name="paint dash")
        classic = Game(MAPS["Classic"])
        paint_surface = pygame.Surface((main.WIDTH, main.HEIGHT))
        classic_surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        paint_dash.draw(paint_surface)
        classic.draw(classic_surface)

        self.assertNotEqual(paint_surface.get_at((75, 82))[:3], paint_dash.background_color)
        self.assertEqual(classic_surface.get_at((75, 82))[:3], classic.background_color)
        self.assertEqual(paint_surface.get_at((100, 200))[:3], (180, 140, 80))

    def test_birthday_rush_is_available_only_on_january_sixteenth(self):
        map_name = "birthday rush"

        self.assertTrue(main.is_seasonal_map_available(map_name, date(2026, 1, 16)))
        self.assertFalse(main.is_seasonal_map_available(map_name, date(2026, 1, 15)))
        self.assertFalse(main.is_seasonal_map_available(map_name, date(2026, 1, 17)))
        self.assertFalse(main.is_seasonal_map_available(map_name, date(2026, 7, 16)))

    def test_birthday_rush_spawns_cakes_falling_onto_the_spiral_path(self):
        game = Game(main.get_map_path("birthday rush"), map_name="birthday rush")
        self.assertEqual(game.path_points, MAPS["Spiral"])
        self.assertGreaterEqual(game.cake_spawn_timer, 7.0)
        self.assertLessEqual(game.cake_spawn_timer, 15.0)

        game.cake_spawn_timer = 0.1
        game.enemies_paused = True
        with patch.object(main.random, "randrange", return_value=1):
            with patch.object(main.random, "uniform", side_effect=[0.5, 120, 10]):
                game.update(0.1)

        cake = game.enemies[0]
        self.assertEqual(cake.type, "cake")
        self.assertTrue(cake.falling)
        self.assertEqual(cake.segment, 1)
        self.assertLess(cake.y, 0)
        self.assertGreater(cake.fall_target[1], 0)
        cake.update(2.0, [])
        self.assertFalse(cake.falling)
        self.assertEqual((cake.x, cake.y), cake.fall_target)

        surface = pygame.Surface((main.WIDTH, main.HEIGHT))
        cake.draw(surface)
        self.assertIn("cake", main.BESTIARY)
        self.assertEqual(game.cake_spawn_timer, 10)

    def test_birthday_rush_draws_no_spiral_plants(self):
        birthday_rush = Game(main.get_map_path("birthday rush"), map_name="birthday rush")
        spiral = Game(MAPS["Spiral"], map_name="Spiral")
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        with patch.object(birthday_rush, "draw_grass_texture", wraps=birthday_rush.draw_grass_texture) as draw_plants:
            birthday_rush.draw(surface)
        draw_plants.assert_not_called()

        with patch.object(spiral, "draw_grass_texture", wraps=spiral.draw_grass_texture) as draw_plants:
            spiral.draw(surface)
        draw_plants.assert_called()

    def test_birthday_rush_uses_its_bright_birthday_background(self):
        birthday_rush = Game(main.get_map_path("birthday rush"), map_name="birthday rush")
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        birthday_rush.draw(surface)

        self.assertEqual(birthday_rush.background_color, (255, 225, 175))
        self.assertEqual(surface.get_at((839, 639))[:3], birthday_rush.background_color)

    def test_thrillero_is_available_only_on_halloween(self):
        map_name = "ThRiLlErO"

        self.assertTrue(main.is_seasonal_map_available(map_name, date(2026, 10, 31)))
        self.assertFalse(main.is_seasonal_map_available(map_name, date(2026, 10, 30)))
        self.assertFalse(main.is_seasonal_map_available(map_name, date(2026, 11, 1)))

    def test_muddy_mud_is_available_only_on_earth_day(self):
        map_name = "muddy mud"

        self.assertTrue(main.is_seasonal_map_available(map_name, date(2026, 4, 22)))
        self.assertFalse(main.is_seasonal_map_available(map_name, date(2026, 4, 21)))
        self.assertFalse(main.is_seasonal_map_available(map_name, date(2026, 4, 23)))

    def test_homework_is_available_during_the_monday_to_sunday_week_containing_october_19(self):
        map_name = "homework"
        expected_ranges = {
            2025: (date(2025, 10, 13), date(2025, 10, 19)),
            2026: (date(2026, 10, 19), date(2026, 10, 25)),
            2027: (date(2027, 10, 18), date(2027, 10, 24)),
        }

        for year, (week_start, week_end) in expected_ranges.items():
            with self.subTest(year=year):
                self.assertTrue(main.is_seasonal_map_available(map_name, week_start))
                self.assertTrue(main.is_seasonal_map_available(map_name, week_end))
                self.assertFalse(main.is_seasonal_map_available(map_name, week_start - main.timedelta(days=1)))
                self.assertFalse(main.is_seasonal_map_available(map_name, week_end + main.timedelta(days=1)))

    def test_homework_reuses_classic_path_and_freezes_three_enemies_on_a_ten_second_cycle(self):
        game = Game(main.get_map_path("homework"), map_name="homework", sandbox=True)
        enemies = [
            Enemy(MAPS["Classic"], speed=0, hp=100, reward=1)
            for _ in range(4)
        ]
        for index, enemy in enumerate(enemies):
            enemy.x = 100 + index * 30
            enemy.y = 100
        game.enemies = enemies
        game.wave_ready = True
        game.homework_timer = 0.1

        with patch.object(main.random, "sample", return_value=enemies[:3]) as sample:
            game.update(0.1)

        self.assertEqual(game.path_points, MAPS["Classic"])
        self.assertEqual(game.background_color, (48, 57, 78))
        self.assertEqual(sample.call_count, 1)
        self.assertEqual([enemy.homework_frozen_timer for enemy in enemies], [2.9, 2.9, 2.9, 0.0])
        self.assertAlmostEqual(game.homework_timer, 10.0)

    def test_homework_freeze_stops_enemy_and_medic_until_three_seconds_expire(self):
        enemy = Enemy(MAPS["Classic"], speed=100, hp=100, reward=1)
        enemy.x, enemy.y = 100, 100
        enemy.homework_frozen_timer = 3.0
        enemy.update(2.5, [])
        self.assertEqual((enemy.x, enemy.y), (100, 100))
        self.assertAlmostEqual(enemy.homework_frozen_timer, 0.5)

        enemy.update(0.5, [])
        self.assertEqual((enemy.x, enemy.y), (100, 100))
        self.assertEqual(enemy.homework_frozen_timer, 0)
        enemy.update(0.1, [])
        self.assertNotEqual((enemy.x, enemy.y), (100, 100))

        medic = Enemy(MAPS["Classic"], speed=0, hp=100, reward=1, enemy_type="medic")
        ally = Enemy(MAPS["Classic"], speed=0, hp=50, reward=1)
        medic.x = ally.x = 100
        medic.y = ally.y = 100
        medic.homework_frozen_timer = 1.0
        medic.heal_touching_allies([medic, ally], 1.0)
        self.assertEqual(ally.hp, 50)

        game = Game(main.get_map_path("homework"), map_name="homework", sandbox=True)
        frozen_enemy = Enemy(MAPS["Classic"], speed=0, hp=100, reward=1)
        moving_enemy = Enemy(MAPS["Classic"], speed=0, hp=100, reward=1)
        frozen_enemy.x, frozen_enemy.y = 100, 100
        moving_enemy.x, moving_enemy.y = 110, 100
        frozen_enemy.homework_frozen_timer = 1.0
        game.enemies = [frozen_enemy, moving_enemy]
        game.separate_enemies()
        self.assertEqual((frozen_enemy.x, frozen_enemy.y), (100, 100))
        self.assertNotEqual((moving_enemy.x, moving_enemy.y), (110, 100))

    def test_homework_freeze_draws_an_animated_book_and_pencil(self):
        enemy = Enemy(MAPS["Classic"], speed=0, hp=100, reward=1)
        enemy.homework_frozen_timer = 3.0
        first_frame = pygame.Surface((main.WIDTH, main.HEIGHT))
        second_frame = pygame.Surface((main.WIDTH, main.HEIGHT))

        enemy.draw(first_frame)
        enemy.homework_animation_time = 0.1
        enemy.draw(second_frame)

        self.assertNotEqual(
            pygame.image.tobytes(first_frame, "RGB"),
            pygame.image.tobytes(second_frame, "RGB"),
        )

    def test_muddy_mud_earth_enemies_emerge_off_path_and_join_classic_route(self):
        game = Game(main.get_map_path("muddy mud"), map_name="muddy mud")
        self.assertEqual(game.path_points, MAPS["Classic"])
        self.assertGreaterEqual(game.earth_spawn_timer, 8.0)
        self.assertLessEqual(game.earth_spawn_timer, 14.0)
        game.earth_spawn_timer = 0.1
        game.enemies_paused = True

        with patch.object(main.random, "uniform", return_value=100):
            game.update(0.1)

        earth = game.enemies[0]
        self.assertEqual(earth.type, "earth")
        self.assertEqual((earth.x, earth.y), (100, 100))
        self.assertEqual(earth.earth_join_target, (100.0, 200.0))
        self.assertGreater(earth.earth_rumble_timer, 0)
        self.assertEqual(earth.earth_emerge_timer, 0)
        self.assertEqual(game.earth_spawn_timer, 100)

        earth.base_speed = 200
        earth.update(0.5, [])
        self.assertAlmostEqual(earth.earth_rumble_timer, 0.3)
        self.assertEqual(earth.earth_emerge_timer, 0)
        earth.update(0.4, [])
        self.assertEqual(earth.earth_rumble_timer, 0)
        self.assertEqual(earth.earth_emerge_timer, 0.45)
        earth.update(0.5, [])
        earth.update(1.0, [])
        self.assertEqual((earth.x, earth.y), (100.0, 200.0))
        self.assertIsNone(earth.earth_join_target)
        earth.update(0.1, [])
        self.assertGreater(earth.x, 100)

        surface = pygame.Surface((main.WIDTH, main.HEIGHT))
        earth.draw(surface)
        self.assertIn("earth", main.BESTIARY)

    def test_earth_enemy_rumble_is_visibly_animated_before_emerging(self):
        earth = Enemy(MAPS["Classic"], speed=5.0, hp=180, reward=18, enemy_type="earth")
        earth.x, earth.y = 200, 200
        earth.earth_rumble_timer = 0.8
        earth.earth_rumble_time = 0.05
        first_frame = pygame.Surface((main.WIDTH, main.HEIGHT))
        second_frame = pygame.Surface((main.WIDTH, main.HEIGHT))

        earth.draw(first_frame)
        earth.earth_rumble_time = 0.12
        earth.draw(second_frame)

        self.assertTrue(earth.earth_rumble_timer > 0)
        self.assertEqual(earth.earth_emerge_timer, 0)
        self.assertNotEqual(
            pygame.image.tobytes(first_frame, "RGB"),
            pygame.image.tobytes(second_frame, "RGB"),
        )

    def test_non_earth_day_maps_do_not_spawn_earth_enemies(self):
        classic = Game(MAPS["Classic"], map_name="Classic")
        self.assertEqual(classic.earth_spawn_timer, 0)
        self.assertFalse(main.SEASONAL_MAPS["ThRiLlErO"].get("earth_spawn_interval"))

    def test_thrillero_reuses_classic_path_and_has_pumpkin_spotlights(self):
        game = Game(main.get_map_path("ThRiLlErO"), map_name="ThRiLlErO")
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        self.assertEqual(game.path_points, MAPS["Classic"])
        self.assertIsNotNone(game.pumpkin_spotlights)
        game.update(1.0)
        self.assertEqual(game.pumpkin_spotlights.time, 1.0)
        game.draw(surface)

        self.assertEqual(surface.get_at((150, 300))[:3], game.background_color)
        self.assertEqual(surface.get_at((300, 300))[:3], (5, 4, 12))

    def test_pumpkin_spotlight_reveals_beams_and_draws_pumpkins(self):
        spotlights = main.PumpkinSpotlights()
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))
        surface.fill((200, 200, 200))

        spotlights.draw(surface)

        self.assertEqual(surface.get_at((420, 300))[:3], (5, 4, 12))
        self.assertEqual(surface.get_at((134, 300))[:3], (200, 200, 200))
        self.assertEqual(surface.get_at((220, 300))[:3], (5, 4, 12))
        self.assertNotEqual(surface.get_at((134, 45))[:3], (200, 200, 200))

    def test_gobble_gobble_reuses_classic_path_and_has_a_turkey(self):
        map_name = "Gobble Gobble"
        game = Game(main.get_map_path(map_name), map_name=map_name)
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        self.assertEqual(game.path_points, MAPS["Classic"])
        self.assertIsNotNone(game.turkey)
        game.draw(surface)
        self.assertEqual(surface.get_at((420, 330))[:3], (125, 70, 42))

        game.spawn_enemy()
        self.assertEqual(game.enemies[0].type, "ground")

    def test_turkey_eats_touching_towers_and_enemies(self):
        turkey = main.Turkey()
        turkey.x, turkey.y = 200, 200
        tower = Tower(200, 200, "basic")
        enemy = Enemy([(100, 100), (300, 100)], speed=0, hp=100, reward=1)
        enemy.x, enemy.y = 200, 200
        towers = [tower]
        enemies = [enemy]
        turkey.target_timer = 100
        turkey.target = tower

        turkey.update(0.1, towers, enemies)
        self.assertEqual(towers, [])
        self.assertEqual(enemies, [enemy])
        self.assertIsNone(turkey.target)
        self.assertEqual(turkey.eating_timer, turkey.eating_duration)

        turkey.update(0.4, towers, enemies)
        self.assertAlmostEqual(turkey.eating_timer, turkey.eating_duration - 0.4)
        turkey.eat_cooldown = 0
        turkey.target_timer = 100
        turkey.target = enemy
        turkey.eating_timer = 0
        turkey.update(0.1, towers, enemies)
        self.assertLessEqual(enemy.hp, 0)
        self.assertEqual(turkey.eating_timer, turkey.eating_duration)

    def test_turkey_draws_a_different_pose_during_eating_animation(self):
        turkey = main.Turkey()
        turkey.x, turkey.y = 200, 200
        idle_surface = pygame.Surface((main.WIDTH, main.HEIGHT))
        eating_surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        turkey.draw(idle_surface)
        turkey.eating_timer = turkey.eating_duration * 0.75
        turkey.draw(eating_surface)

        self.assertNotEqual(
            pygame.image.tobytes(idle_surface, "RGB"),
            pygame.image.tobytes(eating_surface, "RGB"),
        )

    def test_calendar_month_navigation_wraps_year_boundaries(self):
        self.assertEqual(main.shift_calendar_month(date(2026, 12, 1), 1), date(2027, 1, 1))
        self.assertEqual(main.shift_calendar_month(date(2027, 1, 1), -1), date(2026, 12, 1))
        self.assertEqual(main.shift_calendar_month(date(2026, 6, 1), 12), date(2027, 6, 1))

    def test_seasonal_date_panel_draws_calendar_days_and_month_controls(self):
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        buttons = main.draw_seasonal_date_panel(
            surface, date(2028, 2, 25), date(2028, 2, 1)
        )

        self.assertEqual(set(buttons), {"previous_month", "next_month", "close", "days"})
        self.assertEqual(len(buttons["days"]), 29)
        self.assertTrue(buttons["days"][25].collidepoint(buttons["days"][25].center))
        self.assertTrue(buttons["previous_month"].collidepoint(buttons["previous_month"].center))
        self.assertTrue(buttons["next_month"].collidepoint(buttons["next_month"].center))

    def test_seasonal_maps_menu_shows_present_maze_when_closed(self):
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        buttons = main.draw_seasonal_maps_menu(surface, date(2026, 12, 25))

        self.assertEqual(
            set(buttons),
            {
                "present maze", "Gobble Gobble", "paint dash",
                "birthday rush", "ThRiLlErO", "muddy mud", "homework", "select_date",
            },
        )
        self.assertIn("select_date", buttons)
        self.assertEqual(buttons["select_date"], main.SEASONAL_MAPS_DATE_RECT)
        self.assertEqual(main.SEASONAL_MAPS["present maze"]["holiday"], "Christmas")
        self.assertEqual(main.SEASONAL_MAPS["present maze"]["start"], (12, 24))
        self.assertEqual(main.SEASONAL_MAPS["present maze"]["end"], (12, 26))
        self.assertEqual(main.SEASONAL_MAPS["Gobble Gobble"]["holiday"], "Thanksgiving")
        self.assertEqual(main.SEASONAL_MAPS["paint dash"]["holiday"], "Holi")
        self.assertEqual(main.SEASONAL_MAPS["birthday rush"]["holiday"], "Birthday")
        self.assertEqual(main.SEASONAL_MAPS["ThRiLlErO"]["holiday"], "Halloween")
        self.assertEqual(main.SEASONAL_MAPS["muddy mud"]["holiday"], "Earth Day")
        self.assertEqual(main.SEASONAL_MAPS["homework"]["holiday"], "Back to School")

    def test_present_maze_reuses_spiral_path_and_draws_side_presents(self):
        map_name = "present maze"
        game = Game(main.get_map_path(map_name), map_name=map_name)
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        self.assertEqual(game.path_points, MAPS["Spiral"])
        self.assertNotEqual(game.background_color, main.MAP_BACKGROUNDS["Spiral"])
        game.draw(surface)

        self.assertEqual(surface.get_at((166, 162))[:3], (205, 55, 60))

    def test_present_enemies_sometimes_emerge_from_a_present_box(self):
        map_name = "present maze"
        game = Game(main.get_map_path(map_name), map_name=map_name)
        game.wave_index = 0
        game.spawned = 0
        box_x, box_y = main.SEASONAL_MAPS[map_name]["present_boxes"][0]

        with patch.object(main.random, "random", return_value=0.0):
            with patch.object(main.random, "choice", return_value=(box_x, box_y)):
                game.spawn_enemy()

        present = game.enemies[0]
        self.assertEqual(present.type, "present")
        self.assertEqual(present.segment, 0)
        self.assertAlmostEqual(present.x, box_x)
        self.assertEqual(present.y, 120)

    def test_save_file_is_stored_with_game(self):
        self.assertTrue(os.path.isabs(main.SAVE_FILE))
        self.assertEqual(
            os.path.dirname(main.SAVE_FILE),
            os.path.dirname(os.path.abspath(main.__file__)),
        )

    def test_gunner_unlocks_after_wave_six(self):
        self.assertEqual(TOWER_UNLOCK_WAVES["gunner"], 6)

        game = Game(MAPS["Classic"])
        game.highest_cleared_wave = 6
        game.wave_six_cleared = True
        game._apply_unlocks_from_progress()

        self.assertTrue(game.is_tower_unlocked("gunner"))

    def test_invalid_saved_wave_does_not_unlock_gunner(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic", "gunner"], "highest_cleared_wave": 99}, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                game = Game(MAPS["Classic"])
                self.assertFalse(game.is_tower_unlocked("gunner"))
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_gunner_moves_along_path_and_shoots(self):
        path = MAPS["Classic"]
        gunner = Tower(40, 200, "gunner", path)
        enemy = Enemy(path, speed=0, hp=100, reward=1)

        shot = gunner.update(0.7, [enemy])

        self.assertGreater(gunner.x, 40)
        self.assertIsNotNone(shot)

    def test_gunner_follows_path_forward_from_a_corner(self):
        path = MAPS["Classic"]
        gunner = Tower(280, 200, "gunner", path)

        gunner.update(1.0, [])

        self.assertGreater(gunner.y, 200)

    def test_shooter_ignores_unupgraded_nova_tower(self):
        path = [(40, 100), (300, 100)]
        shooter = Enemy(path, speed=0, hp=100, reward=1, enemy_type="shooter")
        nova = Tower(80, 100, "nova")
        basic = Tower(180, 100, "basic")

        shooter.update(1.0, [nova, basic])

        self.assertFalse(nova.shooter_immunity)
        self.assertEqual(len(shooter.projectiles), 1)
        self.assertIs(shooter.projectiles[0].target, basic)

        shooter.projectiles.clear()
        shooter.time_since_shot = 0.0
        shooter.update(1.0, [nova])
        self.assertEqual(shooter.projectiles, [])

    def test_walker_crossing_freeze_tower_unlocks_and_saves_cactus(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic", "freeze"], "highest_cleared_wave": 4}, save_file)
            save_path = save_file.name

        original_save_file = main.SAVE_FILE
        main.SAVE_FILE = save_path
        try:
            path = [(20, 100), (200, 100)]
            game = Game(path)
            game.towers.append(Tower(70, 100, "freeze"))
            game.walkers.append(main.Walker(100, 100, path))

            game.update(0.5)

            self.assertTrue(game.is_tower_unlocked("cactus"))
            self.assertIn("cactus", main.load_progress()[0])
        finally:
            main.SAVE_FILE = original_save_file
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_cactus_damages_touching_enemies_without_moving(self):
        path = [(100, 100), (200, 100)]
        cactus = Tower(100, 100, "cactus")
        enemy = Enemy(path, speed=0, hp=100, reward=1)

        cactus.update(0.6, [enemy])

        self.assertEqual((cactus.x, cactus.y), (100, 100))
        self.assertLess(enemy.hp, 100)

    def test_maps_have_distinct_backgrounds(self):
        classic = Game(MAPS["Classic"], map_name="Classic")
        loop = Game(MAPS["Loop"], map_name="Loop")
        spiral = Game(MAPS["Spiral"], map_name="Spiral")

        self.assertNotEqual(classic.background_color, loop.background_color)
        self.assertNotEqual(loop.background_color, spiral.background_color)
        self.assertEqual(classic.map_name, "Classic")

    def test_game_has_nine_waves(self):
        self.assertEqual(len(WAVES), 9)

    def test_phantom_tower_unlocks_after_beating_wave_seven(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic"], "highest_cleared_wave": 6}, save_file)
            save_path = save_file.name

        original_save_file = main.SAVE_FILE
        main.SAVE_FILE = save_path
        try:
            game = Game(MAPS["Classic"])
            self.assertFalse(game.is_tower_unlocked("phantom"))

            game.wave_index = 6
            game.spawned = WAVES[6]["count"]
            game.complete_wave_unlocks()

            self.assertEqual(game.highest_cleared_wave, 7)
            self.assertTrue(game.is_tower_unlocked("phantom"))
        finally:
            main.SAVE_FILE = original_save_file
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_saved_phantom_unlock_does_not_bypass_wave_seven(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic", "phantom"], "highest_cleared_wave": 6}, save_file)
            save_path = save_file.name

        original_save_file = main.SAVE_FILE
        main.SAVE_FILE = save_path
        try:
            game = Game(MAPS["Classic"])
            self.assertFalse(game.is_tower_unlocked("phantom"))
            self.assertNotIn("phantom", game.unlocked_towers)
            self.assertFalse(
                next(
                    entry for entry in main.get_tower_directory_entries(
                        game.unlocked_towers, game.highest_cleared_wave, game.win_coins
                    )
                    if entry["tower_id"] == "phantom"
                )["unlocked"]
            )

            game.selected_tower = "phantom"
            game.place_tower((100, 100))
            self.assertFalse(any(tower.type == "phantom" for tower in game.towers))
        finally:
            main.SAVE_FILE = original_save_file
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_wave_eight_has_many_flyer_enemies(self):
        game = Game(MAPS["Classic"])
        game.wave_index = 7

        for _ in range(20):
            game.spawn_enemy()

        flyer_count = sum(enemy.type == "flyer" for enemy in game.enemies)
        self.assertEqual(flyer_count, 10)
        self.assertEqual(WAVES[7]["count"], 30)

    def test_lightning_enemy_first_appears_in_wave_six_at_three_times_speed(self):
        game = Game(MAPS["Classic"])
        game.wave_index = 5
        game.spawned = 0

        game.spawn_enemy()

        self.assertEqual(len(game.enemies), 1)
        self.assertEqual(game.enemies[0].type, "lightning")
        self.assertAlmostEqual(game.enemies[0].base_speed, WAVES[5]["speed"] * 3.0)

    def test_shielder_enemy_first_appears_in_wave_six_and_blocks_projectiles(self):
        game = Game(MAPS["Classic"])
        game.wave_index = 5
        game.spawned = 5

        game.spawn_enemy()

        self.assertEqual(len(game.enemies), 1)
        self.assertEqual(game.enemies[0].type, "shielder")

        enemy = game.enemies[0]
        original_hp = enemy.hp
        enemy.x, enemy.y = 200, 200
        projectile = main.Projectile(200, 200 - 35, enemy, 12, (255, 255, 255), speed=100)
        self.assertTrue(projectile.update(0.05))
        self.assertTrue(projectile.active)
        self.assertEqual(enemy.hp, original_hp)

        shield_hit = main.Projectile(247, 200, enemy, 12, (255, 255, 255), speed=100)
        self.assertFalse(shield_hit.update(0.01))
        self.assertFalse(shield_hit.active)
        self.assertEqual(enemy.hp, original_hp)

    def test_bestiary_lists_all_enemy_types(self):
        self.assertIn("ground", main.BESTIARY)
        self.assertIn("flyer", main.BESTIARY)
        self.assertIn("shooter", main.BESTIARY)
        self.assertIn("lightning", main.BESTIARY)
        self.assertIn("medic", main.BESTIARY)
        self.assertIn("wave 6", main.BESTIARY["lightning"]["notes"].lower())

    def test_bestiary_scroll_reaches_last_enemy_entry(self):
        surface = pygame.Surface((600, 560))

        scroll_offset = main.draw_bestiary_window(surface, 1000)

        self.assertEqual(scroll_offset, main.bestiary_scroll_limit(560))
        self.assertGreater(scroll_offset, 0)

    def test_every_bestiary_enemy_has_visible_face_details(self):
        surface = pygame.Surface((600, 123 + len(main.BESTIARY) * 90))
        main.draw_bestiary_window(surface)

        for index, enemy_id in enumerate(main.BESTIARY):
            with self.subTest(enemy_id=enemy_id):
                self.assertEqual(surface.get_at((55, 123 + index * 90))[:3], (35, 25, 25))

    def test_ghost_enemy_appears_in_wave_seven_and_turns_invisible(self):
        game = Game(MAPS["Classic"])
        game.wave_index = 6
        game.spawned = 0

        game.spawn_enemy()

        self.assertEqual(len(game.enemies), 1)
        self.assertEqual(game.enemies[0].type, "ghost")
        self.assertTrue(game.enemies[0].is_visible())
        game.enemies[0].ghost_visible = False
        self.assertFalse(game.enemies[0].is_visible())

    def test_medic_enemy_first_appears_in_wave_nine(self):
        game = Game(MAPS["Classic"])
        game.wave_index = 8

        game.spawn_enemy()
        self.assertEqual(game.enemies[-1].type, "medic")

        game.spawned = 5
        game.spawn_enemy()
        self.assertEqual(game.enemies[-1].type, "medic")

    def test_medic_sprite_draws_doctor_coat_and_scrubs(self):
        medic = Enemy([(80, 80), (200, 80)], speed=0, hp=100, reward=1, enemy_type="medic")
        surface = pygame.Surface((240, 160))
        surface.fill((0, 0, 0))

        medic.draw(surface)

        self.assertEqual(surface.get_at((69, 88))[:3], (225, 235, 240))
        self.assertEqual(surface.get_at((80, 90))[:3], (105, 165, 185))

    def test_medic_heals_touching_allies_without_exceeding_max_health(self):
        path = [(100, 100), (300, 100)]
        medic = Enemy(path, speed=0, hp=100, reward=1, enemy_type="medic")
        ally = Enemy(path, speed=0, hp=100, reward=1)
        distant_ally = Enemy(path, speed=0, hp=100, reward=1)
        medic.x, medic.y = 100, 100
        ally.x, ally.y = 120, 100
        ally.hp = 50
        distant_ally.x, distant_ally.y = 200, 100
        distant_ally.hp = 50

        medic.heal_touching_allies([medic, ally, distant_ally], 1.0)
        self.assertEqual(ally.hp, 80)
        self.assertEqual(distant_ally.hp, 50)
        self.assertEqual(medic.hp, medic.max_hp)

        ally.hp = 95
        medic.heal_touching_allies([medic, ally], 1.0)
        self.assertEqual(ally.hp, ally.max_hp)

    def test_phantom_tower_targets_invisible_ghosts(self):
        path = [(100, 100), (300, 100)]
        ghost = Enemy(path, speed=0, hp=210, reward=36, enemy_type="ghost")
        ghost.ghost_visible = False
        phantom = Tower(100, 120, "phantom")
        basic = Tower(100, 120, "basic")

        self.assertIsNone(basic.update(1.0, [ghost]))

        projectile = phantom.update(1.0, [ghost])

        self.assertIsNotNone(projectile)
        self.assertIs(projectile.target, ghost)
        projectile.update(1.0)
        self.assertLess(ghost.hp, ghost.max_hp)

    def test_milk_bob_unlocks_after_beating_wave_eight(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic"], "highest_cleared_wave": 7}, save_file)
            save_path = save_file.name

        original_save_file = main.SAVE_FILE
        main.SAVE_FILE = save_path
        try:
            game = Game(MAPS["Classic"])
            self.assertFalse(game.is_tower_unlocked("milk_bob"))

            game.wave_index = 7
            game.spawned = WAVES[7]["count"]
            game.complete_wave_unlocks()

            self.assertEqual(game.highest_cleared_wave, 8)
            self.assertTrue(game.is_tower_unlocked("milk_bob"))
        finally:
            main.SAVE_FILE = original_save_file
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_milk_bob_milk_balls_deal_splash_damage(self):
        path = [(150, 100), (300, 100)]
        target = Enemy(path, speed=0, hp=200, reward=1)
        nearby = Enemy(path, speed=0, hp=200, reward=1)
        distant = Enemy(path, speed=0, hp=200, reward=1)
        nearby.x = 190
        distant.x = 240
        milk_bob = Tower(100, 100, "milk_bob")

        projectile = milk_bob.update(1.6, [target, nearby, distant])
        self.assertIsInstance(projectile, main.BombProjectile)
        self.assertEqual(projectile.explosion_color, (235, 245, 255))

        projectile.update(1.0)

        self.assertLess(target.hp, 200)
        self.assertLess(nearby.hp, 200)
        self.assertEqual(distant.hp, 200)

    def test_map_unlock_costs_20_win_coins_and_persists(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic"], "win_coins": 25}, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                unlocked_maps = load_unlocked_maps()
                self.assertNotIn("Spiral", unlocked_maps)
                _, win_coins = main.load_progress()
                self.assertGreaterEqual(win_coins, MAP_UNLOCK_COST)
                win_coins -= MAP_UNLOCK_COST
                unlocked_maps.add("Spiral")
                save_unlocks({"basic"}, win_coins, unlocked_maps)
                self.assertIn("Spiral", load_unlocked_maps())
                self.assertEqual(main.load_progress()[1], 5)
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_achievements_are_saved_and_unlocked(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic"], "win_coins": 0}, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                self.assertEqual(main.load_achievements(), set())
                game = Game(MAPS["Classic"])
                self.assertTrue(game.unlock_achievement("first_wave"))
                self.assertFalse(game.unlock_achievement("first_wave"))
                self.assertTrue(game.unlock_achievement("developer_mode"))
                self.assertFalse(game.unlock_achievement("developer_mode"))
                self.assertIn("developer_mode", main.load_achievements())
                with open(save_path, "r", encoding="utf-8") as save_handle:
                    saved = json.load(save_handle)
                self.assertIn("developer_mode", saved["achievements"])
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_first_successful_tower_placement_unlocks_achievement(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic"], "win_coins": 0}, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                self.assertEqual(main.ACHIEVEMENTS["the_beginning"]["name"], "The Beginning")
                game = Game(MAPS["Classic"])
                game.place_tower((280, 200))
                self.assertNotIn("the_beginning", main.load_achievements())

                game.place_tower((100, 100))
                self.assertIn("the_beginning", main.load_achievements())
                self.assertEqual(len(game.towers), 1)
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_sandbox_tower_placement_does_not_unlock_campaign_achievement(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic"], "win_coins": 0}, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                game = Game(MAPS["Classic"], sandbox=True)
                game.place_tower((100, 100))
                self.assertNotIn("the_beginning", main.load_achievements())
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_saved_progress_reconciles_achievements(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({
                "unlocked_towers": ["basic"],
                "win_coins": 0,
                "highest_cleared_wave": 6,
                "unlocked_maps": ["Classic", "Spiral"],
                "developer_mode_opened": True,
                "stickman_suits": ["classic", "fish"],
                "achievements": ["the_beginning", "bullet_time", "matrix_dodge", "exit_construct"],
            }, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                main.ACHIEVEMENT_POPUPS.clear()
                earned = main.check_achievements()
                self.assertEqual(earned, set(main.ACHIEVEMENTS) - {"slaver", "poor_choice"})
                self.assertEqual(main.load_achievements(), earned)
                queued_ids = {popup["achievement_id"] for popup in main.ACHIEVEMENT_POPUPS}
                self.assertIn("first_wave", queued_ids)
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_achievements_are_rechecked_every_ten_seconds(self):
        with patch("main.check_achievements") as check:
            elapsed = main.update_achievement_check_timer(0.0, 9.9)
            check.assert_not_called()

            elapsed = main.update_achievement_check_timer(elapsed, 0.1)
            check.assert_called_once_with(None)
            self.assertAlmostEqual(elapsed, 0.0)

    def test_campaign_end_rechecks_achievements_on_win_and_loss(self):
        for outcome in ("loss", "win"):
            with self.subTest(outcome=outcome):
                with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
                    json.dump({"unlocked_towers": ["basic"], "win_coins": 0}, save_file)
                    save_path = save_file.name

                try:
                    original_save_file = main.SAVE_FILE
                    main.SAVE_FILE = save_path
                    try:
                        game = Game(MAPS["Classic"])
                        game.highest_cleared_wave = 6
                        if outcome == "loss":
                            game.lives = 0
                        else:
                            game.wave_index = len(WAVES)
                        game.update(0)
                        self.assertTrue(game.game_over)
                        self.assertIn("wave_six", main.load_achievements())
                    finally:
                        main.SAVE_FILE = original_save_file
                finally:
                    if os.path.exists(save_path):
                        os.remove(save_path)

    def test_win_and_loss_screens_show_home_button(self):
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))
        game = Game(MAPS["Classic"])
        game.game_over = True

        for victory in (False, True):
            with self.subTest(victory=victory):
                game.victory = victory
                game.draw(surface)
                button_color = surface.get_at((main.HOME_BUTTON_RECT.left + 2, main.HOME_BUTTON_RECT.top + 2))[:3]
                self.assertNotEqual(button_color, game.background_color)
                self.assertTrue(surface.get_rect().contains(main.HOME_BUTTON_RECT))

    def test_slaver_requires_campaign_win_with_only_one_placed_tower_type(self):
        for tower_types, expected_unlock in ((["basic"], True), (["basic", "rapid"], False)):
            with self.subTest(tower_types=tower_types):
                with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
                    json.dump({"unlocked_towers": ["basic", "rapid"], "win_coins": 0}, save_file)
                    save_path = save_file.name

                original_save_file = main.SAVE_FILE
                main.SAVE_FILE = save_path
                try:
                    game = Game(MAPS["Classic"])
                    game.money = 1000
                    for tower_index, tower_type in enumerate(tower_types):
                        game.selected_tower = tower_type
                        game.place_tower((100 + tower_index * 100, 100))

                    game.wave_index = len(WAVES)
                    game.update(0)

                    self.assertEqual("slaver" in main.load_achievements(), expected_unlock)
                finally:
                    main.SAVE_FILE = original_save_file
                    if os.path.exists(save_path):
                        os.remove(save_path)

    def test_poor_choice_requires_winning_without_any_tower_upgrades(self):
        for upgrade_method, expected_unlock in ((None, True), ("single", False), ("all", False)):
            with self.subTest(upgrade_method=upgrade_method):
                with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
                    json.dump({"unlocked_towers": ["basic"], "win_coins": 0}, save_file)
                    save_path = save_file.name

                original_save_file = main.SAVE_FILE
                main.SAVE_FILE = save_path
                try:
                    game = Game(MAPS["Classic"])
                    game.money = 1000
                    game.place_tower((120, 120))
                    if upgrade_method == "single":
                        self.assertTrue(game.upgrade_tower((120, 120)))
                    elif upgrade_method == "all":
                        game.upgrade_all_towers()

                    game.wave_index = len(WAVES)
                    game.update(0)

                    self.assertEqual("poor_choice" in main.load_achievements(), expected_unlock)
                finally:
                    main.SAVE_FILE = original_save_file
                    if os.path.exists(save_path):
                        os.remove(save_path)

    def test_matrix_themed_achievements_track_campaign_milestones(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic"], "win_coins": 0}, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                game = Game(MAPS["Classic"])
                game.wave_index = 3
                game.spawned = WAVES[3]["count"]
                game.complete_wave_unlocks()
                self.assertIn("code_rain", main.load_achievements())
                self.assertIn("bullet_time", main.load_achievements())

                game.victory = True
                game.game_over = True
                main.check_achievements(game)
                self.assertIn("exit_construct", main.load_achievements())
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_matrix_dodge_is_awarded_when_flyer_evades_tower(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic"], "win_coins": 0}, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            main.ACHIEVEMENT_POPUPS.clear()
            try:
                game = Game(MAPS["Classic"])
                game.wave_ready = True
                game.enemies.append(Enemy(MAPS["Classic"], speed=6, hp=100, reward=1, enemy_type="flyer"))
                game.towers.append(Tower(40, 200, "basic"))

                game.update(0.01)

                self.assertIn("matrix_dodge", main.load_achievements())
                self.assertTrue(any(popup["achievement_id"] == "matrix_dodge" for popup in main.ACHIEVEMENT_POPUPS))

                with open(save_path, "w", encoding="utf-8") as save_handle:
                    json.dump({"unlocked_towers": ["basic"], "win_coins": 0}, save_handle)
                sandbox_game = Game(MAPS["Classic"], sandbox=True)
                sandbox_game.wave_ready = True
                sandbox_game.enemies.append(Enemy(MAPS["Classic"], speed=6, hp=100, reward=1, enemy_type="flyer"))
                sandbox_game.towers.append(Tower(40, 200, "basic"))
                sandbox_game.update(0.01)
                self.assertNotIn("matrix_dodge", sandbox_game.achievements)
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_achievements_window_renders_and_launches_separately(self):
        locked_surface = pygame.Surface((600, 560))
        unlocked_surface = pygame.Surface((600, 560))
        main.draw_achievements_window(locked_surface, set())
        main.draw_achievements_window(unlocked_surface, set(main.ACHIEVEMENTS))
        self.assertEqual(unlocked_surface.get_size(), (600, 560))
        locked_icon_colors = {tuple(locked_surface.get_at((x, y))) for x in range(38, 74) for y in range(98, 126)}
        unlocked_icon_colors = {tuple(unlocked_surface.get_at((x, y))) for x in range(38, 74) for y in range(98, 126)}
        beginning_icon_colors = {tuple(unlocked_surface.get_at((x, y))) for x in range(38, 74) for y in range(143, 171)}
        code_rain_icon_colors = {tuple(unlocked_surface.get_at((x, y))) for x in range(38, 74) for y in range(368, 396)}
        bullet_time_icon_colors = {tuple(unlocked_surface.get_at((x, y))) for x in range(38, 74) for y in range(413, 441)}
        matrix_dodge_icon_colors = {tuple(unlocked_surface.get_at((x, y))) for x in range(38, 74) for y in range(458, 486)}
        exit_construct_icon_colors = {tuple(unlocked_surface.get_at((x, y))) for x in range(38, 74) for y in range(503, 531)}
        self.assertEqual(len(locked_icon_colors), 1)
        self.assertGreater(len(unlocked_icon_colors), 1)
        self.assertGreater(len(beginning_icon_colors), 1)
        self.assertGreater(len(code_rain_icon_colors), 1)
        self.assertGreater(len(bullet_time_icon_colors), 1)
        self.assertGreater(len(matrix_dodge_icon_colors), 1)
        self.assertGreater(len(exit_construct_icon_colors), 1)

        with patch("main.subprocess.Popen") as popen:
            main.open_achievements_window()

        command = popen.call_args.args[0]
        self.assertEqual(command[-1], "--achievements")
        self.assertEqual(command[0], main.sys.executable)

    def test_achievements_scroll_reaches_last_entry(self):
        surface = pygame.Surface((600, 560))

        scroll_offset = main.draw_achievements_window(surface, set(main.ACHIEVEMENTS), scroll_offset=1000)

        self.assertEqual(scroll_offset, main.achievements_scroll_limit(560))
        self.assertGreater(scroll_offset, 0)

    def test_wiki_window_scrolls_and_launches_separately(self):
        surface = pygame.Surface((500, 300))
        pages = main.get_wiki_pages()

        self.assertEqual([title for title, _ in pages], ["Basics", "Towers", "Enemies", "Waves", "Extras"])
        scroll_offset = main.draw_wiki_window(surface, 1000, page=1)

        self.assertEqual(scroll_offset, main.wiki_scroll_limit(300, surface_width=500, page=1))
        self.assertGreater(scroll_offset, 0)

        custom_pages = main.get_default_wiki_documents()
        custom_pages["Community Notes"] = "## Community Notes\nShared page text"
        custom_titles = main.get_wiki_page_titles(custom_pages)
        self.assertEqual(
            len(custom_titles),
            len(pages) + 1,
        )
        visible_tabs = main.wiki_page_tab_rects(surface, custom_titles, len(custom_titles) - 1)
        self.assertIn(len(custom_titles) - 1, [index for index, _ in visible_tabs])
        main.draw_wiki_window(pygame.Surface((760, 680)), page=len(pages), documents=custom_pages)

        with patch("main.subprocess.Popen") as popen:
            main.open_wiki_window()

        command = popen.call_args.args[0]
        self.assertEqual(command[-1], "--wiki")

    def test_wiki_edit_persists_locally_without_cloud_settings(self):
        defaults = {"Basics": "Default basics", "Towers": "Default towers"}
        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = os.path.join(temp_dir, "wiki.json")
            with patch.object(wiki_sync, "LOCAL_WIKI_PATH", local_path), patch.dict(
                os.environ,
                {"TOWER_WIKI_SUPABASE_URL": "", "TOWER_WIKI_SUPABASE_ANON_KEY": ""},
            ):
                local_pages = {**defaults, "Community Notes": "New community page"}
                local_pages["Basics"] = "Player-edited basics"
                saved, status = wiki_sync.save_wiki_page("Basics", local_pages["Basics"], local_pages)
                wiki_sync.save_wiki_page("Community Notes", local_pages["Community Notes"], local_pages)
                pages, loaded_status = wiki_sync.load_wiki_pages(defaults)

        self.assertTrue(saved)
        self.assertEqual(status, "Local only")
        self.assertEqual(loaded_status, "Local only")
        self.assertEqual(pages["Basics"], "Player-edited basics")
        self.assertEqual(pages["Community Notes"], "New community page")

    def test_wiki_edits_sync_through_configured_cloud_service(self):
        defaults = {"Basics": "Default basics", "Towers": "Default towers"}
        remote_rows = [
            {"page_id": "Basics", "content": "Shared basics"},
            {"page_id": "Community Notes", "content": "Shared custom page"},
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(wiki_sync, "LOCAL_WIKI_PATH", os.path.join(temp_dir, "wiki.json")), patch.dict(
                os.environ,
                {
                    "TOWER_WIKI_SUPABASE_URL": "https://example.supabase.co",
                    "TOWER_WIKI_SUPABASE_ANON_KEY": "public-test-key",
                },
            ), patch("wiki_sync._request", side_effect=[remote_rows, None, None]) as request:
                pages, status = wiki_sync.load_wiki_pages(defaults)
                saved, save_status = wiki_sync.save_wiki_page("Basics", "Updated shared basics", pages)

        self.assertEqual(pages["Basics"], "Shared basics")
        self.assertEqual(pages["Community Notes"], "Shared custom page")
        self.assertEqual(status, "Shared")
        self.assertTrue(saved)
        self.assertEqual(save_status, "Shared")
        self.assertEqual(request.call_count, 3)
        self.assertEqual(request.call_args_list[-1].args[2], "POST")
        self.assertEqual(request.call_args_list[-1].args[3][0]["content"], "Updated shared basics")

    def test_every_achievement_icon_animates_over_time(self):
        for achievement_id in main.ACHIEVEMENTS:
            with self.subTest(achievement_id=achievement_id):
                first_frame = pygame.Surface((64, 64), pygame.SRCALPHA)
                second_frame = pygame.Surface((64, 64), pygame.SRCALPHA)
                main.draw_achievement_icon(first_frame, achievement_id, (32, 32), 0.0)
                main.draw_achievement_icon(second_frame, achievement_id, (32, 32), 1.3)

                self.assertNotEqual(
                    pygame.image.tobytes(first_frame, "RGBA"),
                    pygame.image.tobytes(second_frame, "RGBA"),
                )

    def test_achievement_popup_renders_and_expires(self):
        main.ACHIEVEMENT_POPUPS.clear()
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))
        self.assertTrue(main.queue_achievement_popup("the_beginning"))
        main.draw_achievement_popups(surface)
        self.assertNotEqual(surface.get_at((main.WIDTH - 310, main.HEIGHT - 70)), (0, 0, 0, 255))

        main.update_achievement_popups(main.ACHIEVEMENT_POPUP_SECONDS)
        self.assertEqual(main.ACHIEVEMENT_POPUPS, [])

    def test_stickman_costumes_are_saved_and_equipable(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({
                "unlocked_towers": ["basic"],
                "win_coins": 30,
                "stickman_costumes": ["classic"],
                "equipped_stickman_costume": "classic",
            }, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                game = Game(MAPS["Classic"])
                self.assertEqual(game.unlocked_stickman_costumes, {"classic"})
                self.assertEqual(game.equipped_stickman_costume, "classic")
                self.assertTrue(game.buy_stickman_costume("classic"))
                self.assertEqual(game.equipped_stickman_costume, "classic")
                self.assertEqual(game.win_coins, 30)
                with open(save_path, "r", encoding="utf-8") as save_handle:
                    saved = json.load(save_handle)
                self.assertEqual(saved["stickman_costumes"], ["classic"])
                self.assertEqual(saved["equipped_stickman_costume"], "classic")
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_hat_text_can_be_purchased_in_costume_window(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({
                "unlocked_towers": ["basic"],
                "win_coins": 10,
                "stickman_hat_text": "sick-man",
            }, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                game = Game(MAPS["Classic"])
                self.assertEqual(game.stickman_hat_text, "sick-man")
                self.assertTrue(game.buy_hat_text("sick-man-2"))
                self.assertEqual(game.stickman_hat_text, "sick-man-2")
                self.assertEqual(game.win_coins, 5)
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_loser_hat_costs_10_win_coins_and_persists(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic"], "win_coins": 12}, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                game = Game(MAPS["Classic"])
                self.assertEqual(game.stickman_hat, "classic")
                self.assertTrue(game.buy_stickman_hat("loser"))
                self.assertEqual(game.stickman_hat, "loser")
                self.assertEqual(game.win_coins, 2)
                self.assertTrue(game.buy_stickman_hat("classic"))
                self.assertTrue(game.buy_stickman_hat("loser"))
                self.assertEqual(game.win_coins, 2)
                with open(save_path, "r", encoding="utf-8") as save_handle:
                    saved = json.load(save_handle)
                self.assertEqual(saved["stickman_hat"], "loser")
                self.assertEqual(saved["win_coins"], 2)
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_additional_hat_prices(self):
        self.assertEqual(main.STICKMAN_HATS["war"]["price"], 5)
        self.assertEqual(main.STICKMAN_HATS["wizard"]["price"], 15)
        self.assertEqual(main.STICKMAN_HATS["headphones"]["price"], 10)
        self.assertEqual(main.STICKMAN_HATS["graduation"]["price"], 10)
        self.assertEqual(main.STICKMAN_HATS["bicycle"]["price"], 10)
        self.assertEqual(main.STICKMAN_HATS["cardboard"]["price"], 15)
        self.assertEqual(main.STICKMAN_HATS["powder"]["price"], 10)

    def test_legs_prices(self):
        self.assertEqual(main.STICKMAN_LEGS["hermes"]["price"], 10)
        self.assertEqual(main.STICKMAN_LEGS["boots"]["price"], 5)

    def test_suit_prices(self):
        self.assertEqual(main.STICKMAN_SUITS["fish"]["price"], 70)
        self.assertEqual(main.STICKMAN_SUITS["cactus"]["price"], 45)
        self.assertEqual(main.STICKMAN_SUITS["jetpack"]["price"], 50)

    def test_object_prices(self):
        self.assertEqual(main.STICKMAN_OBJECTS["magic_hat"]["price"], 75)
        self.assertEqual(main.STICKMAN_OBJECTS["sword"]["price"], 50)

    def test_magic_hat_emits_moving_random_particles(self):
        game = Game(MAPS["Classic"])
        game.developer_stickman_active = True
        game.stickman_object = "magic_hat"

        game.update_developer_stickman(0.16)

        self.assertTrue(game.magic_hat_particles)
        first_particle = game.magic_hat_particles[0]
        self.assertIn(first_particle["shape"], {"star", "coin", "cube", "orb", "house", "hut"})
        first_position = (first_particle["x"], first_particle["y"])

        game.update_developer_stickman(0.1)

        self.assertNotEqual((first_particle["x"], first_particle["y"]), first_position)

    def test_magic_hat_can_emit_and_draw_buildings_and_dancing_cats(self):
        for shape in ("house", "hut", "office_building", "dancing_cat"):
            with self.subTest(shape=shape):
                game = Game(MAPS["Classic"])
                game.developer_stickman_active = True
                game.stickman_object = "magic_hat"
                with patch("main.random.choices", return_value=[shape]):
                    game.update_developer_stickman(0.01)

                self.assertEqual(game.magic_hat_particles[0]["shape"], shape)
                if shape == "dancing_cat":
                    old_phase = game.magic_hat_particles[0]["dance_phase"]
                    game.update_developer_stickman(0.01)
                    self.assertNotEqual(game.magic_hat_particles[0]["dance_phase"], old_phase)
                game.draw_developer_stickman(pygame.Surface((main.WIDTH, main.HEIGHT)))

    def test_jetpack_suit_emits_flame_trail(self):
        game = Game(MAPS["Classic"])
        game.developer_stickman_active = True
        game.stickman_suit = "jetpack"

        game.update_developer_stickman(0.05)

        self.assertTrue(game.jetpack_flames)
        first_flame = game.jetpack_flames[0]
        first_position = (first_flame["x"], first_flame["y"])

        game.update_developer_stickman(0.05)

        self.assertNotEqual((first_flame["x"], first_flame["y"]), first_position)

    def test_tower_placement_preview_shows_validity(self):
        game = Game(MAPS["Classic"], sandbox=True)
        surface = pygame.Surface((main.WIDTH, main.HEIGHT))

        game.selected_tower = "basic"
        self.assertTrue(game.draw_placement_preview(surface, (80, 320)))
        self.assertFalse(game.draw_placement_preview(surface, (280, 200)))

        game.selected_tower = "mine"
        self.assertTrue(game.draw_placement_preview(surface, (80, 200)))
        game.money = 0
        self.assertFalse(game.draw_placement_preview(surface, (80, 200)))

    def test_object_selection_is_saved_and_loaded(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({
                "unlocked_towers": ["basic"],
                "win_coins": 80,
                "stickman_object": "none",
                "stickman_objects": ["none"],
            }, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                game = Game(MAPS["Classic"])
                self.assertEqual(game.stickman_object, "none")
                self.assertEqual(main.load_stickman_object(), "none")
                self.assertTrue(game.buy_stickman_object("magic_hat"))
                self.assertEqual(game.stickman_object, "magic_hat")
                self.assertEqual(game.win_coins, 5)
                self.assertEqual(main.load_stickman_object(), "magic_hat")
                with open(save_path, "r", encoding="utf-8") as save_handle:
                    saved = json.load(save_handle)
                self.assertEqual(saved["stickman_object"], "magic_hat")
                self.assertEqual(saved["win_coins"], 5)
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_preview_renderer_supports_suit_graphics(self):
        surface = pygame.Surface((200, 200))
        main.draw_stickman_preview(surface, 100, 100, "classic", hat_id="classic", hat_text="sick-man", leg_id="boots", suit_id="fish")
        self.assertEqual(surface.get_size(), (200, 200))

    def test_stickman_costume_button_unlocks_after_first_developer_mode(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({
                "unlocked_towers": ["basic"],
                "win_coins": 0,
            }, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                game = Game(MAPS["Classic"])
                self.assertFalse(game.stickman_costume_menu_unlocked)
                self.assertFalse(game.stickman_costume_menu_open)

                for key in "sick_man":
                    game.register_key(key)

                self.assertTrue(game.developer_mode)
                self.assertTrue(game.stickman_costume_menu_unlocked)
                self.assertFalse(game.stickman_costume_menu_open)
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_developer_mode_flag_persists_in_save_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({
                "unlocked_towers": ["basic"],
                "win_coins": 0,
                "developer_mode_opened": True,
            }, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                game = Game(MAPS["Classic"])
                self.assertTrue(game.stickman_costume_menu_unlocked)
                for key in "sick_man":
                    game.register_key(key)
                with open(save_path, "r", encoding="utf-8") as save_handle:
                    saved = json.load(save_handle)
                self.assertTrue(saved["developer_mode_opened"])
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_sandbox_mode_keeps_towers_available_without_unlocking(self):
        game = Game(MAPS["Classic"], sandbox=True)

        self.assertTrue(game.sandbox)
        self.assertGreater(game.money, 100000)
        self.assertGreater(game.lives, 10)
        self.assertEqual(game.unlocked_towers, {"basic"})
        for tower in [
            "basic",
            "rapid",
            "sniper",
            "mine",
            "freeze",
            "boinger",
            "walker",
            "mine_tower",
            "milk_bob",
        ]:
            self.assertTrue(game.is_tower_unlocked(tower), tower)

        game.wave_index = 0
        game.spawned = WAVES[0]["count"]
        game.complete_wave_unlocks()
        game.unlock_towers()

        self.assertEqual(game.highest_cleared_wave, 0)
        self.assertFalse(game.wave_six_cleared)
        self.assertEqual(game.unlocked_towers, {"basic"})
        game.lives = 0
        game.update(0.016)
        self.assertFalse(game.game_over)

    def test_tower_directory_lists_every_tower_and_hides_secret_lock_state(self):
        entries = main.get_tower_directory_entries({"basic"}, 0, 0)

        self.assertEqual(len(entries), 15)
        self.assertEqual(entries[0]["shortcut"], "1")
        self.assertEqual(entries[0]["name"], "Basic")
        phantom = next(entry for entry in entries if entry["tower_id"] == "phantom")
        self.assertEqual(phantom["shortcut"], "D")
        self.assertFalse(phantom["unlocked"])
        milk_bob = next(entry for entry in entries if entry["tower_id"] == "milk_bob")
        self.assertEqual(milk_bob["shortcut"], "E")
        self.assertFalse(milk_bob["unlocked"])
        self.assertEqual(milk_bob["unlock_hint"], "Unlock: wave 8")
        cactus = next(entry for entry in entries if entry["tower_id"] == "cactus")
        self.assertFalse(cactus["unlocked"])
        self.assertEqual(cactus["unlock_hint"], "Secret tower")
        mine_tower = next(entry for entry in entries if entry["tower_id"] == "mine_tower")
        self.assertEqual(mine_tower["unlock_hint"], "Secret tower")
        wiki_text = " ".join(text for text, _ in main.get_wiki_rows())
        self.assertNotIn("Walker over a Freeze tower", wiki_text)
        self.assertNotIn("arrange towers around a mine", wiki_text)
        self.assertTrue(
            next(entry for entry in main.get_tower_directory_entries(set(), 0, 0, sandbox=True)
                 if entry["tower_id"] == "cactus")["unlocked"]
        )

    def test_tower_directory_filters_locked_towers_and_scrolls(self):
        entries = main.get_tower_directory_entries({"basic", "rapid", "sniper", "freeze", "boinger", "walker"}, 6, 0, unlocked_only=True)

        self.assertTrue(entries)
        self.assertTrue(all(entry["unlocked"] for entry in entries))
        self.assertNotIn("phantom", {entry["tower_id"] for entry in entries})

        all_entries = main.get_tower_directory_entries(set(), 0, 0, sandbox=True)
        surface = pygame.Surface((760, 240))
        scroll_offset = main.draw_tower_directory_window(surface, all_entries, 1000)

        self.assertEqual(scroll_offset, main.tower_directory_scroll_limit(240, len(all_entries)))
        self.assertGreater(scroll_offset, 0)

    def test_sandbox_mode_does_not_update_saved_win_coins(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as save_file:
            json.dump({"unlocked_towers": ["basic"], "win_coins": 12}, save_file)
            save_path = save_file.name

        try:
            original_save_file = main.SAVE_FILE
            main.SAVE_FILE = save_path
            try:
                game = Game(MAPS["Classic"], sandbox=True)
                self.assertEqual(game.win_coins, 12)
                game.win_coins += 5
                self.assertEqual(game.win_coins, 17)
                with open(save_path, "r", encoding="utf-8") as handle:
                    saved = json.load(handle)
                self.assertEqual(saved["win_coins"], 12)
            finally:
                main.SAVE_FILE = original_save_file
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

    def test_dev_code_activates_developer_mode(self):
        game = Game(MAPS["Classic"])
        for key in [
            "s",
            "i",
            "c",
            "k",
            "_",
            "m",
            "a",
            "n",
        ]:
            game.register_key(key)
        self.assertTrue(game.developer_mode)

    def test_cheat_codes_work_on_seasonal_maps(self):
        game = Game(main.get_map_path("Gobble Gobble"), map_name="Gobble Gobble")

        for key in "sick_man":
            game.register_cheat_key(key)
        self.assertTrue(game.developer_mode)

        with patch.object(game, "upgrade_all_towers") as upgrade_all_towers:
            for key in "soft&ball":
                game.register_cheat_key(key)

        upgrade_all_towers.assert_called_once_with()

    def test_developer_mode_only_controls_enemy_pause(self):
        game = Game(MAPS["Classic"])
        starting_money = game.money
        starting_lives = game.lives
        for key in "sick_man":
            game.register_key(key)

        self.assertTrue(game.developer_mode)
        self.assertEqual(game.money, starting_money)
        self.assertEqual(game.lives, starting_lives)
        self.assertFalse(game.enemies_paused)

        game.spawn_enemy()
        enemy = game.enemies[0]
        starting_position = (enemy.x, enemy.y)
        game.toggle_enemy_pause()
        game.update(1.0)

        self.assertTrue(game.enemies_paused)
        self.assertEqual((enemy.x, enemy.y), starting_position)

        game.toggle_enemy_pause()
        game.update(1.0)
        self.assertNotEqual((enemy.x, enemy.y), starting_position)

    def test_only_developer_mode_can_move_enemies_manually(self):
        game = Game(MAPS["Classic"])
        game.spawn_enemy()
        enemy = game.enemies[0]
        starting_position = (enemy.x, enemy.y)

        game.move_enemies(20, 0)
        self.assertEqual((enemy.x, enemy.y), starting_position)

        for key in "sick_man":
            game.register_key(key)
        game.move_enemies(20, 0)
        self.assertEqual(enemy.x, starting_position[0] + 20)

    def test_developer_mode_can_spawn_enemy(self):
        game = Game(MAPS["Classic"])
        self.assertEqual(len(game.enemies), 0)

        for key in "sick_man":
            game.register_key(key)

        game.set_developer_spawn_type("ground")
        game.developer_spawn_enemy()
        self.assertEqual(len(game.enemies), 1)

        game.set_developer_spawn_type("flyer")
        game.developer_spawn_enemy()
        self.assertEqual(len(game.enemies), 2)
        self.assertEqual(game.enemies[-1].type, "flyer")

    def test_developer_mode_can_drag_one_enemy(self):
        game = Game(MAPS["Classic"])
        game.spawn_enemy()
        enemy = game.enemies[0]
        original_position = (enemy.x, enemy.y)

        self.assertFalse(game.begin_enemy_drag(original_position))
        for key in "sick_man":
            game.register_key(key)

        self.assertTrue(game.begin_enemy_drag(original_position))
        game.drag_enemy((original_position[0] + 35, original_position[1] + 10))
        game.end_enemy_drag()

        self.assertEqual((enemy.x, enemy.y), (original_position[0] + 35, original_position[1] + 10))


if __name__ == "__main__":
    unittest.main()
