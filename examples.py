#!/usr/bin/env python3
"""
Exemples d'utilisation du modèle Pikomino pour tester différentes stratégies
"""

from pikomino import (
    Player,
    PikominoGame,
    simulate_game,
    TurnState,
    DiceValue,
)
from strategies import (
    GameStrategy,
    ConservativeStrategy,
    AggressiveStrategy,
    BalancedStrategy,
    TargetedStrategy,
    RandomStrategy,
    OptimalStrategy,
    GameContext
)
from typing import Optional, List
import statistics
import random





class WormFocusedStrategy(GameStrategy):
    """Stratégie qui se concentre sur obtenir des vers rapidement"""

    def choose_dice_value(
        self, turn_state: TurnState, player: Player
    ) -> Optional[DiceValue]:
        available_values = [
            v for v in turn_state.current_roll if turn_state.can_reserve_value(v)
        ]

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
        "WormFocused": WormFocusedStrategy(),
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

            if result["winner"] == strategy_name:
                wins += 1

            total_scores.append(result["final_scores"][strategy_name])

        win_rate = wins / num_games * 100
        avg_score = statistics.mean(total_scores)
        results[strategy_name] = {
            "win_rate": win_rate,
            "avg_score": avg_score,
            "scores": total_scores,
        }

        print(
            f"{strategy_name:12}: {win_rate:5.1f}% victoires, {avg_score:5.1f} vers en moyenne"
        )

    # Analyser les résultats
    print("\n=== Analyse détaillée ===")
    for name, data in results.items():
        scores = data["scores"]
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

            score1 = result["final_scores"][name1]
            score2 = result["final_scores"][name2]

            if score1 > score2:
                wins1 += 1
            elif score2 > score1:
                wins2 += 1
            else:
                draws += 1

        print(f"{name1} vs {name2} ({num_games} parties):")
        print(f"  {name1}: {wins1} victoires ({wins1 / num_games * 100:.1f}%)")
        print(f"  {name2}: {wins2} victoires ({wins2 / num_games * 100:.1f}%)")
        print(f"  Égalités: {draws}")
        print()


def simulate_detailed_game():
    """Simule une partie avec affichage détaillé"""
    print("\n=== Simulation détaillée d'une partie ===\n")

    players = [
        Player("Alice", ConservativeStrategy()),
        Player("Bob", AggressiveStrategy()),
        Player("Charlie", BalancedStrategy()),
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

    for i, player in enumerate(
        sorted(players, key=lambda p: p.get_score(), reverse=True)
    ):
        position = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i + 1}e"
        print(
            f"{position} {player.name}: {player.get_score()} vers ({len(player.tiles)} tuiles)"
        )

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
            Player("P3", BalancedStrategy()),
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


def demo_new_strategies():
    """Démonstration des nouvelles stratégies avec choix de tuiles"""
    print("🎯 Démonstration des stratégies avancées")
    print("=" * 50)
    
    # Créer des joueurs avec différentes stratégies
    players = [
        ("Conservative", ConservativeStrategy()),
        ("Aggressive", AggressiveStrategy()),
        ("Balanced", BalancedStrategy()),
        ("TargetHigh", TargetedStrategy(min_target_value=30)),
        ("TargetPlayer", TargetedStrategy(target_player_name="Conservative")),
    ]
    
    player_names = [name for name, _ in players]
    strategies = [strategy for _, strategy in players]
    
    print(f"Joueurs: {', '.join(player_names)}")
    print()
    
    # Simuler plusieurs parties
    results = []
    wins = {name: 0 for name in player_names}
    
    for i in range(10):
        result = simulate_game(player_names, strategies)
        results.append(result)
        wins[result["winner"]] += 1
        
        print(f"Partie {i+1}: Gagnant = {result['winner']}")
        print(f"  Scores: {result['final_scores']}")
        print()
    
    print("📊 Résultats finaux:")
    for name, win_count in wins.items():
        win_rate = (win_count / 10) * 100
        print(f"  {name}: {win_count}/10 victoires ({win_rate:.1f}%)")


def demo_tactical_choices():
    """Démonstration des choix tactiques possibles"""
    print("\n🧠 Choix tactiques disponibles")
    print("=" * 40)
    
    print("1. 🎲 CHOIX DE DÉS:")
    print("   • Privilégier fréquence vs valeur")
    print("   • Assurer un ver vs maximiser les points") 
    print("   • Adapter selon les dés restants")
    print()
    
    print("2. ⏹️  TIMING D'ARRÊT:")
    print("   • Sécuriser vs risquer pour plus")
    print("   • S'adapter au nombre de dés")
    print("   • Considérer la situation en cours")
    print()
    
    print("3. 🎯 CHOIX DE TUILE:")
    print("   • Voler chez un adversaire vs prendre au centre")
    print("   • Maximiser les vers vs minimiser les risques")
    print("   • Cibler des joueurs spécifiques")
    print("   • Viser des tuiles de valeur particulière")
    print()


def compare_tile_strategies():
    """Compare les différentes approches de choix de tuiles"""
    print("🔍 Comparaison des stratégies de tuiles")
    print("=" * 45)
    
    strategies_info = [
        ("Conservative", "Évite les conflits, préfère le centre, tuiles basses"),
        ("Aggressive", "Privilégie le vol, tuiles hautes, impact maximum"),
        ("Balanced", "Adapte selon le score relatif des adversaires"),
        ("Targeted", "Cible des joueurs ou valeurs spécifiques")
    ]
    
    for name, description in strategies_info:
        print(f"📋 {name}:")
        print(f"   {description}")
        print()


def demo_targeted_strategy():
    """Démonstration spécifique de la stratégie ciblée"""
    print("🎯 Démonstration de la stratégie ciblée")
    print("=" * 40)
    
    # Stratégie qui cible Alice spécifiquement
    target_alice = TargetedStrategy(target_player_name="Alice", min_target_value=28)
    
    # Stratégie qui vise les tuiles hautes
    target_high = TargetedStrategy(min_target_value=32)
    
    players = [
        ("Alice", ConservativeStrategy()),
        ("Hunter", target_alice),  # Cible Alice
        ("HighSeeker", target_high),  # Vise les tuiles 32+
    ]
    
    player_names = [name for name, _ in players]
    strategies = [strategy for _, strategy in players]
    
    print("Scénario: Hunter cible Alice, HighSeeker vise les tuiles 32+")
    print()
    
    for i in range(5):
        result = simulate_game(player_names, strategies)
        print(f"Partie {i+1}:")
        print(f"  Gagnant: {result['winner']}")
        print(f"  Scores: {result['final_scores']}")
        print()


def demo_random_strategy():
    """Démonstration de la stratégie aléatoire"""
    print("🎲 Démonstration de la stratégie aléatoire")
    print("=" * 45)
    
    # Créer différentes variantes de la stratégie aléatoire
    strategies_info = [
        ("Random50", RandomStrategy(continue_probability=0.5), "50% chance de continuer"),
        ("RandomCautious", RandomStrategy(continue_probability=0.3), "30% chance de continuer (prudent)"),
        ("RandomRisky", RandomStrategy(continue_probability=0.7), "70% chance de continuer (risqué)"),
        ("Conservative", ConservativeStrategy(), "Stratégie conservatrice (comparaison)"),
    ]
    
    print("Stratégies testées:")
    for name, strategy, description in strategies_info:
        print(f"📋 {name}: {description}")
    print()
    
    # Simuler plusieurs parties
    num_games = 20
    results = {name: [] for name, _, _ in strategies_info}
    wins = {name: 0 for name, _, _ in strategies_info}
    
    for i in range(num_games):
        player_names = [name for name, _, _ in strategies_info]
        game_strategies = [strategy for _, strategy, _ in strategies_info]
        
        result = simulate_game(player_names, game_strategies)
        
        # Enregistrer les résultats
        for name in player_names:
            results[name].append(result["final_scores"][name])
            if result["winner"] == name:
                wins[name] += 1
    
    print(f"📊 Résultats sur {num_games} parties:")
    for name, _, description in strategies_info:
        win_rate = (wins[name] / num_games) * 100
        avg_score = sum(results[name]) / len(results[name])
        print(f"  {name:15}: {win_rate:5.1f}% victoires, {avg_score:5.1f} vers/partie")
    
    print()
    print("🎯 Observations:")
    print("   • La stratégie aléatoire teste les limites du jeu")
    print("   • Permet de valider la robustesse des règles")
    print("   • Utile comme baseline de comparaison")
    print("   • La probabilité de continuer affecte les performances")


def test_random_vs_strategies():
    """Test la stratégie aléatoire contre d'autres stratégies"""
    print("\n🥊 Random vs Autres Stratégies")
    print("=" * 35)
    
    matchups = [
        ("Random", RandomStrategy(), "Conservative", ConservativeStrategy()),
        ("Random", RandomStrategy(), "Aggressive", AggressiveStrategy()),
        ("Random", RandomStrategy(), "Balanced", BalancedStrategy()),
        ("RandomRisky", RandomStrategy(0.8), "Conservative", ConservativeStrategy()),
    ]
    
    for name1, strat1, name2, strat2 in matchups:
        print(f"\n{name1} vs {name2}:")
        
        wins1 = wins2 = 0
        total_score1 = total_score2 = 0
        num_games = 30
        
        for _ in range(num_games):
            result = simulate_game([name1, name2], [strat1, strat2])
            
            score1 = result["final_scores"][name1]
            score2 = result["final_scores"][name2] 
            
            total_score1 += score1
            total_score2 += score2
            
            if score1 > score2:
                wins1 += 1
            elif score2 > score1:
                wins2 += 1
        
        avg1 = total_score1 / num_games
        avg2 = total_score2 / num_games
        
        print(f"  {name1:12}: {wins1:2d} victoires ({wins1/num_games*100:4.1f}%), {avg1:.1f} vers/partie")
        print(f"  {name2:12}: {wins2:2d} victoires ({wins2/num_games*100:4.1f}%), {avg2:.1f} vers/partie")


def demo_chaos_game():
    """Partie complètement chaotique avec que des stratégies aléatoires"""
    print("\n🌪️  Partie Chaos - Que du Random!")
    print("=" * 35)
    
    # Créer 4 joueurs avec des stratégies aléatoires différentes
    players = [
        ("Chaos1", RandomStrategy(0.3)),    # Prudent
        ("Chaos2", RandomStrategy(0.5)),    # Équilibré  
        ("Chaos3", RandomStrategy(0.7)),    # Risqué
        ("Chaos4", RandomStrategy(0.9)),    # Très risqué
    ]
    
    player_names = [name for name, _ in players]
    strategies = [strategy for _, strategy in players]
    
    print("Joueurs chaotiques:")
    probs = [0.3, 0.5, 0.7, 0.9]
    for i, (name, _) in enumerate(players):
        risk_level = ["🛡️ Prudent", "⚖️ Équilibré", "⚔️ Risqué", "🔥 Kamikaze"][i]
        print(f"  {name}: {risk_level} ({probs[i]*100:.0f}% de continuer)")
    
    print("\nSimulation d'une partie chaotique...")
    result = simulate_game(player_names, strategies)
    
    print(f"\n🏆 Résultat de la partie chaos:")
    print(f"   Gagnant: {result['winner']}")
    print(f"   Scores finaux: {result['final_scores']}")
    print(f"   Tuiles finales: {result['final_tiles']}")


def demo_optimal_strategy():
    """Démonstration de la stratégie optimale théorique"""
    print("\n🎯 Démonstration de la Stratégie Optimale")
    print("=" * 50)
    
    print("🧠 Principes de la stratégie optimale:")
    print("   1. 🎲 Assurer un ver en priorité ABSOLUE")
    print("   2. ⚖️ Équilibrer fréquence × valeur + bonus fréquence")
    print("   3. 📈 Seuils adaptatifs selon les dés restants:")
    print("      • 5+ dés: viser 28+ (zone optimale)")
    print("      • 3-4 dés: viser 25+ (conservateur)")
    print("      • 2 dés: viser 23+ (prudent)")
    print("      • 1 dé: sécuriser à 21+")
    print("   4. 🥷 Vol privilégié si impact double > centre")
    print("   5. 🎯 Cibler la zone 25-32 (meilleur rapport)")
    
    # Test de performance
    strategies_comparison = [
        ("Optimal", OptimalStrategy(), "🎯 Stratégie théoriquement optimale"),
        ("Balanced", BalancedStrategy(), "⚖️ Stratégie équilibrée existante"),
        ("Conservative", ConservativeStrategy(), "🛡️ Stratégie conservatrice"),
        ("Aggressive", AggressiveStrategy(), "⚔️ Stratégie agressive"),
        ("TargetHigh", TargetedStrategy(min_target_value=29), "🎪 Stratégie ciblée"),
    ]
    
    print(f"\n📊 Test de performance (20 parties):")
    num_test_games = 20
    results = {name: [] for name, _, _ in strategies_comparison}
    wins = {name: 0 for name, _, _ in strategies_comparison}
    
    for i in range(num_test_games):
        player_names = [name for name, _, _ in strategies_comparison]
        game_strategies = [strategy for _, strategy, _ in strategies_comparison]
        
        result = simulate_game(player_names, game_strategies)
        
        for name in player_names:
            results[name].append(result["final_scores"][name])
            if result["winner"] == name:
                wins[name] += 1
    
    print("\nRésultats:")
    for name, _, description in strategies_comparison:
        avg_score = sum(results[name]) / len(results[name])
        win_rate = (wins[name] / num_test_games) * 100
        print(f"  {name:12}: {win_rate:5.1f}% victoires, {avg_score:5.2f} vers/partie - {description}")
    
    # Identifier la meilleure
    best_strategy = max(strategies_comparison, 
                       key=lambda x: sum(results[x[0]]) / len(results[x[0]]))
    
    print(f"\n🏆 Meilleure performance: {best_strategy[0]}")
    
    if best_strategy[0] == "Optimal":
        print("   ✅ La stratégie optimale confirme sa supériorité!")
    else:
        print(f"   🤔 Surprise: {best_strategy[0]} surpasse la stratégie optimale")
        print("   → Cela suggère des axes d'amélioration possibles")


def analyze_winning_factors():
    """Analyse des facteurs clés de victoire"""
    print("\n🔍 ANALYSE DES FACTEURS CLÉS DE VICTOIRE")
    print("=" * 50)
    
    print("🎲 DISTRIBUTION DES TUILES:")
    print("   • Tuiles 21-24: 4 × 1 ver = 4 vers (10% du total)")
    print("   • Tuiles 25-28: 4 × 2 vers = 8 vers (20% du total)")
    print("   • Tuiles 29-32: 4 × 3 vers = 12 vers (30% du total)")
    print("   • Tuiles 33-36: 4 × 4 vers = 16 vers (40% du total)")
    print("   • TOTAL: 40 vers dans le jeu")
    
    print("\n⚖️ RAPPORT RISQUE/RÉCOMPENSE:")
    print("   Score   | Effort | Récompense | Ratio")
    print("   --------|--------|------------|-------")
    print("   21-24   | Faible | 1 ver      | 1.0")
    print("   25-28   | Moyen  | 2 vers     | 2.0")
    print("   29-32   | Élevé  | 3 vers     | 1.5")
    print("   33-36   | T.Élevé| 4 vers     | 1.0")
    print("   → Zone 25-28 = meilleur rapport!")
    
    print("\n🥷 IMPACT DU VOL:")
    print("   • Vol réussi = Gain personnel + Perte adversaire")
    print("   • Impact double par rapport au centre")
    print("   • Exemple: Voler 3 vers = +3 pour soi + -3 pour adversaire")
    print("   • Équivalent à gagner 6 vers depuis le centre!")
    
    print("\n🎯 STRATÉGIE OPTIMALE DÉRIVÉE:")
    print("   1. Priorité ABSOLUE aux vers (sine qua non)")
    print("   2. Cibler la zone 25-28 principalement")
    print("   3. Vol systématique si impact ≥ centre")
    print("   4. Adaptation du risque selon les dés restants")
    print("   5. Formule dés: fréquence × valeur + bonus fréquence")


class AnalyticalStrategy(GameStrategy):
    """
    Exemple d'une stratégie avancée qui utilise tout le contexte disponible
    pour prendre des décisions intelligentes
    """
    
    def __init__(self, name="Analytical"):
        self.name = name
        self.adaptations = []  # Historique des adaptations de stratégie
    
    def choose_dice_value(self, context: GameContext) -> Optional["DiceValue"]:
        from pikomino import DiceValue, Dice
        
        turn_state = context.turn_state
        available_values = [
            v for v in turn_state.current_roll if turn_state.can_reserve_value(v)
        ]
        
        if not available_values:
            return None
        
        # Analyser les statistiques des adversaires
        self._analyze_opponents(context)
        
        # PRIORITÉ 1: Assurer un ver si nécessaire
        if DiceValue.WORM in available_values and not turn_state.has_worm():
            return DiceValue.WORM
        
        # PRIORITÉ 2: Adaptation basée sur la position dans la partie
        if self._should_play_aggressively(context):
            # Jouer aggressivement : privilégier les hautes valeurs
            return max(available_values, key=lambda v: Dice.get_point_value(v))
        
        # PRIORITÉ 3: Stratégie équilibrée avec bonus fréquence
        scores = {}
        for value in available_values:
            count = turn_state.current_roll.count(value)
            points = Dice.get_point_value(value)
            
            # Formule avec adaptation contextuelle
            base_score = count * points
            frequency_bonus = (count - 1) * 0.5
            
            # Bonus si on observe que l'adversaire rate souvent les gros scores
            context_bonus = self._calculate_context_bonus(value, context)
            
            scores[value] = base_score + frequency_bonus + context_bonus
            
        return max(scores.keys(), key=lambda v: scores[v])
    
    def should_continue_turn(self, context: GameContext) -> bool:
        turn_state = context.turn_state
        score = turn_state.get_total_score()
        
        # Contraintes de base
        if turn_state.remaining_dice == 0:
            return False
            
        if score < 21 or not turn_state.has_worm():
            return True
        
        # Analyse contextuelle pour les seuils
        risk_tolerance = self._calculate_risk_tolerance(context)
        
        # Seuils adaptatifs basés sur l'analyse
        if turn_state.remaining_dice >= 5:
            target = 26 + risk_tolerance
        elif turn_state.remaining_dice >= 3:
            target = 24 + risk_tolerance  
        elif turn_state.remaining_dice >= 2:
            target = 22 + risk_tolerance
        else:
            target = 21  # Sécuriser avec 1 dé
            
        return score < target
    
    def choose_target_tile(self, context: GameContext) -> Optional["Tile"]:
        turn_state = context.turn_state
        if not turn_state.has_worm():
            return None
        
        # Analyse stratégique basée sur l'historique
        strategic_impact = self._analyze_tile_impact(context)
        
        # Choisir selon l'impact calculé
        if strategic_impact["best_option"] == "steal" and context.stealable_tiles:
            return strategic_impact["best_steal_tile"]
        elif strategic_impact["best_option"] == "center" and context.available_center_tiles:
            return strategic_impact["best_center_tile"]
        
        # Fallback : comportement par défaut
        if context.stealable_tiles:
            return max(context.stealable_tiles, key=lambda x: x[0].worms)[0]
        if context.available_center_tiles:
            return max(context.available_center_tiles, key=lambda t: t.worms)
            
        return None
    
    def _analyze_opponents(self, context: GameContext):
        """Analyse les patterns des adversaires"""
        insights = []
        
        for player in context.all_players:
            if player != context.current_player:
                stats = context.game_history.get_player_statistics(player.name)
                if stats:
                    success_rate = stats.get('success_rate', 0)
                    avg_score = stats.get('average_score_on_success', 0)
                    
                    insight = f"{player.name}: {success_rate:.1%} succès, {avg_score:.1f} pts moy"
                    insights.append(insight)
                    
                    # Adaptation : si adversaire très conservateur, on peut être plus agressif
                    if success_rate < 0.4:
                        self.adaptations.append(f"T{context.turn_number}: {player.name} semble prudent")
    
    def _should_play_aggressively(self, context: GameContext) -> bool:
        """Détermine si il faut jouer aggressivement"""
        current_score = context.current_player.get_score()
        opponent_scores = context.get_opponent_scores()
        
        if not opponent_scores:
            return False
        
        max_opponent_score = max(opponent_scores.values())
        
        # Jouer aggressivement si :
        # 1. On est très en retard (>5 vers)
        # 2. Un adversaire a déjà beaucoup de vers (>15)
        # 3. Peu de tuiles restantes au centre
        
        behind_threshold = current_score < max_opponent_score - 5
        opponent_winning = max_opponent_score > 15
        tiles_scarce = len(context.tiles_center) < 8
        
        return behind_threshold or opponent_winning or tiles_scarce
    
    def _calculate_risk_tolerance(self, context: GameContext) -> int:
        """Calcule la tolérance au risque basée sur le contexte"""
        base_tolerance = 0
        
        # Plus de tolérance si on est en retard
        if not context.is_current_player_leading():
            base_tolerance += 3
        
        # Moins de tolérance si on mène de beaucoup
        current_score = context.current_player.get_score()
        opponent_scores = context.get_opponent_scores()
        if opponent_scores:
            max_opponent = max(opponent_scores.values())
            if current_score > max_opponent + 8:
                base_tolerance -= 2
        
        # Analyse de l'historique récent
        recent_failures = 0
        recent_turns = context.game_history.get_recent_turns(5)
        for turn in recent_turns[-3:]:  # 3 derniers tours
            if turn.result.value != "success":
                recent_failures += 1
        
        if recent_failures >= 2:
            base_tolerance -= 1  # Plus prudent après des échecs
        
        return max(-3, min(3, base_tolerance))  # Limiter entre -3 et +3
    
    def _calculate_context_bonus(self, value: "DiceValue", context: GameContext) -> float:
        """Calcule un bonus contextuel pour une valeur de dé"""
        bonus = 0.0
        
        # Bonus pour les vers si peu d'adversaires en ont
        if value.name == "WORM":
            players_with_worms = sum(1 for p in context.all_players if p.get_score() > 0)
            if players_with_worms < len(context.all_players) * 0.6:
                bonus += 0.5
        
        return bonus
    
    def _analyze_tile_impact(self, context: GameContext) -> dict:
        """Analyse l'impact stratégique des différentes options de tuiles"""
        analysis = {
            "best_option": "none",
            "best_steal_tile": None,
            "best_center_tile": None,
            "steal_impact": 0,
            "center_impact": 0
        }
        
        # Analyser les vols possibles
        if context.stealable_tiles:
            best_steal = max(context.stealable_tiles, key=lambda x: x[0].worms)
            steal_tile, steal_target = best_steal
            
            # Impact = gain + perte adversaire + impact psychologique
            direct_impact = steal_tile.worms * 2  # Double impact
            
            # Bonus psychologique si on vole au leader
            opponent_scores = context.get_opponent_scores()
            if opponent_scores and steal_target.get_score() == max(opponent_scores.values()):
                direct_impact += 1  # Bonus leader
            
            analysis["steal_impact"] = direct_impact
            analysis["best_steal_tile"] = steal_tile
        
        # Analyser les tuiles du centre
        if context.available_center_tiles:
            best_center = max(context.available_center_tiles, key=lambda t: t.worms)
            
            # Impact = gain simple + sécurité
            center_impact = best_center.worms + 0.5  # Bonus sécurité
            
            analysis["center_impact"] = center_impact
            analysis["best_center_tile"] = best_center
        
        # Décision finale
        if analysis["steal_impact"] > analysis["center_impact"]:
            analysis["best_option"] = "steal"
        elif analysis["center_impact"] > 0:
            analysis["best_option"] = "center"
        
        return analysis


def demonstrate_enriched_context():
    """Démontre l'utilisation du contexte enrichi"""
    print("=== Démonstration du Contexte Enrichi ===\n")
    
    # Créer des joueurs avec différentes stratégies
    players = [
        Player("Conservative", ConservativeStrategy()),
        Player("Aggressive", AggressiveStrategy()),
        Player("Analytical", AnalyticalStrategy()),
        Player("Optimal", OptimalStrategy())
    ]
    
    # Lancer une partie
    game = PikominoGame(players)
    
    print("Début de partie...")
    print(f"Joueurs: {[p.name for p in players]}")
    print()
    
    # Jouer quelques tours et analyser
    for tour_num in range(1, 6):  # 5 premiers tours
        if game.is_game_over():
            break
            
        current_player = game.get_current_player()
        print(f"--- Tour {tour_num}: {current_player.name} ---")
        
        # Afficher l'état avant le tour
        print(f"Scores actuels: {[f'{p.name}:{p.get_score()}' for p in players]}")
        print(f"Tuiles au centre: {len(game.tiles_center)}")
        
        # Jouer le tour
        result, details = game.play_turn()
        
        # Afficher les résultats
        print(f"Résultat: {result.value}")
        if details.get('tile_taken'):
            tile = details['tile_taken']
            print(f"Tuile prise: {tile['value']} ({tile['worms']} vers)")
        
        # Afficher les insights de la stratégie analytique
        if current_player.name == "Analytical" and hasattr(current_player.strategy, 'adaptations'):
            if current_player.strategy.adaptations:
                print(f"Adaptations: {current_player.strategy.adaptations[-1]}")
        
        print()
        
        game.next_player()
    
    # Analyser l'historique
    print("=== Analyse de l'Historique ===")
    
    for player in players:
        stats = game.game_history.get_player_statistics(player.name)
        if stats:
            print(f"\n{player.name}:")
            print(f"  Tours joués: {stats['total_turns']}")
            print(f"  Taux de succès: {stats['success_rate']:.1%}")
            if stats['successful_turns'] > 0:
                print(f"  Score moyen sur succès: {stats['average_score_on_success']:.1f}")
                print(f"  Vers gagnés: {stats['total_worms_gained']}")
    
    # Afficher les derniers tours
    print(f"\n=== Derniers Tours ===")
    recent_turns = game.game_history.get_recent_turns(3)
    for turn in recent_turns:
        print(f"Tour {turn.turn_number}: {turn.player_name} - {turn.result.value}")
        if turn.tile_taken:
            print(f"  Tuile: {turn.tile_taken.value} ({turn.tile_taken.worms} vers)")


def compare_strategies_with_history():
    """Compare les stratégies en utilisant l'historique"""
    print("\n=== Comparaison de Stratégies avec Historique ===\n")
    
    strategies = [
        ("Conservative", ConservativeStrategy()),
        ("Aggressive", AggressiveStrategy()),
        ("Balanced", BalancedStrategy()),
        ("Analytical", AnalyticalStrategy()),
        ("Optimal", OptimalStrategy())
    ]
    
    results = {}
    
    # Simuler plusieurs parties
    for i in range(3):
        print(f"Partie {i+1}/3...")
        
        # Créer les joueurs pour cette partie
        players = [Player(name, strategy()) for name, strategy in strategies]
        
        # Simuler la partie
        result = simulate_game([p.name for p in players], [p.strategy for p in players])
        
        # Enregistrer les résultats
        for player_name, score in result['final_scores'].items():
            if player_name not in results:
                results[player_name] = []
            results[player_name].append(score)
    
    # Afficher les résultats
    print("\nRésultats finaux:")
    for strategy_name, scores in results.items():
        avg_score = sum(scores) / len(scores)
        print(f"{strategy_name}: {avg_score:.1f} vers en moyenne (parties: {scores})")


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

    # Démonstration des nouvelles stratégies
    demo_new_strategies()
    demo_tactical_choices()
    compare_tile_strategies()
    demo_targeted_strategy()

    # Nouvelles démonstrations pour RandomStrategy
    demo_random_strategy()
    test_random_vs_strategies()
    demo_chaos_game()

    # Démonstration de la stratégie optimale
    demo_optimal_strategy()
    analyze_winning_factors()

    # Démonstration du contexte enrichi
    demonstrate_enriched_context()
    compare_strategies_with_history()


if __name__ == "__main__":
    main()
