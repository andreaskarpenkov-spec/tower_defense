import json
import os
import tempfile
import unittest

import pygame

import main
from main import Game, MAPS


class SandboxModeTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
