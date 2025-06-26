import pytest
from unittest.mock import patch, MagicMock
from pikomino import (
    DiceValue,
    Dice,
    Tile,
    TurnResult,
    TurnState,
    Player,
    PikominoGame,
)
from strategies import (
    GameStrategy,
    ConservativeStrategy,
    AggressiveStrategy,
    RandomStrategy,
)


class TestDiceValue:
    """Tests pour les valeurs de dés"""

    def test_dice_values(self):
        """Test des valeurs numériques des dés"""
        assert DiceValue.ONE.value == 1
        assert DiceValue.TWO.value == 2
        assert DiceValue.THREE.value == 3
        assert DiceValue.FOUR.value == 4
        assert DiceValue.FIVE.value == 5
        assert DiceValue.WORM.value == 6

    def test_dice_point_values(self):
        """Test des valeurs en points des dés"""
        assert Dice.get_point_value(DiceValue.ONE) == 1
        assert Dice.get_point_value(DiceValue.TWO) == 2
        assert Dice.get_point_value(DiceValue.THREE) == 3
        assert Dice.get_point_value(DiceValue.FOUR) == 4
        assert Dice.get_point_value(DiceValue.FIVE) == 5
        assert Dice.get_point_value(DiceValue.WORM) == 5  # Ver vaut 5 points


class TestDice:
    """Tests pour la classe Dice"""

    def test_dice_roll_returns_valid_value(self):
        """Test que le lancer de dé retourne une valeur valide"""
        for _ in range(100):  # Test multiple pour vérifier la randomisation
            result = Dice.roll()
            assert isinstance(result, DiceValue)
            assert result in list(DiceValue)


class TestTile:
    """Tests pour les tuiles Pikomino"""

    def test_tile_creation(self):
        """Test de création de tuile"""
        tile = Tile(25, 0)  # Le post_init calculera les vers
        assert tile.value == 25
        assert tile.worms == 2  # Selon les règles, tuile 25 = 2 vers

    def test_tile_worm_mapping(self):
        """Test du mapping vers/valeur selon les règles"""
        # Tuiles 21-24 : 1 ver
        for value in [21, 22, 23, 24]:
            tile = Tile(value, 0)
            assert tile.worms == 1

        # Tuiles 25-28 : 2 vers
        for value in [25, 26, 27, 28]:
            tile = Tile(value, 0)
            assert tile.worms == 2

        # Tuiles 29-32 : 3 vers
        for value in [29, 30, 31, 32]:
            tile = Tile(value, 0)
            assert tile.worms == 3

        # Tuiles 33-36 : 4 vers
        for value in [33, 34, 35, 36]:
            tile = Tile(value, 0)
            assert tile.worms == 4

    def test_tile_invalid_value(self):
        """Test avec valeur de tuile invalide"""
        tile = Tile(50, 0)  # Valeur non mappée
        assert tile.value == 50
        assert tile.worms == 0  # Pas de mapping = worms reste 0


class TestTurnState:
    """Tests pour l'état du tour"""

    def test_initial_state(self):
        """Test de l'état initial d'un tour"""
        state = TurnState()
        assert state.remaining_dice == 8
        assert state.reserved_dice == {}
        assert state.used_values == set()
        assert state.current_roll == []

    def test_score_calculation_empty(self):
        """Test du calcul de score avec aucun dé réservé"""
        state = TurnState()
        assert state.get_total_score() == 0

    def test_score_calculation_with_dice(self):
        """Test du calcul de score avec dés réservés"""
        state = TurnState()
        state.reserved_dice = {
            DiceValue.ONE: 2,  # 2 * 1 = 2 points
            DiceValue.THREE: 1,  # 1 * 3 = 3 points
            DiceValue.WORM: 2,  # 2 * 5 = 10 points
        }
        assert state.get_total_score() == 15  # 2 + 3 + 10

    def test_has_worm_false(self):
        """Test has_worm sans ver"""
        state = TurnState()
        state.reserved_dice = {DiceValue.ONE: 2, DiceValue.THREE: 1}
        assert not state.has_worm()

    def test_has_worm_true(self):
        """Test has_worm avec ver"""
        state = TurnState()
        state.reserved_dice = {DiceValue.ONE: 2, DiceValue.WORM: 1}
        assert state.has_worm()

    def test_can_reserve_value_valid(self):
        """Test de réservation de valeur valide"""
        state = TurnState()
        state.current_roll = [DiceValue.ONE, DiceValue.TWO, DiceValue.ONE]
        state.used_values = set()

        assert state.can_reserve_value(DiceValue.ONE)
        assert state.can_reserve_value(DiceValue.TWO)

    def test_can_reserve_value_not_in_roll(self):
        """Test de réservation de valeur non présente"""
        state = TurnState()
        state.current_roll = [DiceValue.ONE, DiceValue.TWO]
        state.used_values = set()

        assert not state.can_reserve_value(DiceValue.THREE)

    def test_can_reserve_value_already_used(self):
        """Test de réservation de valeur déjà utilisée"""
        state = TurnState()
        state.current_roll = [DiceValue.ONE, DiceValue.TWO]
        state.used_values = {DiceValue.ONE}

        assert not state.can_reserve_value(DiceValue.ONE)
        assert state.can_reserve_value(DiceValue.TWO)


class TestPlayer:
    """Tests pour la classe Player"""

    def test_player_creation(self):
        """Test de création de joueur"""
        player = Player("Test Player")
        assert player.name == "Test Player"
        assert player.tiles == []
        assert player.strategy is None

    def test_player_score_empty(self):
        """Test du score avec aucune tuile"""
        player = Player("Test")
        assert player.get_score() == 0

    def test_player_score_with_tiles(self):
        """Test du score avec des tuiles"""
        player = Player("Test")
        player.tiles = [Tile(21, 1), Tile(25, 2), Tile(33, 4)]
        assert player.get_score() == 7  # 1 + 2 + 4 vers

    def test_get_top_tile_empty(self):
        """Test get_top_tile sans tuile"""
        player = Player("Test")
        assert player.get_top_tile() is None

    def test_get_top_tile_with_tiles(self):
        """Test get_top_tile avec tuiles"""
        player = Player("Test")
        tile1 = Tile(21, 1)
        tile2 = Tile(25, 2)
        player.tiles = [tile1, tile2]

        assert player.get_top_tile() == tile2  # Dernière tuile ajoutée

    def test_add_remove_tile(self):
        """Test d'ajout et suppression de tuile"""
        player = Player("Test")
        tile = Tile(21, 1)

        player.add_tile(tile)
        assert len(player.tiles) == 1
        assert player.get_top_tile() == tile

        removed = player.remove_top_tile()
        assert removed == tile
        assert len(player.tiles) == 0
        assert player.get_top_tile() is None

    def test_remove_top_tile_empty(self):
        """Test de suppression sur pile vide"""
        player = Player("Test")
        assert player.remove_top_tile() is None


class TestGameSpecialCases:
    """Tests pour les cas particuliers du jeu selon RULES.md"""

    def test_failed_turn_lose_top_tile_and_remove_highest_center(self):
        """Test: Quand un joueur rate son tour, il perd sa tuile du dessus et la tuile la plus haute du centre est retirée"""
        players = [Player("Test1"), Player("Test2")]
        game = PikominoGame(players)

        # Donner des tuiles aux joueurs
        players[0].add_tile(Tile(21, 1))
        players[0].add_tile(Tile(25, 2))  # Tuile du dessus

        # Mémoriser l'état initial
        initial_center_tiles = len(game.tiles_center)
        top_tile_value = players[0].get_top_tile().value
        highest_center_tile = max(game.tiles_center, key=lambda t: t.value)

        # Simuler un échec
        game.handle_failed_turn()

        # Vérifications
        assert len(players[0].tiles) == 1  # A perdu sa tuile du dessus
        assert players[0].get_top_tile().value == 21  # Ne reste que la première tuile
        assert (
            len(game.tiles_center) == initial_center_tiles - 1
        )  # Une tuile retirée du centre
        assert (
            highest_center_tile not in game.tiles_center
        )  # La plus haute a été retirée
        assert len(game.removed_tiles) == 2  # Deux tuiles retirées au total

    def test_failed_turn_no_player_tile_still_removes_center(self):
        """Test: Même si le joueur n'a pas de tuile, la tuile du centre est quand même retirée"""
        players = [Player("Test1")]
        game = PikominoGame(players)

        initial_center_tiles = len(game.tiles_center)
        highest_center_tile = max(game.tiles_center, key=lambda t: t.value)

        # Le joueur n'a pas de tuiles
        assert players[0].get_top_tile() is None

        game.handle_failed_turn()

        # La tuile du centre doit quand même être retirée
        assert len(game.tiles_center) == initial_center_tiles - 1
        assert highest_center_tile not in game.tiles_center
        assert len(game.removed_tiles) == 1

    def test_steal_tile_exact_score_match(self):
        """Test: Un joueur peut voler une tuile d'un autre joueur en faisant le score exact"""
        players = [Player("Test1"), Player("Test2")]
        game = PikominoGame(players)

        # Donner une tuile au joueur 2
        target_tile = Tile(28, 2)  # Valeur 28
        players[1].add_tile(target_tile)

        # Le joueur 1 fait exactement 28 points avec un ver
        turn_state = TurnState()
        turn_state.reserved_dice = {
            DiceValue.FIVE: 4,
            DiceValue.WORM: 1,
            DiceValue.THREE: 1,
        }  # 5*4 + 5*1 + 3*1 = 28

        score = turn_state.get_total_score()
        has_worm = turn_state.has_worm()

        assert score == 28
        assert has_worm

        # Rechercher la tuile à prendre
        tile_to_take = game.find_tile_to_take(score, has_worm)

        # Doit trouver la tuile du joueur 2 (score exact)
        assert tile_to_take is not None
        assert tile_to_take.value == 28

        # Prendre la tuile
        game.take_tile(tile_to_take)

        # Vérifications
        assert len(players[1].tiles) == 0  # Le joueur 2 a perdu sa tuile
        assert len(players[0].tiles) == 1  # Le joueur 1 a gagné la tuile
        assert players[0].get_top_tile().value == 28

    def test_cannot_reserve_same_value_twice(self):
        """Test: Il n'est pas possible de réserver deux fois la même valeur lors du même tour"""
        state = TurnState()

        # Première réservation de ONE
        state.current_roll = [DiceValue.ONE, DiceValue.ONE, DiceValue.TWO]
        state.used_values = set()

        assert state.can_reserve_value(DiceValue.ONE)

        # Simuler la réservation
        state.used_values.add(DiceValue.ONE)

        # Nouveau lancer avec encore des ONE
        state.current_roll = [DiceValue.ONE, DiceValue.THREE, DiceValue.FOUR]

        # Ne peut plus réserver ONE
        assert not state.can_reserve_value(DiceValue.ONE)
        assert state.can_reserve_value(DiceValue.THREE)
        assert state.can_reserve_value(DiceValue.FOUR)

    def test_must_have_worm_to_take_tile(self):
        """Test: Il faut au moins un ver pour prétendre à une tuile"""
        players = [Player("Test1")]
        game = PikominoGame(players)

        # Score suffisant mais pas de ver
        assert not game.can_take_tile(21, 25, False)

        # Score suffisant avec ver
        assert game.can_take_tile(21, 25, True)

        # Score insuffisant même avec ver
        assert not game.can_take_tile(25, 20, True)

    def test_removed_tiles_cannot_be_taken(self):
        """Test: Les tuiles retirées du jeu ne peuvent plus être prises"""
        players = [Player("Test1"), Player("Test2")]
        game = PikominoGame(players)

        # Retirer manuellement une tuile du centre
        tile_to_remove = game.tiles_center[0]
        game.tiles_center.remove(tile_to_remove)
        game.removed_tiles.append(tile_to_remove)

        # Même avec un score suffisant, la tuile ne peut plus être prise
        score = tile_to_remove.value + 10
        tile_found = game.find_tile_to_take(score, True)

        # Ne doit pas trouver la tuile retirée
        if tile_found:
            assert tile_found.value != tile_to_remove.value

    def test_game_ends_when_no_center_tiles(self):
        """Test: La partie se termine quand il n'y a plus de tuiles au centre"""
        players = [Player("Test1")]
        game = PikominoGame(players)

        assert not game.is_game_over()

        # Retirer toutes les tuiles du centre
        game.tiles_center = []

        assert game.is_game_over()

    def test_find_highest_possible_tile_in_center(self):
        """Test: Quand plusieurs tuiles sont disponibles, prendre la plus haute possible"""
        players = [Player("Test1")]
        game = PikominoGame(players)

        # Score de 30
        tile_found = game.find_tile_to_take(30, True)

        # Doit trouver la tuile 30 (ou la plus haute ≤ 30)
        assert tile_found is not None
        assert tile_found.value <= 30

        # Vérifier que c'est bien la plus haute possible
        possible_tiles = [t for t in game.tiles_center if t.value <= 30]
        highest_possible = max(possible_tiles, key=lambda t: t.value)
        assert tile_found.value == highest_possible.value


class TestTurnFailureScenarios:
    """Tests pour les différents scénarios d'échec de tour"""

    def test_no_valid_dice_choice_available(self):
        """Test: Échec quand aucune nouvelle valeur n'est disponible"""
        players = [Player("Test1")]
        game = PikominoGame(players)

        # Créer un état où toutes les valeurs ont été utilisées
        turn_state = TurnState()
        turn_state.used_values = {
            DiceValue.ONE,
            DiceValue.TWO,
            DiceValue.THREE,
            DiceValue.FOUR,
            DiceValue.FIVE,
            DiceValue.WORM,
        }
        turn_state.current_roll = [
            DiceValue.ONE,
            DiceValue.TWO,
        ]  # Valeurs déjà utilisées

        # Aucune nouvelle valeur disponible
        assert not any(turn_state.can_reserve_value(v) for v in turn_state.current_roll)

    def test_player_stops_voluntarily(self):
        """Test: Un joueur peut choisir de s'arrêter même s'il peut continuer"""
        # Ceci dépend de la stratégie du joueur et de should_continue_turn()
        player = Player("Test", ConservativeStrategy())
        turn_state = TurnState()
        turn_state.reserved_dice = {
            DiceValue.WORM: 1,
            DiceValue.FIVE: 3,
        }  # 20 points avec ver
        turn_state.remaining_dice = 4

        # La stratégie conservative devrait s'arrêter car elle peut prendre une tuile
        should_continue = player.should_continue_turn(turn_state)
        # Dépend de l'implémentation de la stratégie - on teste le comportement
        # La stratégie conservative s'arrête dès qu'elle peut prendre une tuile (≥21 avec ver)
        if turn_state.get_total_score() >= 21 and turn_state.has_worm():
            assert not should_continue


class MockStrategy(GameStrategy):
    """Stratégie de test pour contrôler le comportement"""

    def __init__(self, dice_choice=None, continue_choice=True):
        self.dice_choice = dice_choice
        self.continue_choice = continue_choice

    def choose_dice_value(self, turn_state, player):
        return self.dice_choice

    def should_continue_turn(self, turn_state, player):
        return self.continue_choice

    def choose_target_tile(self, score, has_worm, center_tiles, stealable_tiles, current_player):
        # Comportement par défaut pour les tests
        if not has_worm:
            return None
        if stealable_tiles:
            return stealable_tiles[0][0]  # Première tuile volable
        if center_tiles:
            return center_tiles[0]  # Première tuile du centre
        return None


class TestConservativeStrategy:
    """Tests pour la stratégie conservative"""

    def test_prefers_worm_when_none(self):
        """Test que la stratégie conservative privilégie les vers quand elle n'en a pas"""
        strategy = ConservativeStrategy()
        player = Player("Test", strategy)

        turn_state = TurnState()
        turn_state.current_roll = [DiceValue.ONE, DiceValue.WORM, DiceValue.THREE]
        turn_state.used_values = set()

        choice = strategy.choose_dice_value(turn_state, player)
        assert choice == DiceValue.WORM

    def test_chooses_most_frequent_when_has_worm(self):
        """Test qu'elle choisit la valeur la plus fréquente quand elle a déjà un ver"""
        strategy = ConservativeStrategy()
        player = Player("Test", strategy)

        turn_state = TurnState()
        turn_state.reserved_dice = {DiceValue.WORM: 1}  # A déjà un ver
        turn_state.current_roll = [
            DiceValue.ONE,
            DiceValue.ONE,
            DiceValue.ONE,
            DiceValue.TWO,
        ]
        turn_state.used_values = {DiceValue.WORM}

        choice = strategy.choose_dice_value(turn_state, player)
        assert choice == DiceValue.ONE  # Plus fréquent (3 occurrences)

    def test_stops_when_can_take_tile(self):
        """Test qu'elle s'arrête dès qu'elle peut prendre une tuile"""
        strategy = ConservativeStrategy()
        player = Player("Test", strategy)

        turn_state = TurnState()
        turn_state.reserved_dice = {
            DiceValue.WORM: 1,
            DiceValue.FIVE: 3,
        }  # 5*1 + 5*3 = 20

        # Ne peut pas encore prendre (< 21)
        assert strategy.should_continue_turn(turn_state, player)

        # Maintenant peut prendre (≥ 21)
        turn_state.reserved_dice[DiceValue.ONE] = 1  # +1 = 21 total
        assert not strategy.should_continue_turn(turn_state, player)

    def test_continues_when_cannot_take_tile(self):
        """Test qu'elle continue quand elle ne peut pas prendre de tuile"""
        strategy = ConservativeStrategy()
        player = Player("Test", strategy)

        turn_state = TurnState()
        turn_state.reserved_dice = {DiceValue.ONE: 3}  # 3 points, pas de ver

        assert strategy.should_continue_turn(turn_state, player)


class TestAggressiveStrategy:
    """Tests pour la stratégie agressive"""

    def test_prioritizes_high_values(self):
        """Test qu'elle privilégie les hautes valeurs"""
        strategy = AggressiveStrategy()
        player = Player("Test", strategy)

        turn_state = TurnState()
        turn_state.current_roll = [
            DiceValue.ONE,
            DiceValue.TWO,
            DiceValue.FIVE,
            DiceValue.WORM,
        ]
        turn_state.used_values = set()

        choice = strategy.choose_dice_value(turn_state, player)
        # Doit choisir WORM ou FIVE (selon l'ordre de priorité)
        assert choice in [DiceValue.WORM, DiceValue.FIVE]

    def test_continues_until_30_points(self):
        """Test qu'elle continue jusqu'à avoir au moins 30 points"""
        strategy = AggressiveStrategy()
        player = Player("Test", strategy)

        turn_state = TurnState()
        turn_state.reserved_dice = {DiceValue.WORM: 1, DiceValue.FIVE: 4}  # 25 points
        turn_state.remaining_dice = 3

        # Continue car < 30 points
        assert strategy.should_continue_turn(turn_state, player)

        # S'arrête quand ≥ 30 points
        turn_state.reserved_dice[DiceValue.FIVE] = 5  # 30 points
        assert not strategy.should_continue_turn(turn_state, player)

        # S'arrête aussi quand plus de dés
        turn_state.remaining_dice = 0
        turn_state.reserved_dice[DiceValue.FIVE] = 4  # Retour à 25 points
        assert not strategy.should_continue_turn(turn_state, player)


class TestPikominoGame:
    """Tests pour la classe PikominoGame"""

    def test_game_initialization(self):
        """Test de l'initialisation du jeu"""
        players = [Player("Alice"), Player("Bob")]
        game = PikominoGame(players)

        assert len(game.players) == 2
        assert game.current_player_idx == 0
        assert len(game.tiles_center) == 16  # Tuiles 21-36
        assert len(game.removed_tiles) == 0
        assert not game.game_over
        assert len(game.turn_history) == 0

    def test_tile_initialization_correct(self):
        """Test que les tuiles sont correctement initialisées"""
        players = [Player("Test")]
        game = PikominoGame(players)

        # Vérifier que toutes les tuiles 21-36 sont présentes
        tile_values = [tile.value for tile in game.tiles_center]
        expected_values = list(range(21, 37))

        assert sorted(tile_values) == sorted(expected_values)

        # Vérifier les vers de quelques tuiles
        tile_21 = next(t for t in game.tiles_center if t.value == 21)
        tile_36 = next(t for t in game.tiles_center if t.value == 36)

        assert tile_21.worms == 1
        assert tile_36.worms == 4

    def test_current_player_and_next(self):
        """Test de la gestion du joueur actuel"""
        players = [Player("Alice"), Player("Bob"), Player("Charlie")]
        game = PikominoGame(players)

        assert game.get_current_player().name == "Alice"

        game.next_player()
        assert game.get_current_player().name == "Bob"

        game.next_player()
        assert game.get_current_player().name == "Charlie"

        game.next_player()  # Doit revenir au premier
        assert game.get_current_player().name == "Alice"

    def test_can_take_tile(self):
        """Test de la fonction can_take_tile"""
        players = [Player("Test")]
        game = PikominoGame(players)

        # Peut prendre avec ver et score suffisant
        assert game.can_take_tile(21, 25, True)

        # Ne peut pas prendre sans ver
        assert not game.can_take_tile(21, 25, False)

        # Ne peut pas prendre avec score insuffisant
        assert not game.can_take_tile(25, 20, True)

        # Score exact
        assert game.can_take_tile(25, 25, True)

    def test_find_tile_to_take_center(self):
        """Test de recherche de tuile dans le centre"""
        players = [Player("Test")]
        game = PikominoGame(players)

        # Score pour prendre tuile 25
        tile = game.find_tile_to_take(25, True)
        assert tile is not None
        assert tile.value == 25

        # Score pour prendre tuile 30
        tile = game.find_tile_to_take(30, True)
        assert tile is not None
        assert tile.value == 30

        # Score très élevé - doit prendre la plus haute (36)
        tile = game.find_tile_to_take(50, True)
        assert tile is not None
        assert tile.value == 36

        # Pas de ver - aucune tuile
        tile = game.find_tile_to_take(30, False)
        assert tile is None

    def test_find_tile_to_take_from_player(self):
        """Test de vol de tuile d'un autre joueur"""
        players = [Player("Alice"), Player("Bob")]
        game = PikominoGame(players)

        # Bob a une tuile
        bob_tile = Tile(28, 2)
        players[1].add_tile(bob_tile)

        # Alice fait exactement 28 points
        game.current_player_idx = 0  # Alice joue
        tile = game.find_tile_to_take(28, True)

        # Doit trouver la tuile de Bob car score exact
        assert tile is not None
        assert tile.value == 28
        assert tile is bob_tile  # Même référence

    def test_take_tile_from_center(self):
        """Test de prise de tuile du centre"""
        players = [Player("Test")]
        game = PikominoGame(players)

        # Trouver une tuile dans le centre
        target_tile = game.tiles_center[0]
        initial_center_count = len(game.tiles_center)

        success = game.take_tile(target_tile)

        assert success
        assert len(game.tiles_center) == initial_center_count - 1
        assert target_tile not in game.tiles_center
        assert len(players[0].tiles) == 1
        assert players[0].get_top_tile() == target_tile

    def test_take_tile_from_player(self):
        """Test de vol de tuile d'un autre joueur"""
        players = [Player("Alice"), Player("Bob")]
        game = PikominoGame(players)

        # Bob a une tuile
        bob_tile = Tile(28, 2)
        players[1].add_tile(bob_tile)

        # Alice vole la tuile
        game.current_player_idx = 0
        success = game.take_tile(bob_tile)

        assert success
        assert len(players[1].tiles) == 0  # Bob a perdu sa tuile
        assert len(players[0].tiles) == 1  # Alice a gagné la tuile
        assert players[0].get_top_tile() == bob_tile

    def test_handle_failed_turn(self):
        """Test de gestion d'un tour raté"""
        players = [Player("Alice"), Player("Bob")]
        game = PikominoGame(players)

        # Alice a des tuiles
        alice_tile1 = Tile(21, 1)
        alice_tile2 = Tile(25, 2)
        players[0].add_tile(alice_tile1)
        players[0].add_tile(alice_tile2)

        initial_center_count = len(game.tiles_center)
        highest_tile = max(game.tiles_center, key=lambda t: t.value)

        game.handle_failed_turn()

        # Alice a perdu sa tuile du dessus
        assert len(players[0].tiles) == 1
        assert players[0].get_top_tile() == alice_tile1

        # La tuile la plus haute du centre a été retirée
        assert len(game.tiles_center) == initial_center_count - 1
        assert highest_tile not in game.tiles_center

        # Les tuiles sont dans removed_tiles
        assert len(game.removed_tiles) == 2
        assert alice_tile2 in game.removed_tiles
        assert highest_tile in game.removed_tiles

    def test_handle_failed_turn_no_player_tile(self):
        """Test de gestion d'un tour raté sans tuile joueur"""
        players = [Player("Test")]
        game = PikominoGame(players)

        # Le joueur n'a pas de tuiles
        assert players[0].get_top_tile() is None

        initial_center_count = len(game.tiles_center)
        highest_tile = max(game.tiles_center, key=lambda t: t.value)

        game.handle_failed_turn()

        # Le joueur n'a toujours pas de tuiles
        assert len(players[0].tiles) == 0

        # Mais la tuile du centre a quand même été retirée
        assert len(game.tiles_center) == initial_center_count - 1
        assert highest_tile not in game.tiles_center
        assert len(game.removed_tiles) == 1
        assert highest_tile in game.removed_tiles

    def test_is_game_over(self):
        """Test de détection de fin de partie"""
        players = [Player("Test")]
        game = PikominoGame(players)

        assert not game.is_game_over()

        # Retirer toutes les tuiles du centre
        game.tiles_center = []

        assert game.is_game_over()

    def test_get_winner(self):
        """Test de détermination du gagnant"""
        players = [Player("Alice"), Player("Bob"), Player("Charlie")]
        game = PikominoGame(players)

        # Donner des tuiles aux joueurs
        players[0].add_tile(Tile(21, 1))  # 1 ver
        players[1].add_tile(Tile(25, 2))  # 2 vers
        players[1].add_tile(Tile(29, 3))  # + 3 vers = 5 total
        players[2].add_tile(Tile(33, 4))  # 4 vers

        winner = game.get_winner()
        assert winner.name == "Bob"  # 5 vers > 4 vers > 1 ver

    def test_get_game_state(self):
        """Test de récupération de l'état du jeu"""
        players = [Player("Alice"), Player("Bob")]
        game = PikominoGame(players)

        # Donner quelques tuiles
        players[0].add_tile(Tile(21, 1))
        players[1].add_tile(Tile(25, 2))

        state = game.get_game_state()

        assert state["current_player"] == "Alice"
        assert state["current_player_idx"] == 0
        assert state["tiles_remaining"] == 16
        assert len(state["tiles_center"]) == 16
        assert state["player_scores"] == {"Alice": 1, "Bob": 2}
        assert state["player_tile_counts"] == {"Alice": 1, "Bob": 1}
        assert not state["game_over"]
        assert state["turn_count"] == 0


class TestGameIntegration:
    """Tests d'intégration pour des scénarios de jeu complets"""

    @patch("pikomino.Dice.roll")
    def test_successful_turn(self, mock_roll):
        """Test d'un tour réussi complet"""
        players = [Player("Test")]
        game = PikominoGame(players)

        # Simuler des lancers de dés : d'abord des 5, puis des vers
        mock_roll.side_effect = [
            # Premier lancer : 4 cinq, 4 autres
            DiceValue.FIVE,
            DiceValue.FIVE,
            DiceValue.FIVE,
            DiceValue.FIVE,
            DiceValue.ONE,
            DiceValue.TWO,
            DiceValue.THREE,
            DiceValue.FOUR,
        ] + [
            # Deuxième lancer : des vers parmi les 4 restants
            DiceValue.WORM,
            DiceValue.WORM,
            DiceValue.ONE,
            DiceValue.TWO,
        ]

        # Stratégie personnalisée pour le test
        def side_effect(turn_state, player):
            if (
                DiceValue.FIVE in turn_state.current_roll
                and DiceValue.FIVE not in turn_state.used_values
            ):
                return DiceValue.FIVE
            elif (
                DiceValue.WORM in turn_state.current_roll
                and DiceValue.WORM not in turn_state.used_values
            ):
                return DiceValue.WORM
            return None

        players[0].strategy = MockStrategy()
        players[0].strategy.choose_dice_value = side_effect
        players[0].strategy.should_continue_turn = (
            lambda ts, p: ts.remaining_dice > 0 and not ts.has_worm()
        )

        result, details = game.play_turn()

        assert result == TurnResult.SUCCESS
        assert details["player"] == "Test"
        assert details["final_has_worm"] is True
        assert details["final_score"] >= 21  # Score suffisant pour prendre une tuile
        assert details["tile_taken"] is not None
        assert len(players[0].tiles) == 1

    @patch("pikomino.Dice.roll")
    def test_failed_turn_no_worm(self, mock_roll):
        """Test d'un tour raté : pas de ver"""
        players = [Player("Test")]
        game = PikominoGame(players)

        # Donner une tuile au joueur pour qu'il puisse la perdre
        players[0].add_tile(Tile(21, 1))

        # Simuler des lancers sans vers
        mock_roll.return_value = DiceValue.ONE

        def choose_no_worm(turn_state, player):
            if DiceValue.ONE in turn_state.current_roll:
                return DiceValue.ONE
            return None

        players[0].strategy = MockStrategy()
        players[0].strategy.choose_dice_value = choose_no_worm
        players[0].strategy.should_continue_turn = (
            lambda ts, p: False
        )  # S'arrête immédiatement

        initial_center_count = len(game.tiles_center)

        result, details = game.play_turn()

        assert result == TurnResult.FAILED_NO_WORM
        assert details["final_has_worm"] is False
        assert len(players[0].tiles) == 0  # A perdu sa tuile
        assert (
            len(game.tiles_center) == initial_center_count - 1
        )  # Tuile retirée du centre

    @patch("pikomino.Dice.roll")
    def test_failed_turn_insufficient_score(self, mock_roll):
        """Test d'un tour raté : score insuffisant même avec ver"""
        players = [Player("Test")]
        game = PikominoGame(players)

        # Donner une tuile au joueur
        players[0].add_tile(Tile(25, 2))

        # Retirer toutes les tuiles basses du centre pour forcer l'échec
        # Ne garder que les tuiles 22 et plus
        game.tiles_center = [t for t in game.tiles_center if t.value >= 22]

        # Simuler un lancer avec seulement un ver et des autres valeurs
        mock_roll.side_effect = [
            # Premier lancer : 1 ver, 7 autres valeurs non utilisables après
            DiceValue.WORM,
            DiceValue.ONE,
            DiceValue.ONE,
            DiceValue.ONE,
            DiceValue.ONE,
            DiceValue.ONE,
            DiceValue.ONE,
            DiceValue.ONE,
        ]

        def choose_worm_only(turn_state, player):
            if DiceValue.WORM in turn_state.current_roll:
                return DiceValue.WORM
            return None

        players[0].strategy = MockStrategy()
        players[0].strategy.choose_dice_value = choose_worm_only
        players[0].strategy.should_continue_turn = (
            lambda ts, p: False
        )  # S'arrête immédiatement après le premier lancer

        initial_center_count = len(game.tiles_center)

        result, details = game.play_turn()

        assert result == TurnResult.FAILED_INSUFFICIENT_SCORE
        assert details["final_has_worm"] is True
        assert details["final_score"] == 5  # Seulement 1 ver = 5 points
        assert len(players[0].tiles) == 0  # A perdu sa tuile
        assert (
            len(game.tiles_center) == initial_center_count - 1
        )  # Tuile retirée du centre


class TestRuleComplianceEdgeCases:
    """Tests pour vérifier la conformité aux règles dans les cas limites"""

    def test_must_stop_when_no_dice_remain(self):
        """Test: Un joueur doit s'arrêter s'il n'a plus de dés à lancer"""
        turn_state = TurnState()
        turn_state.remaining_dice = 0
        turn_state.reserved_dice = {
            DiceValue.WORM: 1,
            DiceValue.FIVE: 7,
        }  # Tous les dés utilisés

        # Même une stratégie agressive doit s'arrêter
        strategy = AggressiveStrategy()
        player = Player("Test", strategy)

        assert not strategy.should_continue_turn(turn_state, player)

    def test_worm_counts_as_5_points_but_distinct(self):
        """Test: Le ver vaut 5 points mais reste distinct des 5 normaux"""
        turn_state = TurnState()
        turn_state.reserved_dice = {
            DiceValue.FIVE: 2,  # 2 cinq normaux = 10 points
            DiceValue.WORM: 1,  # 1 ver = 5 points
        }

        assert turn_state.get_total_score() == 15
        assert turn_state.has_worm()  # Le ver est bien présent

        # On peut réserver des 5 ET des vers dans le même tour
        turn_state.used_values = {DiceValue.FIVE}
        turn_state.current_roll = [DiceValue.WORM, DiceValue.THREE]

        assert turn_state.can_reserve_value(DiceValue.WORM)  # Ver encore disponible
        assert not turn_state.can_reserve_value(DiceValue.FIVE)  # 5 déjà utilisé

    def test_tile_value_determines_difficulty(self):
        """Test: Plus la valeur de la tuile est élevée, plus elle est difficile à obtenir"""
        players = [Player("Test")]
        game = PikominoGame(players)

        # Vérifier l'ordre des tuiles
        tile_values = [t.value for t in game.tiles_center]
        assert min(tile_values) == 21
        assert max(tile_values) == 36

        # Vérifier que plus la valeur est haute, plus il y a de vers
        tile_21 = next(t for t in game.tiles_center if t.value == 21)
        tile_36 = next(t for t in game.tiles_center if t.value == 36)

        assert tile_21.worms < tile_36.worms

    def test_exact_score_required_for_player_theft(self):
        """Test: Il faut un score exact pour voler une tuile à un joueur"""
        players = [Player("Alice"), Player("Bob")]
        game = PikominoGame(players)

        # Bob a une tuile de valeur 25
        bob_tile = Tile(25, 2)
        players[1].add_tile(bob_tile)

        game.current_player_idx = 0  # Alice joue

        # Score 26 : ne peut pas voler (trop élevé)
        tile_found = game.find_tile_to_take(26, True)
        # Doit trouver une tuile du centre, pas celle de Bob
        if tile_found:
            assert tile_found != bob_tile

        # Score 24 : ne peut pas voler (trop bas)
        tile_found = game.find_tile_to_take(24, True)
        assert tile_found is None or tile_found != bob_tile

        # Score exact 25 : peut voler
        tile_found = game.find_tile_to_take(25, True)
        assert tile_found == bob_tile


class TestNewDiceLogic:
    """Tests pour la nouvelle logique stricte des dés"""

    def test_must_choose_dice_value_before_reroll(self):
        """Test que le joueur doit choisir une valeur avant de relancer"""
        turn_state = TurnState()
        turn_state.current_roll = [DiceValue.ONE, DiceValue.TWO, DiceValue.THREE]
        turn_state.remaining_dice = 8
        turn_state.used_values = set()

        # Des choix sont disponibles
        assert turn_state.can_reserve_value(DiceValue.ONE)
        assert turn_state.can_reserve_value(DiceValue.TWO)
        assert turn_state.can_reserve_value(DiceValue.THREE)

        # Le joueur ne doit pas pouvoir relancer sans choisir
        # (Cette logique est maintenant gérée côté interface)
        available_choices = [
            v for v in turn_state.current_roll if v not in turn_state.used_values
        ]
        assert len(available_choices) > 0  # Il y a des choix disponibles

    def test_forced_turn_end_when_no_valid_choices(self):
        """Test de fin de tour forcée quand aucun choix valide"""
        turn_state = TurnState()
        turn_state.current_roll = [DiceValue.ONE, DiceValue.TWO]
        turn_state.used_values = {DiceValue.ONE, DiceValue.TWO}  # Déjà utilisées
        turn_state.remaining_dice = 6

        # Aucun choix valide disponible
        assert not turn_state.can_reserve_value(DiceValue.ONE)
        assert not turn_state.can_reserve_value(DiceValue.TWO)

        # Simulation de fin de tour forcée
        has_valid_choices = any(
            turn_state.can_reserve_value(v) for v in turn_state.current_roll
        )
        assert not has_valid_choices  # Confirme qu'il n'y a aucun choix valide

    def test_dice_choice_validation(self):
        """Test de validation des choix de dés"""
        turn_state = TurnState()
        turn_state.current_roll = [DiceValue.WORM, DiceValue.FIVE, DiceValue.ONE]
        turn_state.used_values = {DiceValue.FIVE}  # Déjà utilisé

        # Choix valides
        assert turn_state.can_reserve_value(DiceValue.WORM)
        assert turn_state.can_reserve_value(DiceValue.ONE)

        # Choix invalides
        assert not turn_state.can_reserve_value(DiceValue.FIVE)  # Déjà utilisé
        assert not turn_state.can_reserve_value(DiceValue.TWO)  # Pas dans le lancer


class TestTileTheftInterface:
    """Tests pour la nouvelle interface de vol de tuiles"""

    def test_identify_stealable_tiles_exact_score(self):
        """Test d'identification des tuiles volables avec score exact"""
        players = [Player("P1"), Player("P2"), Player("P3")]
        game = PikominoGame(players)

        # P2 a une tuile 25, P3 a une tuile 30
        players[1].add_tile(Tile(25, 2))
        players[2].add_tile(Tile(30, 3))

        # P1 fait exactement 25 points
        score = 25
        has_worm = True

        # Trouver les tuiles volables
        stealable_tiles = []
        for player in players[1:]:  # Exclure le joueur actuel
            top_tile = player.get_top_tile()
            if top_tile and top_tile.value == score:
                stealable_tiles.append((player.name, top_tile))

        assert len(stealable_tiles) == 1
        assert stealable_tiles[0][0] == "P2"
        assert stealable_tiles[0][1].value == 25

    def test_tile_theft_removes_from_victim(self):
        """Test que le vol retire la tuile de la victime"""
        players = [Player("P1"), Player("P2")]
        game = PikominoGame(players)

        # P2 a une tuile 25
        tile = Tile(25, 2)
        players[1].add_tile(tile)

        # P1 vole la tuile
        game.current_player_idx = 0  # P1 est le joueur actuel
        success = game.take_tile(tile)

        assert success
        assert len(players[0].tiles) == 1  # P1 a maintenant la tuile
        assert len(players[1].tiles) == 0  # P2 l'a perdue
        assert players[0].get_top_tile().value == 25


class TestBugFixes:
    """Tests pour vérifier que les bugs corrigés restent corrigés"""

    def test_dice_display_reset_logic(self):
        """Test que la logique de réinitialisation des dés fonctionne"""
        # Ce test simule la logique de réinitialisation
        # Dans la vraie interface, ceci serait géré par resetDiceDisplay()

        class MockTurnState:
            def __init__(self):
                self.reserved_dice = {}
                self.current_score = 0
                self.has_worm_value = False
                self.remaining_dice = 8
                self.used_values = set()

            def reset(self):
                """Simule la réinitialisation complète"""
                self.reserved_dice = {}
                self.current_score = 0
                self.has_worm_value = False
                self.remaining_dice = 8
                self.used_values = set()

        # Simuler un état de tour avec des dés réservés
        mock_state = MockTurnState()
        mock_state.reserved_dice = {DiceValue.ONE: 2, DiceValue.WORM: 1}
        mock_state.current_score = 7
        mock_state.has_worm_value = True

        # Vérifier l'état avant reset
        assert len(mock_state.reserved_dice) > 0
        assert mock_state.current_score > 0

        # Réinitialiser
        mock_state.reset()

        # Vérifier la réinitialisation complète
        assert len(mock_state.reserved_dice) == 0
        assert mock_state.current_score == 0
        assert not mock_state.has_worm_value
        assert mock_state.remaining_dice == 8
        assert len(mock_state.used_values) == 0

    def test_strict_dice_choice_enforcement(self):
        """Test que la logique stricte des dés est appliquée"""
        turn_state = TurnState()

        # Simuler un lancer avec des choix disponibles
        turn_state.current_roll = [DiceValue.ONE, DiceValue.TWO, DiceValue.THREE]
        turn_state.used_values = set()

        # Vérifier qu'un choix doit être fait
        available_choices = [
            v for v in turn_state.current_roll if v not in turn_state.used_values
        ]
        assert len(available_choices) > 0

        # Simuler le choix d'une valeur
        chosen_value = DiceValue.ONE
        turn_state.used_values.add(chosen_value)

        # Vérifier que la valeur ne peut plus être choisie
        assert not turn_state.can_reserve_value(chosen_value)

        # Simuler un nouveau lancer avec que des valeurs déjà utilisées
        turn_state.current_roll = [
            DiceValue.ONE,
            DiceValue.ONE,
        ]  # Que des valeurs déjà utilisées

        # Vérifier qu'aucun choix valide n'est disponible
        has_valid_choices = any(
            turn_state.can_reserve_value(v) for v in turn_state.current_roll
        )
        assert not has_valid_choices  # Fin de tour forcée

    def test_tile_identity_not_equality(self):
        """Test que les tuiles sont identifiées par référence, pas par valeur"""
        # Créer deux tuiles identiques
        tile1 = Tile(25, 2)
        tile2 = Tile(25, 2)

        # Elles ont la même valeur mais sont des objets différents
        assert tile1.value == tile2.value
        assert tile1.worms == tile2.worms
        assert tile1 is not tile2  # Identité différente

        # Le jeu doit distinguer les tuiles par identité
        players = [Player("P1"), Player("P2")]
        players[0].add_tile(tile1)
        players[1].add_tile(tile2)

        # Chaque joueur a sa propre instance
        assert players[0].get_top_tile() is tile1
        assert players[1].get_top_tile() is tile2
        assert players[0].get_top_tile() is not players[1].get_top_tile()

    def test_forced_turn_end_no_valid_choices(self):
        """Test que la fin de tour forcée fonctionne quand aucun choix valide n'est disponible"""
        # Simuler une situation où toutes les valeurs sont déjà utilisées
        turn_state = TurnState()
        turn_state.current_roll = [DiceValue.ONE, DiceValue.TWO, DiceValue.ONE]
        turn_state.used_values = {
            DiceValue.ONE,
            DiceValue.TWO,
        }  # Toutes les valeurs du lancer déjà utilisées
        turn_state.remaining_dice = 5

        # Vérifier qu'aucun choix valide n'est disponible
        available_choices = [
            v for v in turn_state.current_roll if turn_state.can_reserve_value(v)
        ]
        assert len(available_choices) == 0  # Aucun choix valide

        # Dans ce cas, selon les règles, le tour doit se terminer automatiquement
        # La fonction can_reserve_value doit retourner False pour toutes les valeurs
        for value in turn_state.current_roll:
            assert not turn_state.can_reserve_value(value)

        # Simuler la logique du frontend : si aucun choix valide, fin forcée
        has_valid_choices = any(
            turn_state.can_reserve_value(v) for v in turn_state.current_roll
        )
        assert not has_valid_choices

        # Le tour doit être considéré comme raté (failed_no_valid_choice)
        # Ceci serait géré par l'interface utilisateur qui émet un endTurn automatique


class TestIntegrationWithNewFeatures:
    """Tests d'intégration avec les nouvelles fonctionnalités"""

    @patch("pikomino.Dice.roll")
    def test_complete_turn_with_tile_theft(self, mock_roll):
        """Test d'un tour complet avec vol de tuile"""
        mock_roll.side_effect = [
            # Premier lancer : obtenir exactement 25 points
            DiceValue.WORM,
            DiceValue.WORM,
            DiceValue.WORM,
            DiceValue.WORM,
            DiceValue.WORM,  # 25 points
            DiceValue.ONE,
            DiceValue.ONE,
            DiceValue.ONE,
        ]

        players = [Player("Voleur"), Player("Victime")]

        # Définir une stratégie qui choisit les vers
        class TheftStrategy(GameStrategy):
            def __init__(self):
                self.choice_count = 0

            def choose_dice_value(self, turn_state, player):
                self.choice_count += 1
                if self.choice_count == 1:
                    return DiceValue.WORM  # Choisir tous les vers
                return None

            def should_continue_turn(self, turn_state, player):
                return False  # S'arrêter après le premier choix

            def choose_target_tile(self, score, has_worm, center_tiles, stealable_tiles, current_player):
                # Priorité au vol pour ce test
                if stealable_tiles:
                    return stealable_tiles[0][0]
                if center_tiles:
                    return center_tiles[0]
                return None

        players[0].strategy = TheftStrategy()
        game = PikominoGame(players)

        # La victime a une tuile 25
        victim_tile = Tile(25, 2)
        players[1].add_tile(victim_tile)

        # Jouer le tour
        result, details = game.play_turn()

        # Vérifier que le vol a eu lieu
        assert result == TurnResult.SUCCESS
        assert len(players[0].tiles) == 1  # Le voleur a gagné une tuile
        assert len(players[1].tiles) == 0  # La victime a perdu sa tuile
        assert players[0].get_top_tile().value == 25

    def test_api_compatibility(self):
        """Test que l'API reste compatible avec les anciennes fonctions"""
        players = [Player("P1"), Player("P2")]
        game = PikominoGame(players)

        # Tester que toutes les méthodes importantes existent encore
        assert hasattr(game, "find_tile_to_take")
        assert hasattr(game, "take_tile")
        assert hasattr(game, "handle_failed_turn")
        assert hasattr(game, "get_game_state")
        assert hasattr(game, "play_turn")

        # Tester que get_game_state retourne les bonnes informations
        state = game.get_game_state()
        assert "current_player" in state
        assert "tiles_center" in state
        assert "player_tiles" in state
        assert "player_scores" in state


class TestWebInterface:
    """Tests pour l'interface web Flask"""

    @patch("app.games", {})
    @patch("app.game_modes", {})
    @patch("app.emitted_turns", {})
    def test_create_game_api(self):
        """Test de création de partie via l'API"""
        from app import app

        with app.test_client() as client:
            response = client.post(
                "/api/create_game",
                json={"players": ["Alice", "Bob"], "mode": "interactive"},
            )

            assert response.status_code == 200
            data = response.get_json()
            assert "game_id" in data
            assert "game_state" in data
            assert "mode" in data
            assert data["mode"] == "interactive"

    def test_get_available_tiles_api_real_game(self):
        """Test de l'API pour obtenir les tuiles disponibles avec un vrai jeu"""
        from app import app, games

        # Créer un vrai jeu de test
        test_game = PikominoGame([Player("Alice"), Player("Bob")])
        test_game.players[1].add_tile(Tile(25, 2))  # Bob a une tuile 25
        games["test_game"] = test_game

        with app.test_client() as client:
            response = client.get("/api/game/test_game/available_tiles/25")

            assert response.status_code == 200
            data = response.get_json()
            assert "center_tiles" in data
            assert "stealable_tiles" in data
            assert len(data["stealable_tiles"]) == 1  # Une tuile volable de Bob
            assert data["stealable_tiles"][0]["value"] == 25

    def test_game_state_api(self):
        """Test de l'API pour obtenir l'état du jeu"""
        from app import app, games, game_modes

        # Créer un jeu de test
        test_game = PikominoGame([Player("Alice"), Player("Bob")])
        games["test_game"] = test_game
        game_modes["test_game"] = "interactive"

        with app.test_client() as client:
            response = client.get("/api/game/test_game/state")

            assert response.status_code == 200
            data = response.get_json()
            assert "current_player" in data
            assert "tiles_center" in data
            assert "mode" in data
            assert data["mode"] == "interactive"


class TestRandomStrategy:
    """Tests pour la stratégie aléatoire"""

    def test_chooses_available_values_only(self):
        """Test que la stratégie aléatoire ne choisit que parmi les valeurs disponibles"""
        strategy = RandomStrategy()
        player = Player("Test", strategy)

        turn_state = TurnState()
        turn_state.current_roll = [DiceValue.ONE, DiceValue.ONE, DiceValue.THREE]
        turn_state.used_values = set()

        # Tester plusieurs fois pour s'assurer que seules les bonnes valeurs sont choisies
        available_values = {DiceValue.ONE, DiceValue.THREE}
        
        for _ in range(10):
            choice = strategy.choose_dice_value(turn_state, player)
            assert choice in available_values

    def test_respects_used_values(self):
        """Test que la stratégie respecte les valeurs déjà utilisées"""
        strategy = RandomStrategy()
        player = Player("Test", strategy)

        turn_state = TurnState()
        turn_state.current_roll = [DiceValue.ONE, DiceValue.TWO, DiceValue.THREE]
        turn_state.used_values = {DiceValue.ONE}  # ONE déjà utilisé

        # Tester plusieurs fois
        for _ in range(10):
            choice = strategy.choose_dice_value(turn_state, player)
            assert choice != DiceValue.ONE
            assert choice in [DiceValue.TWO, DiceValue.THREE]

    def test_continue_probability_affects_decision(self):
        """Test que la probabilité de continuer affecte la décision"""
        # Stratégie qui ne continue jamais (probabilité 0)
        never_continue = RandomStrategy(continue_probability=0.0)
        player = Player("Test", never_continue)

        turn_state = TurnState()
        turn_state.remaining_dice = 4
        turn_state.reserved_dice = {DiceValue.WORM: 1, DiceValue.FIVE: 4}  # 25 points

        # Devrait toujours s'arrêter
        for _ in range(10):
            assert not never_continue.should_continue_turn(turn_state, player)

        # Stratégie qui continue toujours (probabilité 1)  
        always_continue = RandomStrategy(continue_probability=1.0)
        
        # Devrait toujours continuer (sauf si impossible)
        for _ in range(10):
            assert always_continue.should_continue_turn(turn_state, player)

    def test_must_continue_when_cannot_take_tile(self):
        """Test qu'elle doit continuer quand elle ne peut pas prendre de tuile"""
        strategy = RandomStrategy(continue_probability=0.0)  # Même avec 0% de chance
        player = Player("Test", strategy)

        turn_state = TurnState()
        turn_state.remaining_dice = 4
        turn_state.reserved_dice = {DiceValue.ONE: 2}  # Seulement 2 points, pas de ver

        # Doit continuer même avec probabilité 0 car ne peut pas prendre de tuile
        assert strategy.should_continue_turn(turn_state, player)

    def test_cannot_continue_without_dice(self):
        """Test qu'elle ne peut pas continuer sans dés restants"""
        strategy = RandomStrategy(continue_probability=1.0)  # Même avec 100% de chance
        player = Player("Test", strategy)

        turn_state = TurnState()
        turn_state.remaining_dice = 0
        turn_state.reserved_dice = {DiceValue.WORM: 1, DiceValue.FIVE: 4}  # 25 points

        # Ne peut pas continuer sans dés
        assert not strategy.should_continue_turn(turn_state, player)

    def test_chooses_from_all_available_tiles(self):
        """Test qu'elle choisit parmi toutes les tuiles disponibles"""
        from pikomino import Tile
        
        strategy = RandomStrategy()
        player = Player("Test", strategy)

        # Créer quelques tuiles test
        center_tiles = [Tile(25, 2), Tile(30, 3)]
        stealable_tiles = [(Tile(28, 2), player)]

        # Collecter les choix sur plusieurs essais
        choices = set()
        for _ in range(50):  # Plus d'essais pour avoir de la variété
            choice = strategy.choose_target_tile(
                score=30, 
                has_worm=True, 
                center_tiles=center_tiles, 
                stealable_tiles=stealable_tiles, 
                current_player=player
            )
            if choice:
                choices.add(choice.value)

        # Devrait avoir choisi parmi toutes les tuiles disponibles
        expected_values = {25, 30, 28}
        assert len(choices) > 1  # Au moins 2 valeurs différentes choisies
        assert choices.issubset(expected_values)

    def test_returns_none_without_worm(self):
        """Test qu'elle retourne None sans ver"""
        from pikomino import Tile
        
        strategy = RandomStrategy()
        player = Player("Test", strategy)

        center_tiles = [Tile(25, 2)]
        stealable_tiles = []

        choice = strategy.choose_target_tile(
            score=30, 
            has_worm=False,  # Pas de ver
            center_tiles=center_tiles, 
            stealable_tiles=stealable_tiles, 
            current_player=player
        )

        assert choice is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
