import os
import random
from flask import Flask, render_template, url_for, send_from_directory, session, redirect

app = Flask(__name__)
app.secret_key = 'super_secret_key'

SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']

def get_deck():
    return [{'rank': rank, 'suit': suit} for suit in SUITS for rank in RANKS]

def card_filename(card):
    return f"{card['rank']} of {card['suit']}.png"

@app.route('/start')
def start():
    session['tokens'] = 100  # Reset tokens at the start of each game
    deck = get_deck()
    random.shuffle(deck)
    player_hand = [deck.pop(), deck.pop()]
    ai_hand = [deck.pop(), deck.pop()]
    community = [deck.pop() for _ in range(5)]
    tokens = session.get('tokens', 100)
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

if __name__ == '__main__':
    app.run(debug=True)