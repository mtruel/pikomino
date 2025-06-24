#!/usr/bin/env python3
"""
Exemples d'utilisation du modèle Pikomino pour tester différentes stratégies
"""

from pikomino import (
    Player, PikominoGame, ConservativeStrategy, AggressiveStrategy,
    simulate_game, GameStrategy, TurnState, DiceValue
)
from typing import Optional, List
import statistics


class BalancedStrategy(GameStrategy):
    """Stratégie équilibrée qui adapte son comportement selon le contexte"""
    
    def choose_dice_value(self, turn_state: TurnState, player: Player) -> Optional[DiceValue]:
        available_values = [v for v in turn_state.current_roll 
                          if turn_state.can_reserve_value(v)]
        
        if not available_values:
            return None
        
        # Privilégier les vers si on n'en a pas encore
        if DiceValue.WORM in available_values and not turn_state.has_worm():
            return DiceValue.WORM
        
        # Si on a déjà beaucoup de points, privilégier la sécurité (plus d'occurrences)
        if turn_state.get_total_score() >= 25:
            value_counts = {}
            for value in available_values:
                value_counts[value] = turn_state.current_roll.count(value)
            return max(value_counts.keys(), key=lambda v: value_counts[v])
        
        # Sinon, privilégier les hautes valeurs
        priority_order = [DiceValue.WORM, DiceValue.FIVE, DiceValue.FOUR, 
                         DiceValue.THREE, DiceValue.TWO, DiceValue.ONE]
        
        for preferred_value in priority_order:
            if preferred_value in available_values:
                return preferred_value
        
        return available_values[0]
    
    def should_continue_turn(self, turn_state: TurnState, player: Player) -> bool:
        score = turn_state.get_total_score()
        
        # S'arrêter si on peut prendre une tuile et qu'on a peu de dés restants
        if score >= 21 and turn_state.has_worm() and turn_state.remaining_dice <= 2:
            return False
        
        # Continuer si on a encore beaucoup de dés et un score raisonnable
        if turn_state.remaining_dice >= 4 and score < 28:
            return True
        
        # Sinon, s'arrêter si on peut prendre une tuile
        return not (score >= 21 and turn_state.has_worm())


class WormFocusedStrategy(GameStrategy):
    """Stratégie qui se concentre sur obtenir des vers rapidement"""
    
    def choose_dice_value(self, turn_state: TurnState, player: Player) -> Optional[DiceValue]:
        available_values = [v for v in turn_state.current_roll 
                          if turn_state.can_reserve_value(v)]
        
        if not available_values:
            return None
        
        # Toujours privilégier les vers
        if DiceValue.WORM in available_values:
            return DiceValue.WORM
        
        # Sinon, prendre la valeur la plus fréquente
        value_counts = {}
        for value in available_values:
            value_counts[value] = turn_state.current_roll.count(value)
        
        return max(value_counts.keys(), key=lambda v: value_counts[v])
    
    def should_continue_turn(self, turn_state: TurnState, player: Player) -> bool:
        # S'arrêter dès qu'on a un ver et au moins 21 points
        return not (turn_state.has_worm() and turn_state.get_total_score() >= 21)


def compare_strategies():
    """Compare les performances de différentes stratégies"""
    print("=== Comparaison des stratégies ===\n")
    
    strategies = {
        "Conservative": ConservativeStrategy(),
        "Aggressive": AggressiveStrategy(),
        "Balanced": BalancedStrategy(),
        "WormFocused": WormFocusedStrategy()
    }
    
    num_games = 100
    results = {name: [] for name in strategies.keys()}
    
    print(f"Simulation de {num_games} parties pour chaque stratégie...")
    
    # Tester chaque stratégie contre les autres
    for strategy_name, strategy in strategies.items():
        wins = 0
        total_scores = []
        
        for _ in range(num_games):
            # Créer une partie avec la stratégie testée et deux stratégies conservatrices
            player_names = [strategy_name, "Conservative1", "Conservative2"]
            game_strategies = [strategy, ConservativeStrategy(), ConservativeStrategy()]
            
            result = simulate_game(player_names, game_strategies)
            
            if result['winner'] == strategy_name:
                wins += 1
            
            total_scores.append(result['final_scores'][strategy_name])
        
        win_rate = wins / num_games * 100
        avg_score = statistics.mean(total_scores)
        results[strategy_name] = {
            'win_rate': win_rate,
            'avg_score': avg_score,
            'scores': total_scores
        }
        
        print(f"{strategy_name:12}: {win_rate:5.1f}% victoires, {avg_score:5.1f} vers en moyenne")
    
    # Analyser les résultats
    print("\n=== Analyse détaillée ===")
    for name, data in results.items():
        scores = data['scores']
        print(f"\n{name}:")
        print(f"  Taux de victoire: {data['win_rate']:.1f}%")
        print(f"  Score moyen: {data['avg_score']:.1f}")
        print(f"  Score médian: {statistics.median(scores):.1f}")
        print(f"  Écart-type: {statistics.stdev(scores):.1f}")
        print(f"  Score min/max: {min(scores)}/{max(scores)}")


def test_strategy_vs_strategy():
    """Teste des duels entre stratégies spécifiques"""
    print("\n=== Duels de stratégies ===\n")
    
    matchups = [
        ("Conservative", ConservativeStrategy(), "Aggressive", AggressiveStrategy()),
        ("Balanced", BalancedStrategy(), "Conservative", ConservativeStrategy()),
        ("WormFocused", WormFocusedStrategy(), "Aggressive", AggressiveStrategy()),
    ]
    
    num_games = 50
    
    for name1, strat1, name2, strat2 in matchups:
        wins1 = 0
        wins2 = 0
        draws = 0
        
        for _ in range(num_games):
            result = simulate_game([name1, name2], [strat1, strat2])
            
            score1 = result['final_scores'][name1]
            score2 = result['final_scores'][name2]
            
            if score1 > score2:
                wins1 += 1
            elif score2 > score1:
                wins2 += 1
            else:
                draws += 1
        
        print(f"{name1} vs {name2} ({num_games} parties):")
        print(f"  {name1}: {wins1} victoires ({wins1/num_games*100:.1f}%)")
        print(f"  {name2}: {wins2} victoires ({wins2/num_games*100:.1f}%)")
        print(f"  Égalités: {draws}")
        print()


def simulate_detailed_game():
    """Simule une partie avec affichage détaillé"""
    print("\n=== Simulation détaillée d'une partie ===\n")
    
    players = [
        Player("Alice", ConservativeStrategy()),
        Player("Bob", AggressiveStrategy()),
        Player("Charlie", BalancedStrategy())
    ]
    
    game = PikominoGame(players)
    turn_count = 0
    max_turns = 30  # Limite pour éviter les parties trop longues
    
    print("Joueurs:")
    for player in players:
        print(f"  - {player.name} ({type(player.strategy).__name__})")
    
    print(f"\nTuiles disponibles au début: {len(game.tiles_center)}")
    print("-" * 50)
    
    while not game.is_game_over() and turn_count < max_turns:
        turn_count += 1
        current_player = game.get_current_player()
        
        print(f"\nTour {turn_count} - {current_player.name}")
        
        # Afficher l'état avant le tour
        print(f"  Score actuel: {current_player.get_score()} vers")
        print(f"  Tuiles en main: {len(current_player.tiles)}")
        
        # Jouer le tour
        result, details = game.play_turn()
        
        # Afficher le résultat
        print(f"  Résultat: {result.value}")
        print(f"  Nouveau score: {current_player.get_score()} vers")
        
        if result.value == "success" and current_player.tiles:
            last_tile = current_player.tiles[-1]
            print(f"  Tuile prise: {last_tile.value} ({last_tile.worms} vers)")
        
        game.next_player()
    
    # Résultats finaux
    print("\n" + "=" * 50)
    print("RÉSULTATS FINAUX")
    print("=" * 50)
    
    winner = game.get_winner()
    
    for i, player in enumerate(sorted(players, key=lambda p: p.get_score(), reverse=True)):
        position = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}e"
        print(f"{position} {player.name}: {player.get_score()} vers ({len(player.tiles)} tuiles)")
    
    print(f"\nGagnant: {winner.name} 🎉")
    print(f"Tuiles restantes au centre: {len(game.tiles_center)}")
    print(f"Tours joués: {turn_count}")


def analyze_game_length():
    """Analyse la durée moyenne des parties"""
    print("\n=== Analyse de la durée des parties ===\n")
    
    num_games = 20
    game_lengths = []
    
    for _ in range(num_games):
        players = [
            Player("P1", ConservativeStrategy()),
            Player("P2", AggressiveStrategy()),
            Player("P3", BalancedStrategy())
        ]
        
        game = PikominoGame(players)
        turns = 0
        
        while not game.is_game_over() and turns < 100:  # Limite de sécurité
            game.play_turn()
            game.next_player()
            turns += 1
        
        game_lengths.append(turns)
    
    print(f"Analyse sur {num_games} parties:")
    print(f"  Durée moyenne: {statistics.mean(game_lengths):.1f} tours")
    print(f"  Durée médiane: {statistics.median(game_lengths):.1f} tours")
    print(f"  Durée min/max: {min(game_lengths)}/{max(game_lengths)} tours")
    print(f"  Écart-type: {statistics.stdev(game_lengths):.1f}")


def main():
    """Fonction principale pour exécuter tous les exemples"""
    print("🎲 PIKOMINO - ANALYSE DES STRATÉGIES 🐛")
    print("=" * 60)
    
    # Comparaison générale des stratégies
    compare_strategies()
    
    # Duels spécifiques
    test_strategy_vs_strategy()
    
    # Analyse de la durée des parties
    analyze_game_length()
    
    # Simulation détaillée d'une partie
    simulate_detailed_game()


if __name__ == "__main__":
    main() 