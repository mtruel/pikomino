#!/usr/bin/env python3
"""
Point d'entrée principal pour l'application Pikomino
"""

import sys
import argparse
import matplotlib.pyplot as plt
import statistics
from collections import defaultdict
import colorsys
from pikomino import (
    Player, PikominoGame, ConservativeStrategy, AggressiveStrategy,
    simulate_game
)


def generate_distinct_colors(n):
    """Génère n couleurs distinctes"""
    colors = []
    for i in range(n):
        # Utilise le cercle chromatique pour générer des couleurs espacées
        hue = i / n
        # Saturation et luminosité fixes pour des couleurs vives mais pas trop claires
        saturation = 0.7
        value = 0.9
        # Convertir HSV en RGB
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        # Convertir en format hexadécimal
        hex_color = '#%02x%02x%02x' % tuple(int(x * 255) for x in rgb)
        colors.append(hex_color)
    return colors


def run_console_demo():
    """Lance une démonstration en console"""
    print("🎲 PIKOMINO - DÉMONSTRATION 🐛")
    print("=" * 50)
    
    # Créer des joueurs avec différentes stratégies
    players = [
        Player("Alice", ConservativeStrategy()),
        Player("Bob", AggressiveStrategy()),
        Player("Charlie", ConservativeStrategy())
    ]
    
    # Lancer une partie
    game = PikominoGame(players)
    
    print("État initial:")
    print(f"Tuiles disponibles: {len(game.tiles_center)}")
    for player in players:
        print(f"{player.name}: {player.get_score()} vers")
    
    # Jouer quelques tours pour la démonstration
    for turn in range(10):
        if game.is_game_over():
            break
        
        current_player = game.get_current_player()
        print(f"\n--- Tour {turn + 1}: {current_player.name} ---")
        
        result, details = game.play_turn()
        print(f"Résultat: {result.value}")
        print(f"Score: {current_player.get_score()} vers")
        
        game.next_player()
    
    # Afficher l'état final
    print("\n" + "=" * 50)
    print("ÉTAT FINAL")
    print("=" * 50)
    for player in players:
        print(f"{player.name}: {player.get_score()} vers ({len(player.tiles)} tuiles)")
    
    print(f"\nTuiles restantes au centre: {len(game.tiles_center)}")
    
    if game.is_game_over():
        winner = game.get_winner()
        print(f"\nGagnant: {winner.name} avec {winner.get_score()} vers! 🎉")


def run_simulation(num_games=10):
    """Lance une simulation de plusieurs parties"""
    print(f"🎯 SIMULATION DE {num_games} PARTIES")
    print("=" * 50)
    
    # Créer les joueurs et leurs stratégies
    player_names = ["Conservative", "Aggressive", "Conservative2"]
    game_strategies = [ConservativeStrategy(), AggressiveStrategy(), ConservativeStrategy()]
    
    # Générer les couleurs dynamiquement
    colors = generate_distinct_colors(len(player_names))
    strategy_colors = dict(zip(player_names, colors))
    
    # Statistiques détaillées pour chaque stratégie
    stats = defaultdict(lambda: {
        'wins': 0,
        'scores': [],
        'tiles_kept': [],
        'turns_per_game': [],
        'failed_turns': 0,
        'successful_turns': 0
    })
    
    for game_num in range(num_games):
        print(f"\rPartie {game_num + 1}/{num_games}", end="", flush=True)
        
        # Créer une nouvelle partie
        players = [Player(name, strategy) for name, strategy in zip(player_names, game_strategies)]
        game = PikominoGame(players)
        
        # Jouer la partie complète
        turn_count = 0
        while not game.is_game_over():
            current_player = game.get_current_player()
            result, details = game.play_turn()
            
            # Collecter les statistiques du tour
            if result.value == "success":
                stats[current_player.name]['successful_turns'] += 1
            else:
                stats[current_player.name]['failed_turns'] += 1
            
            game.next_player()
            turn_count += 1
        
        # Collecter les statistiques de fin de partie
        winner = game.get_winner()
        stats[winner.name]['wins'] += 1
        
        for player in players:
            stats[player.name]['scores'].append(player.get_score())
            stats[player.name]['tiles_kept'].append(len(player.tiles))
        
        # Enregistrer le nombre de tours pour cette partie
        for player in players:
            stats[player.name]['turns_per_game'].append(turn_count // len(players))
    
    print("\n\nRésultats détaillés:")
    print("=" * 50)
    
    # Afficher les statistiques
    for player_name, player_stats in stats.items():
        wins = player_stats['wins']
        win_rate = (wins / num_games) * 100
        avg_score = statistics.mean(player_stats['scores'])
        avg_tiles = statistics.mean(player_stats['tiles_kept'])
        avg_turns = statistics.mean(player_stats['turns_per_game'])
        success_rate = (player_stats['successful_turns'] / 
                       (player_stats['successful_turns'] + player_stats['failed_turns'])) * 100
        
        print(f"\n{player_name}:")
        print(f"  Victoires: {wins}/{num_games} ({win_rate:.1f}%)")
        print(f"  Score moyen: {avg_score:.1f} vers")
        print(f"  Tuiles moyennes: {avg_tiles:.1f}")
        print(f"  Tours moyens: {avg_turns:.1f}")
        print(f"  Taux de réussite des tours: {success_rate:.1f}%")
    
    # Configuration générale des graphiques
    plt.rcParams['figure.figsize'] = (15, 10)
    plt.rcParams['axes.grid'] = True
    
    fig = plt.figure()
    
    def create_bar_plot(ax, values, title, ylabel, percentage=False):
        """Fonction utilitaire pour créer un graphique à barres"""
        bars = ax.bar(players, values, color=[strategy_colors[p] for p in players])
        ax.set_title(title, pad=20, fontsize=12, fontweight='bold')
        ax.set_ylabel(ylabel)
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Ajouter les valeurs au-dessus des barres
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:.1f}{"%" if percentage else ""}',
                   ha='center', va='bottom')
        
        # Ajuster les marges et rotations des labels
        ax.tick_params(axis='x', rotation=45)
        if percentage:
            ax.set_ylim(0, 100)
    
    # 1. Taux de victoire
    ax1 = plt.subplot(2, 2, 1)
    players = list(stats.keys())
    win_rates = [(stats[p]['wins'] / num_games) * 100 for p in players]
    create_bar_plot(ax1, win_rates, 'Taux de victoire', 'Pourcentage (%)', percentage=True)
    
    # 2. Score moyen
    ax2 = plt.subplot(2, 2, 2)
    avg_scores = [statistics.mean(stats[p]['scores']) for p in players]
    create_bar_plot(ax2, avg_scores, 'Score moyen (vers)', 'Nombre de vers')
    
    # 3. Taux de réussite des tours
    ax3 = plt.subplot(2, 2, 3)
    success_rates = [(stats[p]['successful_turns'] / 
                     (stats[p]['successful_turns'] + stats[p]['failed_turns'])) * 100 
                    for p in players]
    create_bar_plot(ax3, success_rates, 'Taux de réussite des tours', 'Pourcentage (%)', percentage=True)
    
    # 4. Nombre moyen de tuiles conservées
    ax4 = plt.subplot(2, 2, 4)
    avg_tiles = [statistics.mean(stats[p]['tiles_kept']) for p in players]
    create_bar_plot(ax4, avg_tiles, 'Nombre moyen de tuiles conservées', 'Nombre de tuiles')
    
    # Ajuster la mise en page
    plt.tight_layout(pad=3.0)
    
    # Ajouter une légende commune
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, label=strat) 
                      for strat, color in strategy_colors.items()]
    fig.legend(handles=legend_elements, loc='center right', bbox_to_anchor=(0.98, 0.5))
    
    # Sauvegarder le graphique
    plt.savefig('simulation_results.png', bbox_inches='tight', dpi=300)
    print("\nGraphiques sauvegardés dans 'simulation_results.png'")


def run_web_app():
    """Lance l'interface web Flask"""
    try:
        from app import app, socketio
        print("🌐 LANCEMENT DE L'INTERFACE WEB")
        print("=" * 50)
        print("Accédez à l'interface sur: http://localhost:5000")
        print("Appuyez sur Ctrl+C pour arrêter")
        print("=" * 50)
        
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    except ImportError:
        print("❌ Erreur: Flask n'est pas installé.")
        print("Installez les dépendances avec: pip install flask flask-socketio")
        sys.exit(1)


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Pikomino - Simulateur de jeu")
    parser.add_argument(
        'mode', 
        choices=['web', 'demo', 'simulate'], 
        help='Mode d\'exécution: web (interface), demo (console), simulate (simulation)'
    )
    parser.add_argument(
        '--games', 
        type=int, 
        default=10, 
        help='Nombre de parties à simuler (mode simulate uniquement)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'web':
            run_web_app()
        elif args.mode == 'demo':
            run_console_demo()
        elif args.mode == 'simulate':
            run_simulation(args.games)
    except KeyboardInterrupt:
        print("\n\n👋 Au revoir !")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
