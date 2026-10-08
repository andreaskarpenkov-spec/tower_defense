import json
import os
import tempfile
import unittest
from unittest.mock import patch

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
                self.assertEqual(earned, set(main.ACHIEVEMENTS))
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
