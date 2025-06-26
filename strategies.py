"""
Stratégies de jeu pour Pikomino

Ce module contient toutes les stratégies de jeu disponibles:
- GameStrategy: Interface abstraite
- ConservativeStrategy: Stratégie prudente
- AggressiveStrategy: Stratégie agressive
- BalancedStrategy: Stratégie équilibrée
- TargetedStrategy: Stratégie ciblée configurable
- RandomStrategy: Stratégie aléatoire
- OptimalStrategy: Stratégie mathématiquement optimale
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field
import random

if TYPE_CHECKING:
    from pikomino import DiceValue, Tile, Player, TurnState, TurnResult


@dataclass
class GameStateSnapshot:
    """Instantané de l'état du jeu à un moment donné"""
    turn_number: int
    current_player_name: str
    tiles_center: List[Tile]  # Tuiles disponibles dans le centre
    players_tiles: Dict[str, List[Tile]]  # Tuiles de chaque joueur
    removed_tiles: List[Tile]  # Tuiles retirées du jeu
    player_scores: Dict[str, int]  # Score (vers) de chaque joueur
    turn_details: Dict[str, Any]  # Détails du tour en cours

@dataclass 
class TurnHistory:
    """Historique d'un tour spécifique"""
    turn_number: int
    player_name: str
    dice_rolls: List[List[DiceValue]]  # Tous les lancers de dés du tour
    reserved_dice: Dict[DiceValue, int]  # Dés finalement réservés
    final_score: int
    final_has_worm: bool
    tile_taken: Optional[Tile]  # Tuile prise (si succès)
    result: TurnResult  # Résultat du tour
    game_state_before: GameStateSnapshot  # État du jeu avant le tour
    game_state_after: GameStateSnapshot   # État du jeu après le tour

@dataclass
class GameHistory:
    """Historique complet d'une partie de Pikomino"""
    turns: List[TurnHistory] = field(default_factory=list)
    game_states: List[GameStateSnapshot] = field(default_factory=list)
    
    def add_turn(self, turn: TurnHistory) -> None:
        """Ajoute un tour à l'historique"""
        self.turns.append(turn)
        self.game_states.append(turn.game_state_after)
    
    def get_player_turns(self, player_name: str) -> List[TurnHistory]:
        """Retourne tous les tours d'un joueur spécifique"""
        return [turn for turn in self.turns if turn.player_name == player_name]
    
    def get_recent_turns(self, count: int = 5) -> List[TurnHistory]:
        """Retourne les N derniers tours"""
        return self.turns[-count:] if count <= len(self.turns) else self.turns
    
    def get_player_statistics(self, player_name: str) -> Dict[str, Any]:
        """Calcule des statistiques pour un joueur"""
        player_turns = self.get_player_turns(player_name)
        if not player_turns:
            return {}
        
        successful_turns = [t for t in player_turns if t.result.value == "success"]
        failed_turns = [t for t in player_turns if t.result.value != "success"]
        
        return {
            "total_turns": len(player_turns),
            "successful_turns": len(successful_turns),
            "failed_turns": len(failed_turns),
            "success_rate": len(successful_turns) / len(player_turns) if player_turns else 0,
            "average_score_on_success": sum(t.final_score for t in successful_turns) / len(successful_turns) if successful_turns else 0,
            "tiles_taken": [t.tile_taken for t in successful_turns if t.tile_taken],
            "total_worms_gained": sum(t.tile_taken.worms for t in successful_turns if t.tile_taken)
        }


@dataclass
class GameContext:
    """Contexte complet du jeu disponible pour les stratégies"""
    # État du tour actuel
    turn_state: TurnState
    current_player: Player
    
    # État complet du jeu
    all_players: List[Player]
    tiles_center: List[Tile]  # Toutes les tuiles disponibles dans le centre
    removed_tiles: List[Tile]  # Tuiles retirées du jeu (échecs)
    
    # Informations calculées pour faciliter les décisions
    stealable_tiles: List[Tuple[Tile, Player]]  # Tuiles volables [(tuile, propriétaire)]
    available_center_tiles: List[Tile]  # Tuiles du centre accessibles avec le score actuel
    
    # Historique et statistiques
    game_history: GameHistory
    turn_number: int
    
    def get_opponent_scores(self) -> Dict[str, int]:
        """Retourne les scores des adversaires"""
        return {
            player.name: player.get_score() 
            for player in self.all_players 
            if player != self.current_player
        }
    
    def get_leading_player(self) -> Player:
        """Retourne le joueur en tête"""
        return max(self.all_players, key=lambda p: p.get_score())
    
    def is_current_player_leading(self) -> bool:
        """Vérifie si le joueur actuel est en tête"""
        return self.get_leading_player() == self.current_player
    
    def get_tiles_by_value_range(self, min_value: int, max_value: int) -> List[Tile]:
        """Retourne les tuiles du centre dans une plage de valeurs"""
        return [
            tile for tile in self.tiles_center 
            if min_value <= tile.value <= max_value
        ]


class GameStrategy(ABC):
    """Interface pour les stratégies de jeu avec accès complet aux informations"""

    @abstractmethod
    def choose_dice_value(self, context: GameContext) -> Optional[DiceValue]:
        """Choisit quelle valeur de dé réserver
        
        Args:
            context: Contexte complet du jeu incluant l'état du tour, 
                    les autres joueurs, l'historique, etc.
                    
        Returns:
            La valeur de dé à réserver ou None si aucun choix possible
        """
        pass

    @abstractmethod
    def should_continue_turn(self, context: GameContext) -> bool:
        """Décide si continuer le tour
        
        Args:
            context: Contexte complet du jeu
            
        Returns:
            True pour continuer, False pour s'arrêter
        """
        pass

    @abstractmethod
    def choose_target_tile(self, context: GameContext) -> Optional[Tile]:
        """Choisit quelle tuile cibler parmi les options disponibles
        
        Args:
            context: Contexte complet du jeu incluant les tuiles disponibles,
                    les tuiles volables, l'historique, etc.
            
        Returns:
            La tuile choisie ou None si aucune tuile acceptable
        """
        pass


class ConservativeStrategy(GameStrategy):
    """Stratégie conservatrice : s'arrête dès qu'on peut prendre une tuile"""

    def choose_dice_value(self, context: GameContext) -> Optional[DiceValue]:
        from pikomino import DiceValue
        
        turn_state = context.turn_state
        available_values = [
            v for v in turn_state.current_roll if turn_state.can_reserve_value(v)
        ]

        if not available_values:
            return None

        # Privilégier les vers si on n'en a pas encore
        if DiceValue.WORM in available_values and not turn_state.has_worm():
            return DiceValue.WORM

        # Sinon, prendre la valeur la plus fréquente
        value_counts = {}
        for value in available_values:
            value_counts[value] = turn_state.current_roll.count(value)

        return max(value_counts.keys(), key=lambda v: value_counts[v])

    def should_continue_turn(self, context: GameContext) -> bool:
        turn_state = context.turn_state
        # S'arrêter dès qu'on peut prendre une tuile (score >= 21 et a un ver)
        return not (turn_state.get_total_score() >= 21 and turn_state.has_worm())

    def choose_target_tile(self, context: GameContext) -> Optional[Tile]:
        """Stratégie conservatrice : évite les conflits, préfère le centre"""
        turn_state = context.turn_state
        if not turn_state.has_worm():
            return None
            
        # Priorité 1 : Tuiles du centre (plus sûr, pas de conflit)
        if context.available_center_tiles:
            # Prendre la tuile de valeur la plus basse accessible (sécurité)
            return min(context.available_center_tiles, key=lambda t: t.value)
        
        # Priorité 2 : Vol seulement si pas d'autre choix
        if context.stealable_tiles:
            # Choisir la tuile avec le moins de vers (moins agressive)
            return min(context.stealable_tiles, key=lambda x: x[0].worms)[0]
            
        return None


class AggressiveStrategy(GameStrategy):
    """Stratégie agressive : vise les tuiles de haute valeur"""

    def choose_dice_value(self, context: GameContext) -> Optional[DiceValue]:
        from pikomino import DiceValue
        
        turn_state = context.turn_state
        available_values = [
            v for v in turn_state.current_roll if turn_state.can_reserve_value(v)
        ]

        if not available_values:
            return None

        # Privilégier les hautes valeurs et les vers
        priority_order = [
            DiceValue.WORM,
            DiceValue.FIVE,
            DiceValue.FOUR,
            DiceValue.THREE,
            DiceValue.TWO,
            DiceValue.ONE,
        ]

        for preferred_value in priority_order:
            if preferred_value in available_values:
                return preferred_value

        return available_values[0]

    def should_continue_turn(self, context: GameContext) -> bool:
        turn_state = context.turn_state
        # Continue jusqu'à avoir au moins 30 points si possible
        return turn_state.get_total_score() < 30 and turn_state.remaining_dice > 0

    def choose_target_tile(self, context: GameContext) -> Optional[Tile]:
        """Stratégie agressive : maximise les vers et l'impact"""
        turn_state = context.turn_state
        if not turn_state.has_worm():
            return None
            
        # Priorité 1 : Vol pour maximiser l'impact (enlever des vers à l'adversaire)
        if context.stealable_tiles:
            # Choisir la tuile volable avec le plus de vers
            return max(context.stealable_tiles, key=lambda x: x[0].worms)[0]
        
        # Priorité 2 : Plus haute tuile du centre (maximum de vers)
        if context.available_center_tiles:
            # Prendre la tuile de plus haute valeur (plus de vers)
            return max(context.available_center_tiles, key=lambda t: t.value)
            
        return None


class BalancedStrategy(GameStrategy):
    """Stratégie équilibrée : adapte ses choix selon le contexte"""

    def choose_dice_value(self, context: GameContext) -> Optional[DiceValue]:
        from pikomino import DiceValue, Dice
        
        turn_state = context.turn_state
        available_values = [
            v for v in turn_state.current_roll if turn_state.can_reserve_value(v)
        ]

        if not available_values:
            return None

        # Privilégier les vers si pas encore de ver ET si on a encore beaucoup de dés
        if (DiceValue.WORM in available_values and 
            not turn_state.has_worm() and 
            turn_state.remaining_dice > 4):
            return DiceValue.WORM

        # Si peu de dés restants, privilégier les hautes valeurs
        if turn_state.remaining_dice <= 3:
            high_values = [v for v in available_values if v.value >= 4 or v == DiceValue.WORM]
            if high_values:
                return max(high_values, key=lambda v: Dice.get_point_value(v))

        # Sinon, équilibrer fréquence et valeur
        value_scores = {}
        for value in available_values:
            count = turn_state.current_roll.count(value)
            points = Dice.get_point_value(value)
            # Score = fréquence × valeur (équilibre les deux)
            value_scores[value] = count * points

        return max(value_scores.keys(), key=lambda v: value_scores[v])

    def should_continue_turn(self, context: GameContext) -> bool:
        turn_state = context.turn_state
        score = turn_state.get_total_score()

        # S'arrêter si on peut prendre une tuile et qu'on a peu de dés restants
        if score >= 21 and turn_state.has_worm() and turn_state.remaining_dice <= 2:
            return False

        # Continuer si on a encore beaucoup de dés et un score raisonnable
        if turn_state.remaining_dice >= 4 and score < 28:
            return True

        # Sinon, s'arrêter si on peut prendre une tuile
        return not (score >= 21 and turn_state.has_worm())

    def choose_target_tile(self, context: GameContext) -> Optional[Tile]:
        """Stratégie équilibrée : optimise selon la situation"""
        turn_state = context.turn_state
        if not turn_state.has_worm():
            return None
            
        # Analyser la situation actuelle
        current_player_score = context.current_player.get_score()
        opponent_scores = context.get_opponent_scores()
        max_opponent_score = max(opponent_scores.values(), default=0)
        
        # Si on est en retard, privilégier l'aggressivité (vol)
        if current_player_score < max_opponent_score:
            if context.stealable_tiles:
                # Voler la tuile avec le plus de vers
                return max(context.stealable_tiles, key=lambda x: x[0].worms)[0]
        
        # Si on est en avance, privilégier la sécurité
        if current_player_score > max_opponent_score:
            if context.available_center_tiles:
                # Prendre une tuile de valeur moyenne (équilibre sécurité/récompense)
                sorted_tiles = sorted(context.available_center_tiles, key=lambda t: t.value)
                mid_index = len(sorted_tiles) // 2
                return sorted_tiles[mid_index]
        
        # Situation équilibrée : optimiser le rapport risque/récompense
        all_options = []
        
        # Évaluer les tuiles du centre (risque faible, récompense variable)
        for tile in context.available_center_tiles:
            all_options.append((tile, tile.worms, "center"))
        
        # Évaluer les tuiles volables (risque moyen, récompense + impact)
        for tile, _ in context.stealable_tiles:
            # Bonus pour l'impact psychologique du vol
            impact_bonus = 1
            all_options.append((tile, tile.worms + impact_bonus, "steal"))
        
        if all_options:
            # Choisir l'option avec le meilleur rapport
            return max(all_options, key=lambda x: x[1])[0]
            
        return None


class TargetedStrategy(GameStrategy):
    """Stratégie ciblée : peut viser des joueurs ou tuiles spécifiques"""
    
    def __init__(self, target_player_name: Optional[str] = None, min_target_value: int = 25):
        """
        Args:
            target_player_name: Nom du joueur à cibler en priorité (None = auto)
            min_target_value: Valeur minimum des tuiles à viser
        """
        self.target_player_name = target_player_name
        self.min_target_value = min_target_value

    def choose_dice_value(self, context: GameContext) -> Optional[DiceValue]:
        from pikomino import DiceValue
        
        turn_state = context.turn_state
        available_values = [
            v for v in turn_state.current_roll if turn_state.can_reserve_value(v)
        ]

        if not available_values:
            return None

        # Si on vise une tuile haute valeur, privilégier les dés de haute valeur
        score = turn_state.get_total_score()
        if score < self.min_target_value:
            # Privilégier les vers et hautes valeurs pour atteindre l'objectif
            priority_order = [DiceValue.WORM, DiceValue.FIVE, DiceValue.FOUR]
            for value in priority_order:
                if value in available_values:
                    return value

        # Stratégie classique sinon
        value_counts = {}
        for value in available_values:
            value_counts[value] = turn_state.current_roll.count(value)

        return max(value_counts.keys(), key=lambda v: value_counts[v])

    def should_continue_turn(self, context: GameContext) -> bool:
        turn_state = context.turn_state
        score = turn_state.get_total_score()
        
        # Continuer si on n'a pas atteint notre objectif minimum
        if score < self.min_target_value and turn_state.remaining_dice > 1:
            return True
            
        # S'arrêter si on peut prendre une tuile
        return not (score >= 21 and turn_state.has_worm())

    def choose_target_tile(self, context: GameContext) -> Optional[Tile]:
        """Stratégie ciblée : priorité aux objectifs définis"""
        turn_state = context.turn_state
        if not turn_state.has_worm():
            return None
            
        # Priorité 1 : Cibler un joueur spécifique si défini
        if self.target_player_name:
            for tile, target_player in context.stealable_tiles:
                if target_player.name == self.target_player_name:
                    return tile
        
        # Priorité 2 : Cibler les tuiles de haute valeur (selon min_target_value)
        high_value_tiles = []
        
        # Tuiles volables de haute valeur
        for tile, _ in context.stealable_tiles:
            if tile.value >= self.min_target_value:
                high_value_tiles.append(tile)
        
        # Tuiles du centre de haute valeur
        for tile in context.available_center_tiles:
            if tile.value >= self.min_target_value:
                high_value_tiles.append(tile)
        
        if high_value_tiles:
            # Prendre la tuile de plus haute valeur parmi les cibles
            return max(high_value_tiles, key=lambda t: t.value)
        
        # Priorité 3 : Comportement par défaut si pas d'objectif atteint
        if context.stealable_tiles:
            return max(context.stealable_tiles, key=lambda x: x[0].worms)[0]
        
        if context.available_center_tiles:
            return max(context.available_center_tiles, key=lambda t: t.value)
            
        return None


class RandomStrategy(GameStrategy):
    """Stratégie complètement aléatoire : tous les choix sont faits au hasard"""
    
    def __init__(self, continue_probability: float = 0.5):
        """
        Args:
            continue_probability: Probabilité de continuer le tour (0.0 à 1.0)
        """
        self.continue_probability = continue_probability

    def choose_dice_value(self, context: GameContext) -> Optional[DiceValue]:
        turn_state = context.turn_state
        available_values = [
            v for v in turn_state.current_roll if turn_state.can_reserve_value(v)
        ]

        if not available_values:
            return None

        # Choix complètement aléatoire
        return random.choice(available_values)

    def should_continue_turn(self, context: GameContext) -> bool:
        turn_state = context.turn_state
        # Vérifications de base (ne peut pas continuer sans dés)
        if turn_state.remaining_dice == 0:
            return False
            
        # Si on ne peut pas encore prendre de tuile, on doit continuer
        if turn_state.get_total_score() < 21 or not turn_state.has_worm():
            return True
            
        # Choix aléatoire basé sur la probabilité configurée
        return random.random() < self.continue_probability

    def choose_target_tile(self, context: GameContext) -> Optional[Tile]:
        """Choix aléatoire de tuile parmi toutes les options disponibles"""
        turn_state = context.turn_state
        if not turn_state.has_worm():
            return None
            
        # Rassembler toutes les tuiles possibles
        all_options = []
        
        # Ajouter les tuiles du centre
        for tile in context.available_center_tiles:
            all_options.append(tile)
        
        # Ajouter les tuiles volables
        for tile, _ in context.stealable_tiles:
            all_options.append(tile)
        
        if not all_options:
            return None
            
        # Choix complètement aléatoire
        return random.choice(all_options)


class OptimalStrategy(GameStrategy):
    """
    Stratégie optimale basée sur l'analyse mathématique du jeu.
    
    Principes:
    1. Assurer un ver en priorité absolue
    2. Équilibrer fréquence × valeur avec bonus fréquence
    3. Seuils adaptatifs selon les dés restants
    4. Vol privilégié si impact double supérieur
    5. Cibler la zone de rentabilité optimale (25-32)
    6. Adaptation selon l'historique et les adversaires
    """
    
    def choose_dice_value(self, context: GameContext) -> Optional[DiceValue]:
        from pikomino import DiceValue, Dice
        
        turn_state = context.turn_state
        available_values = [
            v for v in turn_state.current_roll 
            if turn_state.can_reserve_value(v)
        ]
        
        if not available_values:
            return None
        
        # PRIORITÉ 1: Assurer un ver si pas encore obtenu (CRITIQUE)
        if DiceValue.WORM in available_values and not turn_state.has_worm():
            return DiceValue.WORM
        
        # PRIORITÉ 2: Si peu de dés restants, maximiser la valeur par dé
        if turn_state.remaining_dice <= 3:
            return max(available_values, key=lambda v: Dice.get_point_value(v))
        
        # PRIORITÉ 3: Formule optimisée avec adaptation au contexte
        scores = {}
        for value in available_values:
            count = turn_state.current_roll.count(value)
            points = Dice.get_point_value(value)
            
            # Formule de base : (fréquence × valeur) + bonus fréquence
            base_score = count * points
            frequency_bonus = (count - 1) * 0.5
            
            # Adaptation selon la position dans la partie
            position_bonus = 0
            if not context.is_current_player_leading():
                # Si on est en retard, bonus pour les hautes valeurs
                if value in [DiceValue.WORM, DiceValue.FIVE]:
                    position_bonus = 1
            
            scores[value] = base_score + frequency_bonus + position_bonus
            
        return max(scores.keys(), key=lambda v: scores[v])
    
    def should_continue_turn(self, context: GameContext) -> bool:
        turn_state = context.turn_state
        score = turn_state.get_total_score()
        
        # Contraintes de base
        if turn_state.remaining_dice == 0:
            return False
            
        if score < 21 or not turn_state.has_worm():
            return True
        
        # Adaptation selon la position dans la partie
        opponent_scores = context.get_opponent_scores()
        max_opponent_score = max(opponent_scores.values(), default=0)
        current_score = context.current_player.get_score()
        
        # Si on est très en retard, prendre plus de risques
        if current_score < max_opponent_score - 5:
            base_target = 30
        # Si on est en avance, être plus conservateur
        elif current_score > max_opponent_score + 3:
            base_target = 23
        else:
            base_target = 26
        
        # SEUILS ADAPTATIFS basés sur l'analyse optimale ET la situation
        if turn_state.remaining_dice >= 5:
            target = base_target + 2
        elif turn_state.remaining_dice >= 3:
            target = base_target
        elif turn_state.remaining_dice >= 2:
            target = base_target - 3
        else:
            # 1 dé restant : sécuriser immédiatement
            target = 21
            
        return score < target
    
    def choose_target_tile(self, context: GameContext) -> Optional[Tile]:
        """Choix optimal de tuile basé sur l'analyse d'impact et le contexte"""
        turn_state = context.turn_state
        if not turn_state.has_worm():
            return None
        
        # Analyser l'impact selon la position dans la partie
        current_score = context.current_player.get_score()
        opponent_scores = context.get_opponent_scores()
        max_opponent_score = max(opponent_scores.values(), default=0)
        is_leading = current_score >= max_opponent_score
        
        # PRIORITÉ 1: Analyser l'impact du vol vs centre avec adaptation
        if context.stealable_tiles and context.available_center_tiles:
            # Calculer le meilleur vol possible
            best_steal = max(context.stealable_tiles, key=lambda x: x[0].worms)
            steal_impact = best_steal[0].worms * 2  # Double impact
            
            # Calculer la meilleure tuile du centre
            best_center = max(context.available_center_tiles, key=lambda t: t.worms)
            center_impact = best_center.worms
            
            # Ajustement selon la position : si on est en retard, favoriser le vol
            if not is_leading:
                steal_impact *= 1.2  # Bonus aggressivité
            
            # Choisir l'option avec le meilleur impact ajusté
            if steal_impact > center_impact:
                return best_steal[0]
            else:
                return best_center
        
        # PRIORITÉ 2: Vol si pas d'alternative au centre
        elif context.stealable_tiles:
            return max(context.stealable_tiles, key=lambda x: x[0].worms)[0]
        
        # PRIORITÉ 3: Centre par défaut
        elif context.available_center_tiles:
            return max(context.available_center_tiles, key=lambda t: t.worms)
        
        return None 