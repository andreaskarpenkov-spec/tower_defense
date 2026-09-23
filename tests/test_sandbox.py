import json
import os
import tempfile
import unittest

import pygame

import main
from main import Enemy, Game, MAPS, MAP_UNLOCK_COST, TOWER_UNLOCK_WAVES, Tower, WAVES, load_unlocked_maps, save_unlocks


class SandboxModeTest(unittest.TestCase):
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

    def test_maps_have_distinct_backgrounds(self):
        classic = Game(MAPS["Classic"], map_name="Classic")
        loop = Game(MAPS["Loop"], map_name="Loop")
        spiral = Game(MAPS["Spiral"], map_name="Spiral")

        self.assertNotEqual(classic.background_color, loop.background_color)
        self.assertNotEqual(loop.background_color, spiral.background_color)
        self.assertEqual(classic.map_name, "Classic")

    def test_game_has_six_waves(self):
        self.assertEqual(len(WAVES), 6)

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

    def test_sandbox_mode_unlocks_everything_and_ignores_loss(self):
        game = Game(MAPS["Classic"], sandbox=True)

        self.assertTrue(game.sandbox)
        self.assertGreater(game.money, 100000)
        self.assertGreater(game.lives, 10)
        for tower in [
            "basic",
            "rapid",
            "sniper",
            "mine",
            "freeze",
            "boinger",
            "walker",
            "mine_tower",
        ]:
            self.assertTrue(game.is_tower_unlocked(tower), tower)

        game.lives = 0
        game.update(0.016)
        self.assertFalse(game.game_over)

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
