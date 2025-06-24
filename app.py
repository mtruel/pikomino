from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
from typing import Dict, Optional
import json
import threading
import time

from pikomino import (
    Player, PikominoGame, ConservativeStrategy, AggressiveStrategy,
    DiceValue, TurnResult, TurnState
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pikomino-secret-key-for-sessions'
socketio = SocketIO(app, cors_allowed_origins="*")

# Stockage des parties en cours
games: Dict[str, PikominoGame] = {}
game_sessions: Dict[str, str] = {}  # session_id -> game_id
game_modes: Dict[str, str] = {}  # game_id -> mode
step_by_step_games: Dict[str, Dict] = {}  # game_id -> step_by_step_config
emitted_turns: Dict[str, set] = {}  # game_id -> set de tours déjà émis


class HumanStrategy:
    """Stratégie pour les joueurs humains via l'interface web"""
    
    def __init__(self):
        self.pending_choice = None
        self.choice_made = False
        self.continue_turn = True
        self.current_turn_state = None
    
    def choose_dice_value(self, turn_state, player):
        # Cette méthode sera appelée par l'interface web
        choice = self.pending_choice
        self.pending_choice = None
        return choice
    
    def should_continue_turn(self, turn_state, player):
        return self.continue_turn
    
    def reset_turn(self):
        """Réinitialise l'état du tour"""
        self.pending_choice = None
        self.choice_made = False
        self.continue_turn = True
        self.current_turn_state = None


@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/game/<game_id>')
def game_view(game_id):
    """Vue de jeu"""
    if game_id not in games:
        return "Partie non trouvée", 404
    
    game = games[game_id]
    mode = game_modes.get(game_id, 'interactive')
    step_config = step_by_step_games.get(game_id, {})
    
    return render_template('game.html', 
                         game_id=game_id,
                         game_state=game.get_game_state(),
                         mode=mode,
                         step_config=step_config)


@app.route('/api/create_game', methods=['POST'])
def create_game():
    """Crée une nouvelle partie"""
    data = request.json
    player_names = data.get('players', ['Alice', 'Bob', 'Charlie'])
    mode = data.get('mode', 'interactive')
    strategies = data.get('strategies', [])  # Nouvelles stratégies spécifiées
    
    # Créer les joueurs selon le mode
    players = []
    if mode == 'interactive':
        # Premier joueur humain, autres IA avec stratégies spécifiées
        for i, name in enumerate(player_names):
            if i == 0:  # Premier joueur humain
                strategy = HumanStrategy()
            else:  # Autres joueurs IA avec stratégie spécifiée
                strategy_type = strategies[i-1] if i-1 < len(strategies) else 'conservative'
                strategy = ConservativeStrategy() if strategy_type == 'conservative' else AggressiveStrategy()
            players.append(Player(name, strategy))
    else:  # mode simulation
        # Tous les joueurs sont des IA avec stratégies spécifiées
        for i, name in enumerate(player_names):
            strategy_type = strategies[i] if i < len(strategies) else 'conservative'
            strategy = ConservativeStrategy() if strategy_type == 'conservative' else AggressiveStrategy()
            players.append(Player(name, strategy))
    
    # Créer la partie
    game = PikominoGame(players)
    game_id = str(uuid.uuid4())
    games[game_id] = game
    game_modes[game_id] = mode
    emitted_turns[game_id] = set()  # Initialiser le tracking des tours émis
    
    # Configuration par défaut pour le mode pas à pas
    if mode == 'simulation':
        step_by_step_games[game_id] = {
            'auto_play': False,
            'speed': 1.0,  # secondes entre chaque action
            'paused': True,
            'current_step': 0
        }
    
    return jsonify({
        'game_id': game_id,
        'game_state': game.get_game_state(),
        'mode': mode
    })


@app.route('/api/game/<game_id>/state')
def get_game_state(game_id):
    """Récupère l'état actuel de la partie"""
    if game_id not in games:
        return jsonify({'error': 'Partie non trouvée'}), 404
    
    game = games[game_id]
    mode = game_modes.get(game_id, 'interactive')
    step_config = step_by_step_games.get(game_id, {})
    
    return jsonify({
        **game.get_game_state(),
        'mode': mode,
        'step_config': step_config
    })


@app.route('/api/game/<game_id>/available_tiles/<int:score>')
def get_available_tiles(game_id, score):
    """Récupère les tuiles disponibles pour un score donné"""
    if game_id not in games:
        return jsonify({'error': 'Partie non trouvée'}), 404
    
    game = games[game_id]
    current_player = game.get_current_player()
    
    # Tuiles du centre disponibles
    center_tiles = [
        {
            'value': tile.value,
            'worms': tile.worms,
            'source': 'center',
            'player': None
        }
        for tile in game.tiles_center 
        if tile.value <= score
    ]
    
    # Tuiles volables chez les autres joueurs (score exact)
    stealable_tiles = []
    for player in game.players:
        if player != current_player:
            top_tile = player.get_top_tile()
            if top_tile and top_tile.value == score:
                stealable_tiles.append({
                    'value': top_tile.value,
                    'worms': top_tile.worms,
                    'source': 'player',
                    'player': player.name
                })
    
    return jsonify({
        'center_tiles': center_tiles,
        'stealable_tiles': stealable_tiles,
        'best_center_tile': max(center_tiles, key=lambda t: t['value']) if center_tiles else None,
        'stealable_available': len(stealable_tiles) > 0
    })


@app.route('/api/game/<game_id>/play_turn', methods=['POST'])
def play_turn(game_id):
    """Joue un tour automatique (pour l'IA)"""
    if game_id not in games:
        return jsonify({'error': 'Partie non trouvée'}), 404
    
    game = games[game_id]
    current_player = game.get_current_player()
    
    # Vérifier si c'est un joueur IA ou mode simulation
    mode = game_modes.get(game_id, 'interactive')
    if mode == 'interactive' and isinstance(current_player.strategy, HumanStrategy):
        return jsonify({'error': 'Tour du joueur humain'}), 400
    
    # Sauvegarder le nom du joueur avant de jouer le tour
    player_name = current_player.name
    
    # Jouer le tour
    result, details = game.play_turn()
    game.next_player()
    
    # Convertir les objets non-sérialisables en JSON
    serializable_details = details.copy()
    if 'result' in serializable_details and hasattr(serializable_details['result'], 'value'):
        serializable_details['result'] = serializable_details['result'].value
    
    # Émettre les détails du tour aux clients connectés
    emit_turn_played(game_id, result, details, player_name, is_human=False)
    
    return jsonify({
        'result': result.value,
        'details': serializable_details,
        'game_state': game.get_game_state()
    })


@app.route('/api/game/<game_id>/step_control', methods=['POST'])
def step_control(game_id):
    """Contrôle le mode pas à pas"""
    if game_id not in games:
        return jsonify({'error': 'Partie non trouvée'}), 404
    
    if game_id not in step_by_step_games:
        return jsonify({'error': 'Partie non en mode simulation'}), 400
    
    data = request.json
    action = data.get('action')
    
    step_config = step_by_step_games[game_id]
    
    if action == 'play':
        step_config['paused'] = False
        if not step_config['auto_play']:
            # Jouer un seul pas
            play_turn(game_id)
            step_config['paused'] = True
    elif action == 'pause':
        step_config['paused'] = True
    elif action == 'auto_play':
        step_config['auto_play'] = data.get('enabled', True)
        step_config['paused'] = not step_config['auto_play']
        if step_config['auto_play']:
            start_auto_play(game_id)
    elif action == 'set_speed':
        step_config['speed'] = max(0.1, min(5.0, data.get('speed', 1.0)))
    
    socketio.emit('step_config_updated', step_config, room=game_id)
    
    return jsonify(step_config)


def start_auto_play(game_id):
    """Démarre le jeu automatique en arrière-plan"""
    def auto_play_worker():
        game = games.get(game_id)
        step_config = step_by_step_games.get(game_id)
        
        if not game or not step_config:
            return
        
        while (not game.is_game_over() and 
               step_config['auto_play'] and 
               not step_config['paused']):
            
                         # Jouer un tour
            current_player = game.get_current_player()
            # Sauvegarder le nom du joueur avant de jouer le tour
            player_name = current_player.name
            result, details = game.play_turn()
            game.next_player()
            
            # Convertir les objets non-sérialisables en JSON
            serializable_details = details.copy()
            if 'result' in serializable_details and hasattr(serializable_details['result'], 'value'):
                serializable_details['result'] = serializable_details['result'].value
            
            # Émettre les détails aux clients
            emit_turn_played(game_id, result, details, player_name, is_human=False)
            
            # Attendre selon la vitesse configurée
            time.sleep(step_config['speed'])
        
        # Arrêter l'auto-play si la partie est finie
        if game.is_game_over():
            step_config['auto_play'] = False
            step_config['paused'] = True
            socketio.emit('step_config_updated', step_config, room=game_id)
    
    # Lancer dans un thread séparé
    thread = threading.Thread(target=auto_play_worker)
    thread.daemon = True
    thread.start()


@socketio.on('join_game')
def on_join_game(data):
    """Un joueur rejoint une partie"""
    game_id = data['game_id']
    if game_id in games:
        join_room(game_id)
        game_sessions[session.get('session_id', str(uuid.uuid4()))] = game_id
        
        # Envoyer l'état complet du jeu
        game_state = games[game_id].get_game_state()
        mode = game_modes.get(game_id, 'interactive')
        step_config = step_by_step_games.get(game_id, {})
        
        emit('game_state', {
            **game_state,
            'mode': mode,
            'step_config': step_config
        })


@socketio.on('leave_game')
def on_leave_game(data):
    """Un joueur quitte une partie"""
    game_id = data['game_id']
    leave_room(game_id)
    session_id = session.get('session_id')
    if session_id in game_sessions:
        del game_sessions[session_id]


@socketio.on('roll_dice')
def on_roll_dice(data):
    """Lance les dés pour le joueur actuel"""
    game_id = data['game_id']
    
    if game_id not in games:
        emit('error', {'message': 'Partie non trouvée'})
        return
    
    game = games[game_id]
    current_player = game.get_current_player()
    
    # Vérifier si c'est un joueur humain
    if not isinstance(current_player.strategy, HumanStrategy):
        emit('error', {'message': 'Ce n\'est pas votre tour'})
        return
    
    # Simuler le lancement de dés
    from pikomino import Dice
    remaining_dice = data.get('remaining_dice', 8)
    roll = [Dice.roll() for _ in range(remaining_dice)]
    
    # Créer ou mettre à jour l'état du tour
    if not current_player.strategy.current_turn_state:
        current_player.strategy.current_turn_state = TurnState()
    
    turn_state = current_player.strategy.current_turn_state
    turn_state.current_roll = roll
    turn_state.remaining_dice = remaining_dice
    
    # Filtrer les valeurs disponibles (non utilisées)
    available_values = [v for v in roll if v not in turn_state.used_values]
    
    emit('dice_rolled', {
        'dice': [die.name for die in roll],
        'remaining': remaining_dice,
        'current_score': turn_state.get_total_score(),
        'has_worm': turn_state.has_worm(),
        'available_values': [v.name for v in available_values],
        'used_values': [v.name for v in turn_state.used_values]
    }, room=game_id)


@socketio.on('choose_dice_value')
def on_choose_dice_value(data):
    """Le joueur choisit une valeur de dé"""
    game_id = data['game_id']
    chosen_value = data['value']
    
    if game_id not in games:
        emit('error', {'message': 'Partie non trouvée'})
        return
    
    game = games[game_id]
    current_player = game.get_current_player()
    
    if not isinstance(current_player.strategy, HumanStrategy):
        emit('error', {'message': 'Ce n\'est pas votre tour'})
        return
    
    try:
        # Convertir la valeur string en DiceValue
        dice_value = DiceValue[chosen_value.upper()]
        turn_state = current_player.strategy.current_turn_state
        
        if not turn_state:
            emit('error', {'message': 'Le tour n\'a pas commencé'})
            return
        
        # Vérifier si la valeur peut être choisie
        if not turn_state.can_reserve_value(dice_value):
            if dice_value in turn_state.used_values:
                emit('error', {'message': 'Cette valeur a déjà été choisie'})
            else:
                emit('error', {'message': 'Cette valeur n\'est pas disponible'})
            return
        
        # Mettre à jour l'état du tour
        count = turn_state.current_roll.count(dice_value)
        if dice_value in turn_state.reserved_dice:
            turn_state.reserved_dice[dice_value] += count
        else:
            turn_state.reserved_dice[dice_value] = count
        
        turn_state.used_values.add(dice_value)
        turn_state.remaining_dice -= count
        
        # Préparer les détails du tour
        turn_details = {
            'reserved_dice': [k.name for k in turn_state.reserved_dice.keys() for _ in range(turn_state.reserved_dice[k])],
            'remaining_dice_count': turn_state.remaining_dice,
            'current_score': turn_state.get_total_score(),
            'has_worm': turn_state.has_worm(),
            'can_take_tile': turn_state.has_worm() and turn_state.get_total_score() >= 21,
            'used_values': [v.name for v in turn_state.used_values]
        }
        
        # Émettre la mise à jour
        socketio.emit('choice_made', {
            'success': True,
            'details': turn_details
        }, room=game_id)
        
    except KeyError:
        emit('error', {'message': 'Valeur de dé invalide'})
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('choose_tile')
def on_choose_tile(data):
    """Le joueur choisit une tuile spécifique à prendre"""
    game_id = data['game_id']
    tile_choice = data.get('tile_choice')  # {'source': 'center'/'player', 'value': int, 'player': str}
    
    if game_id not in games:
        emit('error', {'message': 'Partie non trouvée'})
        return
    
    game = games[game_id]
    current_player = game.get_current_player()
    
    if not isinstance(current_player.strategy, HumanStrategy):
        emit('error', {'message': 'Ce n\'est pas votre tour'})
        return
    
    turn_state = current_player.strategy.current_turn_state
    if not turn_state:
        emit('error', {'message': 'Aucun état de tour trouvé'})
        return
    
    # Calculer le score final et vérifier les vers
    final_score = turn_state.get_total_score()
    has_worm = turn_state.has_worm()
    
    if not has_worm:
        emit('error', {'message': 'Vous devez avoir au moins un ver pour prendre une tuile'})
        return
    
    # Trouver la tuile spécifique
    tile_to_take = None
    
    if tile_choice['source'] == 'center':
        # Chercher dans les tuiles du centre
        for tile in game.tiles_center:
            if tile.value == tile_choice['value']:
                if final_score >= tile.value:
                    tile_to_take = tile
                break
    elif tile_choice['source'] == 'player':
        # Chercher chez le joueur spécifié
        target_player = None
        for player in game.players:
            if player.name == tile_choice['player']:
                target_player = player
                break
        
        if target_player:
            top_tile = target_player.get_top_tile()
            if top_tile and top_tile.value == tile_choice['value'] and final_score == tile_choice['value']:
                tile_to_take = top_tile
    
    if tile_to_take is None:
        emit('error', {'message': 'Tuile non disponible'})
        return
    
    # Prendre la tuile
    success = game.take_tile(tile_to_take)
    if not success:
        emit('error', {'message': 'Erreur lors de la prise de tuile'})
        return
    
    # Préparer les détails du tour
    turn_details = {
        'player': current_player.name,
        'final_score': final_score,
        'final_has_worm': has_worm,
        'reserved_dice': {k.name: v for k, v in turn_state.reserved_dice.items()},
        'result': TurnResult.SUCCESS,
        'tile_taken': {
            'value': tile_to_take.value, 
            'worms': tile_to_take.worms,
            'source': tile_choice['source'],
            'stolen_from': tile_choice.get('player')
        }
    }
    
    # Ajouter à l'historique
    game.turn_history.append(turn_details)
    
    # Réinitialiser l'état du tour et passer au joueur suivant
    current_player.strategy.reset_turn()
    game.next_player()
    
    # Réinitialiser l'état du tour du nouveau joueur actuel s'il est humain
    new_current_player = game.get_current_player()
    if isinstance(new_current_player.strategy, HumanStrategy):
        new_current_player.strategy.reset_turn()
    
    # Émettre le résultat
    emit_turn_played(game_id, TurnResult.SUCCESS, turn_details, current_player.name, is_human=True)
    
    # Déclencher automatiquement les tours des joueurs IA suivants
    def play_ai_turns():
        time.sleep(1)
        while not game.is_game_over():
            current_player = game.get_current_player()
            if not isinstance(current_player.strategy, HumanStrategy):
                player_name = current_player.name
                result, details = game.play_turn()
                game.next_player()
                
                serializable_details = details.copy()
                if 'result' in serializable_details and hasattr(serializable_details['result'], 'value'):
                    serializable_details['result'] = serializable_details['result'].value
                
                emit_turn_played(game_id, result, details, player_name, is_human=False)
                time.sleep(2)
            else:
                break
    
    ai_thread = threading.Thread(target=play_ai_turns)
    ai_thread.daemon = True
    ai_thread.start()


@socketio.on('end_turn')
def on_end_turn(data):
    """Le joueur termine son tour (ancienne méthode pour compatibilité)"""
    game_id = data['game_id']
    
    if game_id not in games:
        emit('error', {'message': 'Partie non trouvée'})
        return
    
    game = games[game_id]
    current_player = game.get_current_player()
    
    if isinstance(current_player.strategy, HumanStrategy):
        turn_state = current_player.strategy.current_turn_state
        
        if not turn_state:
            emit('error', {'message': 'Aucun état de tour trouvé'})
            return
        
        # Calculer le score final et vérifier les vers
        final_score = turn_state.get_total_score()
        has_worm = turn_state.has_worm()
        
        # Préparer les détails du tour
        turn_details = {
            'player': current_player.name,
            'final_score': final_score,
            'final_has_worm': has_worm,
            'reserved_dice': {k.name: v for k, v in turn_state.reserved_dice.items()},
            'result': None,
            'tile_taken': None
        }
        
        # Déterminer le résultat du tour
        if not has_worm:
            # Échec : pas de ver
            game.handle_failed_turn()
            result = TurnResult.FAILED_NO_WORM
            turn_details['result'] = result
        else:
            # Essayer de prendre une tuile automatiquement (ancienne logique)
            tile_to_take = game.find_tile_to_take(final_score, has_worm)
            if tile_to_take is None:
                # Échec : score insuffisant
                game.handle_failed_turn()
                result = TurnResult.FAILED_INSUFFICIENT_SCORE
                turn_details['result'] = result
            else:
                # Succès : prendre la tuile
                game.take_tile(tile_to_take)
                result = TurnResult.SUCCESS
                turn_details['result'] = result
                turn_details['tile_taken'] = {'value': tile_to_take.value, 'worms': tile_to_take.worms}
        
        # Ajouter à l'historique
        game.turn_history.append(turn_details)
        
        # Réinitialiser l'état du tour du joueur actuel avant de passer au suivant
        current_player.strategy.reset_turn()
        
        # Passer au joueur suivant
        game.next_player()
        
        # Réinitialiser l'état du tour du nouveau joueur actuel s'il est humain
        new_current_player = game.get_current_player()
        if isinstance(new_current_player.strategy, HumanStrategy):
            new_current_player.strategy.reset_turn()
        
        # Convertir les objets non-sérialisables en JSON
        serializable_details = turn_details.copy()
        if 'result' in serializable_details and hasattr(serializable_details['result'], 'value'):
            serializable_details['result'] = serializable_details['result'].value
        
        # Émettre le résultat final du tour
        emit_turn_played(game_id, result, turn_details, current_player.name, is_human=True)
        
        # Déclencher automatiquement les tours des joueurs IA suivants
        def play_ai_turns():
            time.sleep(1)  # Petite pause pour que l'interface se mette à jour
            while not game.is_game_over():
                current_player = game.get_current_player()
                # Si c'est un joueur IA, jouer automatiquement
                if not isinstance(current_player.strategy, HumanStrategy):
                    # Sauvegarder le nom du joueur avant de jouer le tour
                    player_name = current_player.name
                    result, details = game.play_turn()
                    game.next_player()
                    
                    # Convertir les objets non-sérialisables en JSON
                    serializable_details = details.copy()
                    if 'result' in serializable_details and hasattr(serializable_details['result'], 'value'):
                        serializable_details['result'] = serializable_details['result'].value
                    
                    # Émettre les détails du tour aux clients connectés
                    emit_turn_played(game_id, result, details, player_name, is_human=False)
                    
                    time.sleep(2)  # Pause entre les tours IA pour suivre le jeu
                else:
                    # C'est le tour d'un joueur humain, on s'arrête
                    break
        
        # Lancer les tours IA dans un thread séparé
        ai_thread = threading.Thread(target=play_ai_turns)
        ai_thread.daemon = True
        ai_thread.start()


def emit_turn_played(game_id, result, details, player_name, is_human=False):
    """Fonction utilitaire pour émettre turn_played sans doublons"""
    
    # Créer un identifiant unique pour ce tour
    turn_id = f"{player_name}_{details.get('final_score', 0)}_{result.value if hasattr(result, 'value') else result}_{len(games[game_id].turn_history)}"
    
    # Initialiser le set pour ce jeu si nécessaire
    if game_id not in emitted_turns:
        emitted_turns[game_id] = set()
    
    # Vérifier si ce tour a déjà été émis
    if turn_id in emitted_turns[game_id]:
        print(f"⚠️  Tour déjà émis, ignoré: {turn_id}")
        return
    
    # Marquer ce tour comme émis
    emitted_turns[game_id].add(turn_id)
    
    # Convertir les objets non-sérialisables en JSON
    serializable_details = details.copy()
    if 'result' in serializable_details and hasattr(serializable_details['result'], 'value'):
        serializable_details['result'] = serializable_details['result'].value
    
    print(f"📤 Émission turn_played: {player_name} - {turn_id}")
    
    socketio.emit('turn_played', {
        'result': result.value if hasattr(result, 'value') else result,
        'details': serializable_details,
        'game_state': games[game_id].get_game_state(),
        'player': player_name,
        'is_human': is_human
    }, room=game_id)


def create_app():
    """Factory pour créer l'application Flask"""
    return app


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 