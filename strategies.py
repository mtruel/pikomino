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

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
import random


class GameStrategy(ABC):
    """Interface pour les stratégies de jeu"""

    @abstractmethod
    def choose_dice_value(
        self, turn_state: "TurnState", player: "Player"
    ) -> Optional["DiceValue"]:
        """Choisit quelle valeur de dé réserver"""
        pass

    @abstractmethod
    def should_continue_turn(self, turn_state: "TurnState", player: "Player") -> bool:
        """Décide si continuer le tour"""
        pass

    @abstractmethod
    def choose_target_tile(
        self, 
        score: int, 
        has_worm: bool, 
        center_tiles: List["Tile"], 
        stealable_tiles: List[Tuple["Tile", "Player"]], 
        current_player: "Player"
    ) -> Optional["Tile"]:
        """Choisit quelle tuile cibler parmi les options disponibles
        
        Args:
            score: Score total du joueur
            has_worm: Si le joueur a au moins un ver
            center_tiles: Tuiles disponibles dans le centre
            stealable_tiles: Tuiles volables [(tuile, joueur_propriétaire)]
            current_player: Le joueur qui fait le choix
            
        Returns:
            La tuile choisie ou None si aucune tuile acceptable
        """
        pass


class ConservativeStrategy(GameStrategy):
    """Stratégie conservatrice : s'arrête dès qu'on peut prendre une tuile"""

    def choose_dice_value(
        self, turn_state: "TurnState", player: "Player"
    ) -> Optional["DiceValue"]:
        from pikomino import DiceValue
        
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

    def should_continue_turn(self, turn_state: "TurnState", player: "Player") -> bool:
        # S'arrêter dès qu'on peut prendre une tuile (score >= 21 et a un ver)
        return not (turn_state.get_total_score() >= 21 and turn_state.has_worm())

    def choose_target_tile(
        self, 
        score: int, 
        has_worm: bool, 
        center_tiles: List["Tile"], 
        stealable_tiles: List[Tuple["Tile", "Player"]], 
        current_player: "Player"
    ) -> Optional["Tile"]:
        """Stratégie conservatrice : évite les conflits, préfère le centre"""
        if not has_worm:
            return None
            
        # Priorité 1 : Tuiles du centre (plus sûr, pas de conflit)
        if center_tiles:
            # Prendre la tuile de valeur la plus basse accessible (sécurité)
            return min(center_tiles, key=lambda t: t.value)
        
        # Priorité 2 : Vol seulement si pas d'autre choix
        if stealable_tiles:
            # Choisir la tuile avec le moins de vers (moins agressive)
            return min(stealable_tiles, key=lambda x: x[0].worms)[0]
            
        return None


class AggressiveStrategy(GameStrategy):
    """Stratégie agressive : vise les tuiles de haute valeur"""

    def choose_dice_value(
        self, turn_state: "TurnState", player: "Player"
    ) -> Optional["DiceValue"]:
        from pikomino import DiceValue
        
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

    def should_continue_turn(self, turn_state: "TurnState", player: "Player") -> bool:
        # Continue jusqu'à avoir au moins 30 points si possible
        return turn_state.get_total_score() < 30 and turn_state.remaining_dice > 0

    def choose_target_tile(
        self, 
        score: int, 
        has_worm: bool, 
        center_tiles: List["Tile"], 
        stealable_tiles: List[Tuple["Tile", "Player"]], 
        current_player: "Player"
    ) -> Optional["Tile"]:
        """Stratégie agressive : maximise les vers et l'impact"""
        if not has_worm:
            return None
            
        # Priorité 1 : Vol pour maximiser l'impact (enlever des vers à l'adversaire)
        if stealable_tiles:
            # Choisir la tuile volable avec le plus de vers
            return max(stealable_tiles, key=lambda x: x[0].worms)[0]
        
        # Priorité 2 : Plus haute tuile du centre (maximum de vers)
        if center_tiles:
            # Prendre la tuile de plus haute valeur (plus de vers)
            return max(center_tiles, key=lambda t: t.value)
            
        return None


class BalancedStrategy(GameStrategy):
    """Stratégie équilibrée : adapte ses choix selon le contexte"""

    def choose_dice_value(
        self, turn_state: "TurnState", player: "Player"
    ) -> Optional["DiceValue"]:
        from pikomino import DiceValue, Dice
        
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

    def should_continue_turn(self, turn_state: "TurnState", player: "Player") -> bool:
        score = turn_state.get_total_score()

        # S'arrêter si on peut prendre une tuile et qu'on a peu de dés restants
        if score >= 21 and turn_state.has_worm() and turn_state.remaining_dice <= 2:
            return False

        # Continuer si on a encore beaucoup de dés et un score raisonnable
        if turn_state.remaining_dice >= 4 and score < 28:
            return True

        # Sinon, s'arrêter si on peut prendre une tuile
        return not (score >= 21 and turn_state.has_worm())

    def choose_target_tile(
        self, 
        score: int, 
        has_worm: bool, 
        center_tiles: List["Tile"], 
        stealable_tiles: List[Tuple["Tile", "Player"]], 
        current_player: "Player"
    ) -> Optional["Tile"]:
        """Stratégie équilibrée : optimise selon la situation"""
        if not has_worm:
            return None
            
        # Analyser la situation actuelle
        current_player_score = current_player.get_score()
        
        # Calculer le score des adversaires (on a besoin d'accès aux autres joueurs)
        # Pour l'instant, on utilise les tuiles volables comme proxy des adversaires
        opponent_scores = [tile.worms for tile, _ in stealable_tiles] if stealable_tiles else [0]
        max_opponent_score = max(opponent_scores, default=0)
        
        # Si on est en retard, privilégier l'aggressivité (vol)
        if current_player_score < max_opponent_score:
            if stealable_tiles:
                # Voler la tuile avec le plus de vers
                return max(stealable_tiles, key=lambda x: x[0].worms)[0]
        
        # Si on est en avance, privilégier la sécurité
        if current_player_score > max_opponent_score:
            if center_tiles:
                # Prendre une tuile de valeur moyenne (équilibre sécurité/récompense)
                sorted_tiles = sorted(center_tiles, key=lambda t: t.value)
                mid_index = len(sorted_tiles) // 2
                return sorted_tiles[mid_index]
        
        # Situation équilibrée : optimiser le rapport risque/récompense
        all_options = []
        
        # Évaluer les tuiles du centre (risque faible, récompense variable)
        for tile in center_tiles:
            all_options.append((tile, tile.worms, "center"))
        
        # Évaluer les tuiles volables (risque moyen, récompense + impact)
        for tile, _ in stealable_tiles:
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

    def choose_dice_value(
        self, turn_state: "TurnState", player: "Player"
    ) -> Optional["DiceValue"]:
        from pikomino import DiceValue
        
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

    def should_continue_turn(self, turn_state: "TurnState", player: "Player") -> bool:
        score = turn_state.get_total_score()
        
        # Continuer si on n'a pas atteint notre objectif minimum
        if score < self.min_target_value and turn_state.remaining_dice > 1:
            return True
            
        # S'arrêter si on peut prendre une tuile
        return not (score >= 21 and turn_state.has_worm())

    def choose_target_tile(
        self, 
        score: int, 
        has_worm: bool, 
        center_tiles: List["Tile"], 
        stealable_tiles: List[Tuple["Tile", "Player"]], 
        current_player: "Player"
    ) -> Optional["Tile"]:
        """Stratégie ciblée : priorité aux objectifs définis"""
        if not has_worm:
            return None
            
        # Priorité 1 : Cibler un joueur spécifique si défini
        if self.target_player_name:
            for tile, target_player in stealable_tiles:
                if target_player.name == self.target_player_name:
                    return tile
        
        # Priorité 2 : Cibler les tuiles de haute valeur (selon min_target_value)
        high_value_tiles = []
        
        # Tuiles volables de haute valeur
        for tile, _ in stealable_tiles:
            if tile.value >= self.min_target_value:
                high_value_tiles.append(tile)
        
        # Tuiles du centre de haute valeur
        for tile in center_tiles:
            if tile.value >= self.min_target_value:
                high_value_tiles.append(tile)
        
        if high_value_tiles:
            # Prendre la tuile de plus haute valeur parmi les cibles
            return max(high_value_tiles, key=lambda t: t.value)
        
        # Priorité 3 : Comportement par défaut si pas d'objectif atteint
        if stealable_tiles:
            return max(stealable_tiles, key=lambda x: x[0].worms)[0]
        
        if center_tiles:
            return max(center_tiles, key=lambda t: t.value)
            
        return None


class RandomStrategy(GameStrategy):
    """Stratégie complètement aléatoire : tous les choix sont faits au hasard"""
    
    def __init__(self, continue_probability: float = 0.5):
        """
        Args:
            continue_probability: Probabilité de continuer le tour (0.0 à 1.0)
        """
        self.continue_probability = continue_probability

    def choose_dice_value(
        self, turn_state: "TurnState", player: "Player"
    ) -> Optional["DiceValue"]:
        available_values = [
            v for v in turn_state.current_roll if turn_state.can_reserve_value(v)
        ]

        if not available_values:
            return None

        # Choix complètement aléatoire
        return random.choice(available_values)

    def should_continue_turn(self, turn_state: "TurnState", player: "Player") -> bool:
        # Vérifications de base (ne peut pas continuer sans dés)
        if turn_state.remaining_dice == 0:
            return False
            
        # Si on ne peut pas encore prendre de tuile, on doit continuer
        if turn_state.get_total_score() < 21 or not turn_state.has_worm():
            return True
            
        # Choix aléatoire basé sur la probabilité configurée
        return random.random() < self.continue_probability

    def choose_target_tile(
        self, 
        score: int, 
        has_worm: bool, 
        center_tiles: List["Tile"], 
        stealable_tiles: List[Tuple["Tile", "Player"]], 
        current_player: "Player"
    ) -> Optional["Tile"]:
        """Choix aléatoire de tuile parmi toutes les options disponibles"""
        if not has_worm:
            return None
            
        # Rassembler toutes les tuiles possibles
        all_options = []
        
        # Ajouter les tuiles du centre
        for tile in center_tiles:
            all_options.append(tile)
        
        # Ajouter les tuiles volables
        for tile, _ in stealable_tiles:
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
    """
    
    def choose_dice_value(self, turn_state: "TurnState", player: "Player") -> Optional["DiceValue"]:
        from pikomino import DiceValue, Dice
        
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
        
        # PRIORITÉ 3: Formule optimisée fréquence × valeur + bonus
        scores = {}
        for value in available_values:
            count = turn_state.current_roll.count(value)
            points = Dice.get_point_value(value)
            
            # Formule optimale : (fréquence × valeur) + bonus fréquence
            # Le bonus fréquence favorise les grappes de dés identiques
            base_score = count * points
            frequency_bonus = (count - 1) * 0.5  # Bonus pour fréquence élevée
            
            scores[value] = base_score + frequency_bonus
            
        return max(scores.keys(), key=lambda v: scores[v])
    
    def should_continue_turn(self, turn_state: "TurnState", player: "Player") -> bool:
        score = turn_state.get_total_score()
        
        # Contraintes de base
        if turn_state.remaining_dice == 0:
            return False
            
        if score < 21 or not turn_state.has_worm():
            return True
        
        # SEUILS ADAPTATIFS basés sur l'analyse optimale
        # Plus on a de dés, plus on peut viser haut
        if turn_state.remaining_dice >= 5:
            # Beaucoup de dés : viser la zone optimale (25-32)
            target = 28  
        elif turn_state.remaining_dice >= 3:
            # Dés moyens : seuil conservateur mais rentable
            target = 25  
        elif turn_state.remaining_dice >= 2:
            # Peu de dés : sécurité tout en gardant une ambition modérée
            target = 23
        else:
            # 1 dé restant : sécuriser immédiatement
            target = 21
            
        return score < target
    
    def choose_target_tile(
        self, 
        score: int, 
        has_worm: bool, 
        center_tiles: List["Tile"], 
        stealable_tiles: List[Tuple["Tile", "Player"]], 
        current_player: "Player"
    ) -> Optional["Tile"]:
        """Choix optimal de tuile basé sur l'analyse d'impact"""
        if not has_worm:
            return None
        
        # PRIORITÉ 1: Analyser l'impact du vol vs centre
        if stealable_tiles and center_tiles:
            # Calculer le meilleur vol possible
            best_steal = max(stealable_tiles, key=lambda x: x[0].worms)
            steal_impact = best_steal[0].worms * 2  # Double impact (gain + perte adversaire)
            
            # Calculer la meilleure tuile du centre
            best_center = max(center_tiles, key=lambda t: t.worms)
            center_impact = best_center.worms  # Simple gain
            
            # Choisir l'option avec le meilleur impact
            if steal_impact > center_impact:
                return best_steal[0]
            else:
                return best_center
        
        # PRIORITÉ 2: Vol si pas d'alternative au centre
        elif stealable_tiles:
            return max(stealable_tiles, key=lambda x: x[0].worms)[0]
        
        # PRIORITÉ 3: Centre par défaut
        elif center_tiles:
            return max(center_tiles, key=lambda t: t.worms)
        
        return None 