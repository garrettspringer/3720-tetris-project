"""Game of Tetris for Liftoff Interview

Written by Grant Jenks
Copyright 2019

"""

import atexit
import collections
import itertools
import random
import sqlite3
import threading
import time

import pygame

class Game:
    "Game state for Tetris."
    def __init__(self, width, height, seed=None):
        self.random = random.Random(seed)
        self.width = width
        self.height = height
        self.board = collections.defaultdict(lambda: '#')
        for x in range(width):
            for y in range(height):
                self.board[x, y] = ' '
        self.active = True
        self.speed = 20
        self.next_letter = self.random.choice('IJLOSTZ')
        self.piece = self.next_piece()
        self.score = 0
        self.stash = None
        pygame.init()

    def draw(self):
        "Draw game state."
        print('Score:', self.score, end='\r\n')
        print('Level:', self.score // 4 + 1, end='\r\n')
        print('Next piece:', self.next_letter, end='\r\n')
        print('Stash piece:', 'no' if self.stash is None else 'yes', end='\r\n')
        print('*' * (self.width + 2), end='\r\n')
        for y in range(self.height):
            print('|', end='')
            for x in range(self.width):
                if (x, y) in self.piece:
                    print('@', end='')
                else:
                    print(self.board[x, y], end='')
            print('|', end='\r\n')
        print('*' * (self.width + 2), end='\r\n')

    def next_piece(self):
        "Create a new piece, on collision set active to False."
        letter = self.next_letter
        self.next_letter = self.random.choice('IJLOSTZ')
        if letter == 'I':
            piece = {(0, 0), (0, 1), (0, 2), (0, 3)}
        elif letter == 'J':
            piece = {(1, 0), (1, 1), (1, 2), (0, 2)}
        elif letter == 'L':
            piece = {(0, 0), (0, 1), (0, 2), (1, 2)}
        elif letter == 'O':
            piece = {(0, 0), (0, 1), (1, 0), (1, 1)}
        elif letter == 'S':
            piece = {(0, 1), (1, 0), (1, 1), (2, 0)}
        elif letter == 'T':
            piece = {(0, 0), (1, 0), (2, 0), (1, 1)}
        else:
            assert letter == 'Z'
            piece = {(0, 0), (1, 0), (1, 1), (2, 1)}
        offset = self.width // 2 - 1
        piece = {(x + offset, y) for x, y in piece}
        if self.collide(piece):
            self.end()
        return piece

    def end(self):
        self.active = False
        print('Game over! Press any key to quit.', end='\r\n')

    def tick(self, mark):
        "Notify the game of a clock tick."
        if mark % self.speed == 0:
            moved = self.move_piece(0, 1)
            if not moved:
                for x, y in self.piece:
                    self.board[x, y] = '#'
                self.collapse()
                self.piece = self.next_piece()
            self.draw()

    def collapse(self):
        "Collapse full lines."
        y = self.height - 1
        while y >= 0:
            full_line = all(self.board[x, y] == '#' for x in range(self.width))
            if full_line:
                z = y
                while z > 0:
                    for x in range(self.width):
                        self.board[x, z] = self.board[x, z - 1]
                    z -= 1
                for x in range(self.width):
                    self.board[x, 0] = ' '
                self.score += 1
                if self.score % 4 == 0:
                    self.speed -= 1
            else:
                y -= 1

    def collide(self, piece):
        "Check whether piece collides with others on board."
        return any(self.board[x, y] != ' ' for x, y in piece)

    def move_piece(self, x, y):
        "Move piece by delta x and y."
        new_piece = {(a + x, y + b) for a, b in self.piece}
        if self.collide(new_piece):
            return False
        self.piece = new_piece
        return True

    def rotate_piece(self):
        "Rotate piece."
        min_x = min(x for x, y in self.piece)
        max_x = max(x for x, y in self.piece)
        diff_x = max_x - min_x
        min_y = min(y for x, y in self.piece)
        max_y = max(y for x, y in self.piece)
        diff_y = max_y - min_y
        size = max(diff_x, diff_y)
        new_piece = set()
        for x, y in self.piece:
            pair = (min_x + size) - (y - min_y), min_y + (x - min_x)
            new_piece.add(pair)
        if self.collide(new_piece):
            return False
        self.piece = new_piece
        return True

    def move(self, key):
        "Update game state based on key press."
        if key == 'left':
            moved = self.move_piece(-1, 0)
        elif key == 'right':
            moved = self.move_piece(1, 0)
        elif key == 'down':
            moved = self.move_piece(0, 1)
        elif key == 'up':
            moved = self.rotate_piece()
        elif key == 'swap':
            if self.stash is None:
                self.stash = self.piece
                self.piece = self.next_piece()
            else:
                self.piece, self.stash = self.stash, self.piece
            if self.collide(self.piece):
                self.end()
            moved = True
        else:
            assert key == 'space'
            moved = self.move_piece(0, 1)
            while moved:
                moved = self.move_piece(0, 1)
            moved = True
        if moved:
            self.draw()


def draw_loop(game):
    """Draw loop.

    Handle console drawing in a separate thread.

    """
    game.draw()
    counter = itertools.count(start=1)
    while game.active:
        mark = next(counter)
        game.tick(mark)
        time.sleep(0.1)


def input_loop(game):
    """Input loop.

    Handle keyboard input in a separate thread.

    """
    while game.active:
        #FIXME
        keys = pygame.key.get_pressed()
        # If up, left, down, or right isn't pressed
        if no_keys_pressed(keys):
            continue
        #if key is None:
            #continue
        elif key[pygame.K_LEFT]:
            print('yeet')
        #elif key == 'quit':
            #game.active = False
        else:
            #assert key in ('left', 'down', 'right', 'up', 'space', 'swap')
            #FIXME I added left as a test
            keys = None 
            game.move(keys)
    print('Enter your name for leaderboard (blank to ignore):')
    name = input()
    if name:
        con = sqlite3.connect('tetris.sqlite3', isolation_level=None)
        con.execute('CREATE TABLE IF NOT EXISTS Leaderboard (name, score)')
        con.execute('INSERT INTO Leaderboard VALUES (?, ?)', (name, game.score))
        scores = con.execute('SELECT * FROM Leaderboard ORDER BY score DESC LIMIT 10')
        print('{0:<16} | {1:<16}'.format('Name', 'Score'))
        for pair in scores:
            print('{0:<16} | {1:<16}'.format(*pair))

def no_keys_pressed(keys):
    """Checks if not valid keys were pressed

    """

    if keys[pygame.K_LEFT] == True:
        return False
    elif keys[pygame.K_RIGHT] == True:
        return False
    elif keys[pygame.K_DOWN] == True:
        return False
    elif keys[pygame.K_UP] == True:
        return False
    else:
        return True

def main():
    "Main entry-point for Tetris."
    game = Game(10, 10)
    draw_thread = threading.Thread(target=draw_loop, args=(game,))
    input_thread = threading.Thread(target=input_loop, args=(game,))
    draw_thread.start()
    input_thread.start()
    draw_thread.join()
    input_thread.join()


if __name__ == '__main__':
    main()
