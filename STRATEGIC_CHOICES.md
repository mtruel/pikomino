# 🧠 Choix Stratégiques dans Pikomino

## 📋 Résumé des Actions avec Choix

D'après les règles du jeu et l'implémentation, voici **tous les choix stratégiques** possibles pour un joueur :

### 1. 🎲 **Choix de Valeur de Dé** (obligatoire à chaque lancer)
**Méthode**: `choose_dice_value(turn_state, player) -> DiceValue`

**Options disponibles** :
- `ONE` (1 point)
- `TWO` (2 points) 
- `THREE` (3 points)
- `FOUR` (4 points)
- `FIVE` (5 points)
- `WORM` (5 points + obligatoire pour prendre une tuile)

**Contraintes** :
- Doit choisir une valeur présente sur au moins un dé du lancer actuel
- Ne peut pas choisir une valeur déjà réservée dans ce tour
- Réserve TOUS les dés de cette valeur

**Choix stratégiques possibles** :
- **Fréquence vs Valeur** : Prendre 3 dés "1" ou 1 dé "5" ?
- **Sécurité vs Optimisation** : Assurer un ver rapidement ou maximiser les points ?
- **Adaptation au contexte** : Choisir selon le nombre de dés restants

### 2. ⏹️ **Décision de Continuer/Arrêter** (après chaque choix de dé)
**Méthode**: `should_continue_turn(turn_state, player) -> bool`

**Options** :
- `True` : Continuer à lancer les dés restants
- `False` : S'arrêter et essayer de prendre une tuile

**Choix stratégiques possibles** :
- **Gestion du risque** : Sécuriser une tuile vs viser plus haut
- **Adaptation au score** : S'arrêter à 21+ ou continuer jusqu'à 30+ ?
- **Considération des dés restants** : Plus de risque avec peu de dés

### 3. 🎯 **Choix de Tuile Cible** (nouveau !)
**Méthode**: `choose_target_tile(score, has_worm, center_tiles, stealable_tiles, current_player) -> Tile`

**Options disponibles** :
- **Tuiles du centre** : Score ≥ valeur tuile (sécurisé)
- **Tuiles volables** : Score = valeur exacte chez un adversaire (impact)

**Choix stratégiques possibles** :
- **Vol vs Sécurité** : Voler chez un adversaire ou prendre au centre ?
- **Valeur vs Facilité** : Viser les hautes tuiles ou assurer le coup ?
- **Ciblage tactique** : Viser des joueurs spécifiques ou des tuiles particulières ?

## 🎯 Stratégies Implémentées

### `ConservativeStrategy` 🛡️
**Philosophie** : Éviter les risques, assurer les gains

**Choix de dé** :
- Privilégie les vers si pas encore obtenu
- Sinon, choisit la valeur la plus fréquente

**Timing d'arrêt** :
- S'arrête dès que possible (21+ points + ver)

**Choix de tuile** :
- Priorité au centre (plus sûr)
- Prend la tuile de plus BASSE valeur accessible (sécurité)
- Vol uniquement si pas d'autre choix

### `AggressiveStrategy` ⚔️
**Philosophie** : Maximiser les gains, accepter les risques

**Choix de dé** :
- Priorité aux hautes valeurs : WORM > 5 > 4 > 3 > 2 > 1

**Timing d'arrêt** :
- Continue jusqu'à 30+ points si possible

**Choix de tuile** :
- Priorité au vol (impact psychologique + retirer des vers à l'adversaire)
- Choisit la tuile volable avec le PLUS de vers
- Sinon, prend la tuile de plus HAUTE valeur au centre

### `BalancedStrategy` ⚖️
**Philosophie** : Adapter selon le contexte

**Choix de dé** :
- Vers si pas encore obtenu ET beaucoup de dés restants
- Hautes valeurs si peu de dés restants
- Équilibre fréquence × valeur sinon

**Timing d'arrêt** :
- S'arrête si tuile possible + peu de dés restants
- Continue si beaucoup de dés + score < 28
- Sinon, s'arrête dès que possible

**Choix de tuile** :
- En retard : privilégie le vol (aggressivité)
- En avance : privilégie la sécurité (centre)
- Équilibré : optimise le rapport vers/risque

### `TargetedStrategy` 🎯
**Philosophie** : Viser des objectifs spécifiques

**Paramètres configurables** :
- `target_player_name` : Joueur à cibler prioritairement
- `min_target_value` : Valeur minimum des tuiles visées

**Choix de dé** :
- Privilégie les hautes valeurs pour atteindre l'objectif
- Adapte selon la distance à l'objectif

**Timing d'arrêt** :
- Continue si pas encore atteint l'objectif minimum
- S'arrête dès que possible sinon

**Choix de tuile** :
- Priorité 1 : Cibler le joueur spécifié
- Priorité 2 : Cibler les tuiles ≥ valeur minimum
- Priorité 3 : Comportement par défaut

### `RandomStrategy` 🎲
**Philosophie** : Choix complètement aléatoires (baseline/test)

**Paramètres configurables** :
- `continue_probability` : Probabilité de continuer le tour (0.0 à 1.0)

**Choix de dé** :
- Sélection aléatoire parmi toutes les valeurs disponibles
- Aucune préférence stratégique

**Timing d'arrêt** :
- Respecte les contraintes de base (doit continuer si < 21 points ou pas de ver)
- Sinon, décision aléatoire selon `continue_probability`

**Choix de tuile** :
- Sélection aléatoire parmi TOUTES les tuiles accessibles
- Pas de distinction entre vol et centre
- Traite toutes les options sur un pied d'égalité

**Utilité** :
- **Baseline de comparaison** : Performance de référence "neutre"
- **Test de robustesse** : Valide que le jeu fonctionne avec des choix imprévisibles
- **Recherche** : Point de départ pour analyser l'impact des différents choix
- **Apprentissage** : Comprendre l'importance de la stratégie par contraste

## 🔧 Comment Créer sa Propre Stratégie

```python
from pikomino import GameStrategy, TurnState, Player, DiceValue, Tile
from typing import Optional, List, Tuple

class MaStrategie(GameStrategy):
    
    def choose_dice_value(self, turn_state: TurnState, player: Player) -> Optional[DiceValue]:
        """Choisit quelle valeur de dé réserver"""
        available_values = [
            v for v in turn_state.current_roll 
            if turn_state.can_reserve_value(v)
        ]
        
        if not available_values:
            return None
            
        # VOTRE LOGIQUE ICI
        # Exemples :
        # - Toujours prendre les vers : if WORM in available_values: return WORM
        # - Privilégier la fréquence : return most_frequent_value
        # - Viser les hautes valeurs : return highest_value
        
        return available_values[0]  # Placeholder
    
    def should_continue_turn(self, turn_state: TurnState, player: Player) -> bool:
        """Décide si continuer le tour"""
        score = turn_state.get_total_score()
        has_worm = turn_state.has_worm()
        remaining_dice = turn_state.remaining_dice
        
        # VOTRE LOGIQUE ICI
        # Exemples :
        # - Conservateur : return not (score >= 21 and has_worm)
        # - Agressif : return score < 30 and remaining_dice > 0
        # - Adaptatif : considérer le score actuel du joueur vs adversaires
        
        return False  # Placeholder
    
    def choose_target_tile(
        self, 
        score: int, 
        has_worm: bool, 
        center_tiles: List[Tile], 
        stealable_tiles: List[Tuple[Tile, Player]], 
        current_player: Player
    ) -> Optional[Tile]:
        """Choisit quelle tuile cibler"""
        if not has_worm:
            return None
            
        # VOTRE LOGIQUE ICI
        # Exemples :
        # - Toujours voler : if stealable_tiles: return best_stealable_tile
        # - Sécurité : if center_tiles: return safest_center_tile
        # - Optimiser vers : return tile_with_most_worms
        # - Cibler joueur : return tile_from_specific_player
        
        # Comportement par défaut
        if stealable_tiles:
            return stealable_tiles[0][0]
        if center_tiles:
            return center_tiles[0]
        return None
```

## 📊 Exemples d'Utilisation

### Test de Stratégie Personnalisée
```python
from pikomino import simulate_game

# Créer votre stratégie
ma_strategie = MaStrategie()

# Tester contre d'autres stratégies
result = simulate_game(
    ["MaStrategie", "Conservative", "Aggressive"],
    [ma_strategie, ConservativeStrategy(), AggressiveStrategy()]
)

print(f"Gagnant: {result['winner']}")
print(f"Scores: {result['final_scores']}")
```

### Stratégie Ciblée Avancée
```python
# Stratégie qui cible spécifiquement "Alice" et vise les tuiles 32+
hunter = TargetedStrategy(
    target_player_name="Alice", 
    min_target_value=32
)

# Test en situation
players = [
    ("Alice", ConservativeStrategy()),
    ("Hunter", hunter),
    ("Bob", AggressiveStrategy())
]
```

### Stratégie Aléatoire pour Tests
```python
# Stratégie complètement aléatoire (50% de chance de continuer)
random_strategy = RandomStrategy()

# Stratégie aléatoire prudente (30% de chance de continuer)
cautious_random = RandomStrategy(continue_probability=0.3)

# Stratégie aléatoire risquée (80% de chance de continuer)  
risky_random = RandomStrategy(continue_probability=0.8)

# Test de baseline
result = simulate_game(
    ["Random", "Conservative", "Aggressive"],
    [random_strategy, ConservativeStrategy(), AggressiveStrategy()]
)
```

### Partie Chaos Complète
```python
# Partie avec que des stratégies aléatoires
chaos_players = [
    ("Chaos1", RandomStrategy(0.3)),    # Prudent
    ("Chaos2", RandomStrategy(0.5)),    # Normal
    ("Chaos3", RandomStrategy(0.7)),    # Risqué
    ("Chaos4", RandomStrategy(0.9)),    # Kamikaze
]
```

## 🎮 Intégration avec l'Interface Web

L'interface web utilise ces choix stratégiques pour :
- **Mode IA** : Les stratégies choisissent automatiquement
- **Mode Humain** : Le joueur fait les choix via l'interface
- **Mode Mixte** : Combinaison humains + IA avec différentes stratégies

## 🧪 Tests des Stratégies

Tous les choix stratégiques sont testés :
- **Tests unitaires** : Chaque méthode de choix
- **Tests d'intégration** : Comportement en partie complète
- **Tests comparatifs** : Performance relative des stratégies

## 💡 Idées d'Améliorations Futures

### Choix Avancés Possibles :
1. **Méta-stratégie** : Changer de stratégie selon l'état de la partie
2. **Apprentissage** : Adapter selon le comportement des adversaires
3. **Coopération** : Éviter de nuire à certains joueurs
4. **Bluff** : Feindre certains objectifs pour tromper l'adversaire
5. **Analyse prédictive** : Anticiper les coups des adversaires

### Métriques Stratégiques :
- **Efficacité de vol** : Pourcentage de vols réussis
- **Gestion du risque** : Ratio tours réussis/ratés
- **Optimisation des tuiles** : Vers/tours moyens
- **Impact tactique** : Influence sur les autres joueurs

---

**🎯 Résultat : Le système offre maintenant un contrôle stratégique complet sur tous les aspects du jeu, permettant de créer des IA sophistiquées et des expériences de jeu variées !** 