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
        self.windowWidth = width * 30
        self.height = height
        self.windowHeight = height * 37
        self.window = pygame.display.set_mode((self.windowWidth, self.windowHeight), 0, 32)
        self.font = pygame.font.Font('freesansbold.ttf', 24)
        self.board = collections.defaultdict(lambda: '#')
        for x in range(width):
            for y in range(height):
                self.board[x, y] = ' '
        self.active = True
        self.speed = 20
        self.next_letter = self.random.choice('IJLOSTZ')
        self.piece = self.next_piece()
        self.pieceColor = self.next_color()
        self.score = 0
        self.stash = None
        self.white = (255, 255, 255)
        self.blue = (0, 0, 255)
        self.red = (255, 0, 0)
        self.black = (0, 0, 0)
        self.bgColor = self.black

    def draw(self):
        "Draws the Window"
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

    def draw_window(self):
        "Draws Pygame Window"
        # Check if player moved piece 
        input_loop(self)

        #canvas declaration
        self.window.fill(self.bgColor)

        # Score
        text1 = self.font.render('Score: ' + str(self.score), True, self.blue, self.bgColor)
        textRect1 = text1.get_rect()     
        textRect1.center = (55, 15)

        # Level
        text2 = self.font.render('Level: ' + str(self.score // 4 + 1), True, self.blue, self.bgColor)
        textRect2 = text2.get_rect()     
        textRect2.center = (53, 43)

        # Next Piece
        text3 = self.font.render('Next piece: ' + self.next_letter, True, self.blue, self.bgColor)
        textRect3 = text3.get_rect()     
        textRect3.center = (84, 73)

        # Stash Piece
        text4 = self.font.render('Stash piece: ' + 'no' if self.stash is None else 'yes', True, self.blue, self.bgColor)
        textRect4 = text4.get_rect()     
        textRect4.center = (97, 103)

        # Starting Line
        pygame.draw.line(self.window, self.blue, (0, 125), (self.width*50, 125), 5)
        # Ending Line
        pygame.draw.line(self.window, self.blue, (0, self.height*37), (self.width*50, self.height*37), 25)

        # Draw the board, incorporating each piece
        for x in range(self.width):
            for y in range(self.height):
                if ((x, y) in self.piece):
                    # Draw squares and outlines
                    pygame.draw.rect(self.window, self.pieceColor, ((30*x), 127+(30*y), 30, 30))
                    pygame.draw.rect(self.window, self.black, ((30*x), 127+(30*y), 30, 30), 1)
                elif (self.board[x, y] == '#'):
                    pygame.draw.rect(self.window, self.pieceColor, ((30*x), 127+(30*y), 30, 30))
                    pygame.draw.rect(self.window, self.black, ((30*x), 127+(30*y), 30, 30), 1)

        # Drawing/Updating of Window
        self.window.blit(text1, textRect1)
        self.window.blit(text2, textRect2)
        self.window.blit(text3, textRect3)
        self.window.blit(text4, textRect4)
        
        pygame.display.update()

    def draw_text_box(self):
        "Draws text box for user to enter name"
        input_box = InputBox(100, 130, 140, 32)

        collectingInput = True
         
        # Infinite Loop...need to fix after successfully save leader score
        while collectingInput:
            for event in pygame.event.get():
                input_box.handle_event(event)
                input_box.update()
                input_box.draw(self.window)
                pygame.display.update()
                

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

    def next_color(self):
        "Select a random color for next game piece"
        letter = self.next_letter
        self.next_letter = self.random.choice('IJLOSTZ')
        if letter == 'I':
            color = (255, 0, 0)
        elif letter == 'J':
            color = (0, 255, 0)
        elif letter == 'L':
            color = (0, 0, 255)
        elif letter == 'O':
            color = (255, 255, 0)
        elif letter == 'S':
            color = (255, 0, 255)
        elif letter == 'T':
            color = (0, 255, 255)

        return color


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
                self.pieceColor = self.next_color()
            self.draw()
            self.draw_window()

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
            self.draw_window()


class InputBox:

    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.COLOR_INACTIVE = pygame.Color('lightskyblue3')
        self.COLOR_ACTIVE = pygame.Color('dodgerblue2')
        self.FONT = pygame.font.Font(None, 32)
        self.color = self.COLOR_INACTIVE
        self.text = text
        self.txt_surface = self.FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = self.COLOR_ACTIVE if self.active else self.COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    print(self.text)
                    return self.text
                    self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = self.FONT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)


def draw_loop(game):
    """Draw loop.

    """
    #game.draw() # Uncomment to have CLI

    game.draw_window() 
    counter = itertools.count(start=1)
    while game.active:
        mark = next(counter)
        game.tick(mark)
        time.sleep(0.01)

def input_loop(game):
    """Input loop.

    """
    # Collect user input
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN:
            if no_key_pressed(events):
                continue
            elif event.key == pygame.K_LEFT:
                game.move('left')
            elif event.key == pygame.K_RIGHT:
                game.move('right')
            elif event.key == pygame.K_DOWN:
                game.move('down')
            elif event.key == pygame.K_UP:
                game.move('up')
            elif event.key == pygame.K_SPACE:
                game.move('space')
            elif event.key == pygame.K_q:
                game.active = False

    if game.active == False:
        print('Enter your name for leaderboard (blank to ignore):')
        game.draw_text_box()
        name = input()
        if name:
            print('got \'em')
            con = sqlite3.connect('tetris.sqlite3', isolation_level=None)
            con.execute('CREATE TABLE IF NOT EXISTS Leaderboard (name, score)')
            con.execute('INSERT INTO Leaderboard VALUES (?, ?)', (name, game.score))
            scores = con.execute('SELECT * FROM Leaderboard ORDER BY score DESC LIMIT 10')
            print('{0:<16} | {1:<16}'.format('Name', 'Score'))
            for pair in scores:
                print('{0:<16} | {1:<16}'.format(*pair))


def no_key_pressed(events):
    """Quickly determine if a move key was pressed

    """
    for event in events:
      if event.key == pygame.K_LEFT:
        return False     
      elif event.key == pygame.K_RIGHT:
        return False
      elif event.key == pygame.K_DOWN:
        return False
      elif event.key == pygame.K_UP:
        return False
      elif event.key == pygame.K_SPACE:
        return False
      elif event.key == pygame.K_q:
        return False
      else:
        return True
    

def main():
    "Main entry-point for Tetris."
    pygame.init()

    # Define board size
    game = Game(10, 20)

    draw_loop(game)

if __name__ == '__main__':
    main()
