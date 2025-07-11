from enum import Enum
from typing import List, Optional, Dict, Tuple
import random
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


class DiceValue(Enum):
    """Représente les valeurs possibles sur un dé Pikomino"""

    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    WORM = 6  # Le symbole "ver" vaut 5 points mais est distinct


@dataclass
class Dice:
    """Représente un dé du jeu Pikomino"""

    @staticmethod
    def roll() -> DiceValue:
        """Lance un dé et retourne sa valeur"""
        return random.choice(list(DiceValue))

    @staticmethod
    def get_point_value(value: DiceValue) -> int:
        """Retourne la valeur en points d'une face de dé"""
        if value == DiceValue.WORM:
            return 5
        return value.value


@dataclass
class Tile:
    """Représente une tuile Pikomino"""

    value: int  # Valeur nécessaire pour prendre la tuile
    worms: int  # Nombre de vers sur la tuile

    def __post_init__(self):
        """Initialise les tuiles selon les règles du jeu"""
        # Les vraies valeurs des tuiles Pikomino (21-36)
        # avec le nombre de vers correspondant
        worm_mapping = {
            21: 1,
            22: 1,
            23: 1,
            24: 1,
            25: 2,
            26: 2,
            27: 2,
            28: 2,
            29: 3,
            30: 3,
            31: 3,
            32: 3,
            33: 4,
            34: 4,
            35: 4,
            36: 4,
        }
        if self.value in worm_mapping:
            self.worms = worm_mapping[self.value]


class TurnResult(Enum):
    """Résultats possibles d'un tour"""

    SUCCESS = "success"
    FAILED_NO_WORM = "failed_no_worm"
    FAILED_INSUFFICIENT_SCORE = "failed_insufficient_score"
    FAILED_NO_VALID_CHOICE = "failed_no_valid_choice"


@dataclass
class TurnState:
    """État d'un tour en cours"""

    remaining_dice: int = 8
    reserved_dice: Dict[DiceValue, int] = field(default_factory=dict)
    used_values: set = field(default_factory=set)
    current_roll: List[DiceValue] = field(default_factory=list)

    def get_total_score(self) -> int:
        """Calcule le score total des dés réservés"""
        return sum(
            Dice.get_point_value(value) * count
            for value, count in self.reserved_dice.items()
        )

    def has_worm(self) -> bool:
        """Vérifie si au moins un ver a été réservé"""
        return DiceValue.WORM in self.reserved_dice

    def can_reserve_value(self, value: DiceValue) -> bool:
        """Vérifie si une valeur peut être réservée"""
        return value in self.current_roll and value not in self.used_values


# Import des stratégies depuis le module dédié
from strategies import GameStrategy, GameHistory, GameContext, GameStateSnapshot, TurnHistory


class Player:
    """Représente un joueur"""

    def __init__(self, name: str, strategy: Optional[GameStrategy] = None):
        self.name = name
        self.tiles: List[Tile] = []
        self.strategy = strategy

    def get_score(self) -> int:
        """Calcule le score total du joueur (nombre de vers)"""
        return sum(tile.worms for tile in self.tiles)

    def get_top_tile(self) -> Optional[Tile]:
        """Retourne la tuile du dessus de la pile du joueur"""
        return self.tiles[-1] if self.tiles else None

    def add_tile(self, tile: Tile):
        """Ajoute une tuile à la pile du joueur"""
        self.tiles.append(tile)

    def remove_top_tile(self) -> Optional[Tile]:
        """Retire et retourne la tuile du dessus"""
        return self.tiles.pop() if self.tiles else None

    def choose_dice_value(self, context: GameContext) -> Optional[DiceValue]:
        """Choisit une valeur de dé à réserver"""
        if self.strategy:
            return self.strategy.choose_dice_value(context)

        # Stratégie par défaut : choisir la valeur la plus fréquente
        turn_state = context.turn_state
        available_values = [
            v for v in turn_state.current_roll if turn_state.can_reserve_value(v)
        ]

        if not available_values:
            return None

        # Compter les occurrences de chaque valeur
        value_counts = {}
        for value in available_values:
            value_counts[value] = turn_state.current_roll.count(value)

        # Choisir la valeur avec le plus d'occurrences
        return max(value_counts.keys(), key=lambda v: value_counts[v])

    def should_continue_turn(self, context: GameContext) -> bool:
        """Décide si continuer le tour ou s'arrêter"""
        if self.strategy:
            return self.strategy.should_continue_turn(context)

        # Stratégie par défaut : s'arrêter si on a au moins 25 points
        return context.turn_state.get_total_score() < 25


class PikominoGame:
    """Classe principale pour gérer une partie de Pikomino"""

    def __init__(self, players: List[Player]):
        self.players = players
        self.current_player_idx = 0
        self.tiles_center = self._initialize_tiles()
        self.removed_tiles: List[Tile] = []
        self.game_over = False
        self.turn_history: List[Dict] = []  # Ancienne structure (pour compatibilité)
        self.game_history = GameHistory()  # Nouvel historique structuré
        self.turn_number = 0

    def _initialize_tiles(self) -> List[Tile]:
        """Initialise les tuiles du centre"""
        tiles = []
        for value in range(21, 37):  # Tuiles 21 à 36
            tile = Tile(value, 0)  # Le post_init calculera les vers
            tiles.append(tile)
        return tiles

    def get_current_player(self) -> Player:
        """Retourne le joueur actuel"""
        return self.players[self.current_player_idx]

    def next_player(self):
        """Passe au joueur suivant"""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def get_available_tiles(self) -> List[Tile]:
        """Retourne les tuiles disponibles dans le centre"""
        return [tile for tile in self.tiles_center if tile is not None]

    def can_take_tile(self, tile_value: int, score: int, has_worm: bool) -> bool:
        """Vérifie si on peut prendre une tuile donnée"""
        return has_worm and score >= tile_value

    def _create_game_state_snapshot(self, turn_details: Dict = None) -> GameStateSnapshot:
        """Crée un instantané de l'état du jeu"""
        return GameStateSnapshot(
            turn_number=self.turn_number,
            current_player_name=self.get_current_player().name,
            tiles_center=list(self.tiles_center),  # Copie des tuiles du centre
            players_tiles={p.name: list(p.tiles) for p in self.players},  # Copie des tuiles des joueurs
            removed_tiles=list(self.removed_tiles),  # Copie des tuiles retirées
            player_scores={p.name: p.get_score() for p in self.players},
            turn_details=turn_details or {}
        )

    def _build_game_context(self, turn_state: TurnState) -> GameContext:
        """Construit le contexte complet du jeu pour les stratégies"""
        current_player = self.get_current_player()
        score = turn_state.get_total_score()
        
        # Calculer les tuiles volables (score exact)
        stealable_tiles = []
        for player in self.players:
            if player != current_player:
                top_tile = player.get_top_tile()
                if top_tile and top_tile.value == score:
                    stealable_tiles.append((top_tile, player))

        # Calculer les tuiles du centre accessibles (score >= valeur tuile)
        available_center_tiles = [t for t in self.tiles_center if t.value <= score]

        return GameContext(
            turn_state=turn_state,
            current_player=current_player,
            all_players=list(self.players),
            tiles_center=list(self.tiles_center),
            removed_tiles=list(self.removed_tiles),
            stealable_tiles=stealable_tiles,
            available_center_tiles=available_center_tiles,
            game_history=self.game_history,
            turn_number=self.turn_number
        )

    def find_tile_to_take(self, score: int, has_worm: bool, turn_state: TurnState) -> Optional[Tile]:
        """Trouve la meilleure tuile à prendre avec le score donné"""
        if not has_worm:
            return None

        current_player = self.get_current_player()
        
        # Si le joueur a une stratégie, utiliser le nouveau système
        if current_player.strategy:
            context = self._build_game_context(turn_state)
            return current_player.strategy.choose_target_tile(context)

        # Comportement par défaut (code original)
        # Rassembler toutes les tuiles volables (score exact)
        stealable_tiles = []
        for player in self.players:
            if player != current_player:
                top_tile = player.get_top_tile()
                if top_tile and top_tile.value == score:
                    stealable_tiles.append((top_tile, player))

        # Rassembler les tuiles du centre accessibles (score >= valeur tuile)
        center_tiles = [t for t in self.tiles_center if t.value <= score]

        # Comportement par défaut : priorité au vol, sinon plus haute tuile du centre
        if stealable_tiles:
            # Choisir la tuile volable avec le plus de vers
            return max(stealable_tiles, key=lambda x: x[0].worms)[0]

        if center_tiles:
            # Prendre la tuile de plus haute valeur possible
            return max(center_tiles, key=lambda t: t.value)

        return None

    def take_tile(self, tile: Tile) -> bool:
        """Prend une tuile et l'attribue au joueur actuel"""
        current_player = self.get_current_player()

        # D'abord vérifier si la tuile est chez un autre joueur (comparaison par référence)
        for player in self.players:
            if player != current_player:
                top_tile = player.get_top_tile()
                if top_tile is tile:
                    removed_tile = player.remove_top_tile()
                    current_player.add_tile(removed_tile)
                    return True

        # Sinon vérifier si la tuile est dans le centre (comparaison par référence aussi)
        for i, center_tile in enumerate(self.tiles_center):
            if center_tile is tile:
                self.tiles_center.remove(center_tile)
                current_player.add_tile(center_tile)
                return True

        return False

    def handle_failed_turn(self):
        """Gère un tour raté"""
        current_player = self.get_current_player()

        # Le joueur perd sa tuile du dessus
        lost_tile = current_player.remove_top_tile()
        if lost_tile:
            self.removed_tiles.append(lost_tile)

        # Retirer la tuile la plus haute du centre
        if self.tiles_center:
            highest_tile = max(self.tiles_center, key=lambda t: t.value)
            self.tiles_center.remove(highest_tile)
            self.removed_tiles.append(highest_tile)

    def play_turn(self) -> Tuple[TurnResult, Dict]:
        """Joue un tour complet pour le joueur actuel et retourne le résultat avec les détails"""
        current_player = self.get_current_player()
        turn_state = TurnState()
        self.turn_number += 1
        
        # Créer l'état du jeu avant le tour
        game_state_before = self._create_game_state_snapshot()
        
        turn_details = {
            "player": current_player.name,
            "rolls": [],
            "final_score": 0,
            "final_has_worm": False,
            "tile_taken": None,
            "result": None,
        }

        dice_rolls = []  # Pour l'historique structuré

        while turn_state.remaining_dice > 0:
            # Lancer les dés
            turn_state.current_roll = [
                Dice.roll() for _ in range(turn_state.remaining_dice)
            ]
            dice_rolls.append(list(turn_state.current_roll))  # Copie pour l'historique
            
            turn_details["rolls"].append(
                {
                    "dice": [dice.name for dice in turn_state.current_roll],
                    "remaining": turn_state.remaining_dice,
                }
            )

            # Construire le contexte et le joueur choisit une valeur
            context = self._build_game_context(turn_state)
            chosen_value = current_player.choose_dice_value(context)

            if chosen_value is None or not turn_state.can_reserve_value(chosen_value):
                # Aucune valeur valide disponible
                self.handle_failed_turn()
                turn_details["result"] = TurnResult.FAILED_NO_VALID_CHOICE
                self.turn_history.append(turn_details)
                
                # Créer l'entrée d'historique structuré
                game_state_after = self._create_game_state_snapshot(turn_details)
                turn_history_entry = TurnHistory(
                    turn_number=self.turn_number,
                    player_name=current_player.name,
                    dice_rolls=dice_rolls,
                    reserved_dice=turn_state.reserved_dice,
                    final_score=turn_state.get_total_score(),
                    final_has_worm=turn_state.has_worm(),
                    tile_taken=None,
                    result=TurnResult.FAILED_NO_VALID_CHOICE,
                    game_state_before=game_state_before,
                    game_state_after=game_state_after
                )
                self.game_history.add_turn(turn_history_entry)
                
                return TurnResult.FAILED_NO_VALID_CHOICE, turn_details

            # Réserver tous les dés de cette valeur
            count = turn_state.current_roll.count(chosen_value)
            turn_state.reserved_dice[chosen_value] = (
                turn_state.reserved_dice.get(chosen_value, 0) + count
            )
            turn_state.used_values.add(chosen_value)
            turn_state.remaining_dice -= count

            turn_details["rolls"][-1]["chosen_value"] = chosen_value.name
            turn_details["rolls"][-1]["chosen_count"] = count

            # Vérifier si le joueur veut continuer
            if turn_state.remaining_dice > 0:
                context = self._build_game_context(turn_state)
                if not current_player.should_continue_turn(context):
                    break

        # Fin du tour : essayer de prendre une tuile
        score = turn_state.get_total_score()
        has_worm = turn_state.has_worm()

        turn_details["final_score"] = score
        turn_details["final_has_worm"] = has_worm
        turn_details["reserved_dice"] = {
            k.name: v for k, v in turn_state.reserved_dice.items()
        }

        if not has_worm:
            self.handle_failed_turn()
            turn_details["result"] = TurnResult.FAILED_NO_WORM
            self.turn_history.append(turn_details)
            
            # Créer l'entrée d'historique structuré
            game_state_after = self._create_game_state_snapshot(turn_details)
            turn_history_entry = TurnHistory(
                turn_number=self.turn_number,
                player_name=current_player.name,
                dice_rolls=dice_rolls,
                reserved_dice=turn_state.reserved_dice,
                final_score=score,
                final_has_worm=has_worm,
                tile_taken=None,
                result=TurnResult.FAILED_NO_WORM,
                game_state_before=game_state_before,
                game_state_after=game_state_after
            )
            self.game_history.add_turn(turn_history_entry)
            
            return TurnResult.FAILED_NO_WORM, turn_details

        tile_to_take = self.find_tile_to_take(score, has_worm, turn_state)
        if tile_to_take is None:
            self.handle_failed_turn()
            turn_details["result"] = TurnResult.FAILED_INSUFFICIENT_SCORE
            self.turn_history.append(turn_details)
            
            # Créer l'entrée d'historique structuré
            game_state_after = self._create_game_state_snapshot(turn_details)
            turn_history_entry = TurnHistory(
                turn_number=self.turn_number,
                player_name=current_player.name,
                dice_rolls=dice_rolls,
                reserved_dice=turn_state.reserved_dice,
                final_score=score,
                final_has_worm=has_worm,
                tile_taken=None,
                result=TurnResult.FAILED_INSUFFICIENT_SCORE,
                game_state_before=game_state_before,
                game_state_after=game_state_after
            )
            self.game_history.add_turn(turn_history_entry)
            
            return TurnResult.FAILED_INSUFFICIENT_SCORE, turn_details

        self.take_tile(tile_to_take)
        turn_details["tile_taken"] = {
            "value": tile_to_take.value,
            "worms": tile_to_take.worms,
        }
        turn_details["result"] = TurnResult.SUCCESS
        self.turn_history.append(turn_details)
        
        # Créer l'entrée d'historique structuré
        game_state_after = self._create_game_state_snapshot(turn_details)
        turn_history_entry = TurnHistory(
            turn_number=self.turn_number,
            player_name=current_player.name,
            dice_rolls=dice_rolls,
            reserved_dice=turn_state.reserved_dice,
            final_score=score,
            final_has_worm=has_worm,
            tile_taken=tile_to_take,
            result=TurnResult.SUCCESS,
            game_state_before=game_state_before,
            game_state_after=game_state_after
        )
        self.game_history.add_turn(turn_history_entry)
        
        return TurnResult.SUCCESS, turn_details

    def is_game_over(self) -> bool:
        """Vérifie si la partie est terminée"""
        return len(self.tiles_center) == 0

    def get_winner(self) -> Player:
        """Retourne le joueur gagnant"""
        return max(self.players, key=lambda p: p.get_score())

    def play_game(self) -> Player:
        """Joue une partie complète et retourne le gagnant"""
        while not self.is_game_over():
            self.play_turn()
            self.next_player()

        return self.get_winner()

    def get_game_state(self) -> Dict:
        """Retourne l'état actuel du jeu"""
        return {
            "current_player": self.get_current_player().name,
            "current_player_idx": self.current_player_idx,
            "tiles_remaining": len(self.tiles_center),
            "tiles_center": [
                {"value": t.value, "worms": t.worms} for t in self.tiles_center
            ],
            "player_scores": {p.name: p.get_score() for p in self.players},
            "player_tiles": {
                p.name: [{"value": t.value, "worms": t.worms} for t in p.tiles]
                for p in self.players
            },
            "player_tile_counts": {p.name: len(p.tiles) for p in self.players},
            "game_over": self.is_game_over(),
            "turn_count": len(self.turn_history),
            "turn_number": self.turn_number,
        }


def simulate_game(
    player_names: List[str], strategies: List[GameStrategy] = None
) -> Dict:
    """Simule une partie avec les joueurs et stratégies donnés"""
    if strategies is None:
        from strategies import ConservativeStrategy
        strategies = [ConservativeStrategy() for _ in player_names]

    players = [
        Player(name, strategy) for name, strategy in zip(player_names, strategies)
    ]
    game = PikominoGame(players)

    winner = game.play_game()

    return {
        "winner": winner.name,
        "final_scores": {p.name: p.get_score() for p in players},
        "final_tiles": {p.name: len(p.tiles) for p in players},
    }
