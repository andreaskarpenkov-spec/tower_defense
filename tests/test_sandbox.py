import json
import os
import tempfile
import unittest

import pygame

import main
from main import Enemy, Game, MAPS, MAP_UNLOCK_COST, TOWER_UNLOCK_WAVES, Tower, WAVES, load_unlocked_maps, save_unlocks


class SandboxModeTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
