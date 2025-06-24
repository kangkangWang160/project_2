import os
import random
from flask import Flask, render_template, url_for, send_from_directory, session, redirect, request, jsonify

app = Flask(__name__)
app.secret_key = 'super_secret_key'

SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']

def get_deck():
    return [{'rank': rank, 'suit': suit} for suit in SUITS for rank in RANKS]

def card_filename(card):
    return f"{card['rank']} of {card['suit']}.png"

def evaluate_hand_strength(hand):
    # Very basic: pairs are strong, high cards are medium, else weak
    ranks = [card['rank'] for card in hand]
    rank_counts = {r: ranks.count(r) for r in ranks}
    if 2 in rank_counts.values():
        return 'strong'  # Pair
    high_cards = {'ace', 'king', 'queen', 'jack', '10'}
    if any(r in high_cards for r in ranks):
        return 'medium'
    return 'weak'

@app.route('/start')
def start():
    session['tokens'] = 100  # Reset tokens at the start of each game
    session['ai_tokens'] = 100
    session['player_bet'] = 0
    session['ai_bet'] = 0
    deck = get_deck()
    random.shuffle(deck)
    player_hand = [deck.pop(), deck.pop()]
    ai_hand = [deck.pop(), deck.pop()]
    session['ai_hand'] = str(ai_hand)
    community = [deck.pop() for _ in range(5)]
    tokens = session.get('tokens', 100)
    ai_tokens = session.get('ai_tokens', 100)
    player_bet = session.get('player_bet', 0)
    ai_bet = session.get('ai_bet', 0)
    # Choose token image based on token count (no underscores in filenames)
    if tokens < 20:
        token_img = 'token.png'
    elif tokens <= 70:
        token_img = 'low tokens.jpg'
    elif tokens <= 130:
        token_img = 'starter tokens.png'
    else:
        token_img = 'high tokens.png'
    return render_template(
        'table.html',
        player_hand=player_hand,
        ai_hand=ai_hand,
        community=community,
        card_filename=card_filename,
        tokens=tokens,
        ai_tokens=ai_tokens,
        player_bet=player_bet,
        ai_bet=ai_bet,
        token_img=token_img
    )

@app.route('/')
def home():
    return render_template('index.html')

# Explicit static file serving route for cards (in case Flask static is misconfigured)
@app.route('/cards/<path:filename>')
def custom_cards(filename):
    cards_dir = os.path.join(app.root_path, 'static', 'cards')
    file_path = os.path.join(cards_dir, filename)
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
    return send_from_directory(cards_dir, filename)

# Test route to list and show all card images
@app.route('/test_cards')
def test_cards():
    cards_dir = os.path.join(app.root_path, 'static', 'cards')
    files = []
    if os.path.exists(cards_dir):
        files = [f for f in os.listdir(cards_dir) if f.endswith('.png')]
    else:
        print(f"[ERROR] Directory not found: {cards_dir}")
    return render_template('test_cards.html', files=files)

@app.route('/bet', methods=['POST'])
def bet():
    data = request.get_json()
    player_bet = int(data.get('player_bet', 1))
    tokens = session.get('tokens', 100)
    if player_bet < 1 or player_bet > tokens:
        return jsonify({'error': 'Invalid bet amount'}), 400
    # Deduct player bet
    tokens -= player_bet
    session['tokens'] = tokens
    session['player_bet'] = session.get('player_bet', 0) + player_bet
    # AI logic: use hand strength
    ai_tokens = session.get('ai_tokens', 100)
    ai_bet = 0
    ai_action = 'check'
    ai_hand = session.get('ai_hand')
    if not ai_hand:
        ai_hand = [
            {'rank': '2', 'suit': 'hearts'},
            {'rank': '7', 'suit': 'clubs'}
        ]
    else:
        # If stored as string, convert to dict
        import ast
        if isinstance(ai_hand, str):
            ai_hand = ast.literal_eval(ai_hand)
    strength = evaluate_hand_strength(ai_hand)
    import random
    if ai_tokens > 0:
        if strength == 'strong':
            if player_bet < 10:
                ai_bet = min(player_bet + random.randint(5, 15), ai_tokens)
                ai_action = 'raise'
            else:
                ai_bet = min(player_bet, ai_tokens)
                ai_action = 'call'
        elif strength == 'medium':
            if player_bet <= 10:
                ai_bet = min(player_bet, ai_tokens)
                ai_action = 'call'
            else:
                ai_bet = 0
                ai_action = 'check'
        else:
            if player_bet <= 5:
                ai_bet = min(player_bet, ai_tokens)
                ai_action = 'call'
            else:
                ai_bet = 0
                ai_action = 'check'
    ai_tokens -= ai_bet
    session['ai_tokens'] = ai_tokens
    session['ai_bet'] = session.get('ai_bet', 0) + ai_bet
    return jsonify({
        'player_bet': session['player_bet'],
        'ai_bet': session['ai_bet'],
        'tokens': tokens,
        'ai_tokens': ai_tokens,
        'ai_action': ai_action,
        'ai_bet_amount': ai_bet
    })

if __name__ == '__main__':
    app.run(debug=True)