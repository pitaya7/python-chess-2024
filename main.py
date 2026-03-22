global board_display
global black_score
global white_score

# This program is based on the classic board game "chess"


class Square:
    def __init__(self, xpos, ypos):

        self.x = xpos
        self.y = ypos
        self.pos = [self.x, self.y]
        self.color = self.which_color()
        self.coords = self.find_coordinates()
        self.piece = None  # piece not added yet
        self.IsOccupied = False
        self.en_passant = None


    def find_coordinates(self):
        columns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        return (columns[self.x] + str(self.y + 1))
    
    def set_occ(self, val):
        self.IsOccupied = val
        if self.piece == None:
            self.IsOccupied = False

    def which_color(self):  # Color alternates every square
        if (self.y + self.x) % 2 == 0: 
            color = 1  # Black
        else:
            color = 0  # White
        return color

#  create board
    
board = []
squares = []
for col in range(8):
    rank = []
    for row in range(8):
        square = Square(row, col)
        rank.append(square)
        squares.append(square)
    board.append(rank)

class InvalidMove(Exception):
    pass

# Initialize Pieces

class Piece:
    def __init__(self, name, team, pos):
        self.t = team
        self.pos = pos
        self.x = pos[0]
        self.y = pos[1]
        self.name = name
        self.moves = []
        self.dests = []
        self.coords = ''
        self.init_ms = []  # for verifying if a move does not put self into check
    
    def set_pos(self, pos):
        self.pos = pos
        self.x = pos[0]
        self.y = pos[1]
        
    def set_dests(self):
        d = []
        org_sq = board[self.y][self.x]
        for m in self.moves:
            self.moves = list(filter(lambda m: self.x + m[0] >= 0 and self.x + m[0] <= 7 and self.y + m[1] >= 0, self.moves))
            d_x = self.x + m[0]
            d_y = self.y + m[1]
            try:
                if (m[0] > self.x and m[0] < 0) or (m[1] > self.y and m[1] < 0):
                    self.moves.remove(m)
                if d_x > 7 or d_y > 7:
                    self.moves.remove(m)
            except ValueError:
                continue
            try:
                dest_sq = board[d_y][d_x]  
            except IndexError:
                try:
                    self.moves.remove(m)
                except ValueError:
                    continue
                continue
            if self.check_dest(dest_sq):
                d.append(dest_sq)
            
        self.dests = d
        self.show_dests = []
        for dest in d:
            self.show_dests.append(dest.coords)

    def check_dest(self, dest):
        if dest.IsOccupied and dest.piece.t == self.t:
            return False
        else:
            return True

    def move(self, move):  # move = (change in x, change in y)
        check_check()
        org_sq = board[self.y][self.x]
        new_x = self.x + move[0]
        new_y = self.y + move[1]
        dest = board[new_y][new_x]  
        if isinstance(self, Pawn):
            if move == (0, 2):
                board[self.y + 1][self.x].en_passant = self
            elif move == (0, -2):
                board[self.y - 1][self.x].en_passant = self
            if (self.t == 'white' and new_y == 7) or (self.t == 'black' and new_y == 0):
                promotion(self, self.x, self.y)
        if dest.IsOccupied and dest.piece.t != self.t:
            take_piece(dest.piece)
        elif dest.en_passant in pieces and dest.en_passant.t != self.t:
            board[dest.en_passant.y][dest.en_passant.x].piece = None
            board[dest.en_passant.y][dest.en_passant.x].IsOccupied = False
            take_piece(dest.en_passant)
            dest.en_passant = False
        self.set_pos((new_x, new_y))
        dest.piece = self
        dest.set_occ(True)
        org_sq.piece = None
        org_sq.set_occ(False)
        for s in squares:
            if s.piece in pieces or (s.en_passant in pieces and s.en_passant.t != turn):
                s.en_passant = None
        check_check()
        if turn == 'white' and white_is_checked:
            raise InvalidMove
        refresh()


class Pawn(Piece):
    type_name = 'P'
    def __init__(self, name, team, pos):
        super().__init__(name, team, pos)

    def pawn_moves(self):
        moves = []
        if self.t == 'black':
            i = -1
            self.init_y = 6
        else:
            i = 1
            self.init_y = 1
        
        if not board[self.y + i][self.x].IsOccupied:  # can move directly forward only if unoccupied
            moves.append((0, i))
            if self.y == self.init_y:
                if not board[self.y + i * 2][self.x].IsOccupied:  # can move 2 on first turn
                    moves.append((0, i * 2))
        if self.x < 7:
            if board[self.y + i][self.x + 1].IsOccupied:
                moves.append((1, i))
            if board[self.y + i][self.x + 1].en_passant != None and board[self.y + i][self.x + 1].en_passant.t != self.t:
                moves.append((1, i))    
        if self.x > 0:
            if board[self.y + i][self.x - 1].IsOccupied: 
                moves.append((-1, i))
            if board[self.y + i][self.x - 1].en_passant != None and board[self.y + i][self.x - 1].en_passant.t != self.t:
                moves.append((-1, i))
        self.init_ms = [(-1, i), (1, i)]
        self.moves = moves
  
class Rook(Piece):
    type_name = 'R'
    def __init__(self, name, team, pos):
        super().__init__(name, team, pos)
        
    def rook_moves(self):
        moves = []
        self.init_ms = []
        blocked = 0
        for f in range(1, self.x + 1):
            self.init_ms.append((-f, 0))
            if board[self.y][self.x - f].IsOccupied:
                blocked += 1 
                if board[self.y][self.x - f].piece.t == self.t:
                    break
            if blocked <= 1:  
                moves.append((-f, 0))
        blocked = 0
        for f in range(1, 8 - self.x):
            if board[self.y][self.x + f].IsOccupied:
                blocked += 1
                if board[self.y][self.x + f].piece.t == self.t:
                    break
            if blocked <= 1:
                moves.append((f, 0))
            self.init_ms.append((f, 0))
        blocked = 0
        for r in range(1, self.y + 1):
            self.init_ms.append((-f, 0))
            if board[self.y - r][self.x].IsOccupied:
                blocked += 1    
                if board[self.y - r][self.x].piece.t == self.t:
                    break
            if blocked <= 1:
                moves.append((0, -r))
        blocked = 0
        for r in range(1, 8 - self.y):
            if board[self.y + r][self.x].IsOccupied:
                blocked += 1
                if board[self.y + r][self.x].piece.t == self.t:
                    break
            if blocked <= 1:
                moves.append((0, r))
            self.init_ms.append((0, r))
        self.moves = list(filter(lambda m: m != (0, 0), moves))

class Bishop(Piece):
    type_name = 'B'

    def __init__(self, name, team, pos):
        super().__init__(name, team, pos)
        
    def bishop_moves(self):
        moves = []
        self.init_ms = []
        for i in [-1, 1]:
            blocked = 0
            for b_x in range(1, self.x + 1):
                b_y = b_x * i
                if self.y + b_y > 7 or self.y + b_y < 0:
                    break
                if board[self.y + b_y][self.x - b_x].IsOccupied: # if a square is occupied, the bishop cannot move beyond it
                    blocked += 1 
                    if board[self.y + b_y][self.x - b_x].piece.t == self.t: 
                        break
                if blocked <= 1:  # if the target piece is of the other team, adds that square to moves before stopping
                    moves.append((-b_x, b_y))
                self.init_ms.append((-b_x, b_y))
            blocked = 0
            for b_x in range(1, 8 - self.x):
                b_y = b_x * i
                if self.y + b_y > 7 or self.y + b_y < 0:
                    break
                if board[self.y + b_y][self.x + b_x].IsOccupied:
                    blocked += 1
                    if board[self.y + b_y][self.x + b_x].piece.t == self.t:
                        break
                if blocked <= 1:
                    moves.append((b_x, b_y))
                self.init_ms.append((b_x, b_y))
        for m in moves:  # adds each move only once
            if not  m in self.moves:
                self.moves.append(m)
        self.moves = list(filter(lambda m: m != (0, 0), self.moves))  # removes (0, 0) from moveset
        self.init_ms = filter(lambda m: m != (0, 0), self.init_ms)

class Knight(Piece):
    type_name = 'N'
    def __init__(self, name, team, pos):
        super().__init__(name, team, pos)

    def knight_moves(self):
        moves = []
        for i in [1, -1]:
            for j in [2, -2]:
                moves.append((i, j))
                moves.append((j, i))

        self.moves = moves

class Queen(Piece):
    type_name = 'Q'
    def __init__(self, name, team, pos):
        super().__init__(name, team, pos)
    
    def queen_moves(self):
        moves = []
        Rook.rook_moves(self)
        for m in self.moves:
            moves.append(m)
        Bishop.bishop_moves(self)
        for m in self.moves:
            if not  m in moves:
                moves.append(m)
        self.moves = moves
  
class King(Piece):
    type_name = 'K'
    def __init__(self, name, team, pos):
        super().__init__(name, team, pos)

    def king_moves(self):  # must check other team's moves
        moves = []
        for i in [1, -1]:
            for j in [1, -1]:
                moves.append((i, j))
        self.moves = moves

def check_check():  # check for check
    team_white = filter(lambda p: p.t == 'white', pieces)
    team_black = filter(lambda p: p.t == 'black', pieces)
    for p in team_black:
        if pieces[15].pos in p.dests:
            white_is_checked == True
            if turn == 'white':
                raise InvalidMove
        else:
            white_is_checked == False
    for p in team_white:
        try:
            if pieces[31].pos in p.dests:
                black_is_checked == True
                if turn == 'black':
                    raise InvalidMove
            else:
                black_is_checked == False
        except IndexError:
            pass

def take_piece(piece):
    global black_score
    global white_score
    if isinstance(piece, Pawn):  # 1
        add_point = 1
    elif isinstance(piece, (Bishop, Knight)):  # both 3
        add_point = 3
    elif isinstance(piece, Rook): # rook 5
        add_point = 5
    elif isinstance(piece, Queen): # 9
        add_point = 9

    if piece.t == 'white': 
        white_taken.append(piece.name)
        black_score += add_point
    else:
        black_taken.append(piece.name)
        white_score += add_point
    active_pieces.remove(piece)

piece_types = [Pawn, Rook, Knight, Bishop, Queen, King]
def set_moves(p):
    if isinstance(p, Pawn):
        p.pawn_moves()
    elif isinstance(p, Rook):
        p.rook_moves()
    elif isinstance(p, Knight):
        p.knight_moves()
    elif isinstance(p, Bishop):
        p.bishop_moves()
    elif isinstance(p, Queen):
        p.queen_moves()
    elif isinstance(p, King):
        p.king_moves()
    p.set_dests()

def refresh():
    for p in pieces:
        p.coords = board[p.y][p.x].coords
        board[p.y][p.x].set_occ(True)
        board[p.y][p.x].piece = p
        set_moves(p)
        p.set_dests()
    check_check()
    for s in squares:
        if s.piece == None:
            s.set_occ(False)   

def promotion(pawn, xpos, ypos):
    print(f'{pawn.name} at ({xpos}, {ypos} can be promoted')
    while True:
        promote_to = input("R, B, N, Q ").upper()
        if promote_to in ['R', 'B', 'N', 'Q']:
            break
    if pawn.t == 'white':
        col = 'w'
    else: 
        col = 'b'
    if promote_to == 'R':
        typ = Rook
    elif promote_to == 'B':
        typ = Bishop
    elif promote_to == 'N':
        typ = Knight
    else:
        typ = Queen
    typ_count = 1
    for p in filter(lambda t: isinstance(t, typ), pieces):
        typ_count += 1

    new_piece = typ((col + typ.name + str(typ_count)), pawn.t, pawn.pos)
    active_pieces.append(new_piece)
    active_pieces.remove(pawn)
    set_moves(new_piece)

def display_board():
    global board_display
    if turn == 'white':
        print("""         [ WHITE ]: {}   black: {}
    """.format(white_score, black_score))
    else:
        print("""         white: {}   [ BLACK ]: {}
    """.format(white_score, black_score))
    if board_display:
        print('     A    B    C    D    E    F    G    H  ')
        print('  ===========================================')
        rows = []
        for r in range(len(board)):
            rank = []
            rs = []
            for s in board[r]:
                try: rank.append(s.piece.name)
                except AttributeError: rank.append('  ')
                finally: rs.append('----')
            
            rows.append(f' {r + 1}|| ' + ' | '.join(rank) + ' ||')
            if r < len(board) - 1:
                rows.append('  ||' + '-'.join(rs) + '||')
        if turn == 'black':
            for row in rows: print(row)
        else: 
            for row in range(len(rows)):
                print(rows[-(row + 1)])
        print('  ===========================================\n')

def toggle_board_display():
    global board_display
    if board_display == True:
        board_display = False
    else:
        board_display = True

def show_help():
    print("""
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    - On your turn, type the coordinates of a square with your piece on it to show the squares it can move to.
        Example: 'b4'
           
    - To move, type the coordinates of a piece followed by sand the square you with to move that piece to, seperated by a space.
        Example: 'a2 a3'
    
    - If the move or selected piece is invalid, you will be prompted again.
    
    - By default, the board will be displayed after every turn. Toggle with 'b' or 'board'.
    
    - There is currently no way to win because the game is not finished
    
    'q' or 'quit' will exit the game.
    'h' or 'help' will display this text again
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """)
    

new_game = True
running = True


while running:  # main loop

    if new_game:
        pieces = []
        piece_init_y = 0
        team = 'white'
        for col in ['w', 'b']:  # init all pieces
            piece_init_x = 0
            for f in range(8):
                if team == 'white': r = 1
                else: r = 6
                pieces.append(Pawn((col + 'P'), team, (f, r)))
            for typ in piece_types[1:4]:  # init R, N, and B in init positions
                piece1 = typ((col + typ.type_name), team, (piece_init_x, piece_init_y))
                piece2 = typ((col + typ.type_name), team, (7 - piece_init_x, piece_init_y))
                piece_init_x += 1
                pieces.append(piece1)
                pieces.append(piece2)
            pieces.append(Queen(col + 'Q', team, (3, piece_init_y)))  # both Q's at x = 3, 
            pieces.append(King(col + 'K', team, (4, piece_init_y)))  # K's at x = 4
            piece_init_y = 7  # white pieces all at y = 0, black at y = 7
            team = 'black'
        turn = 'white'
        white_is_checked = False
        black_is_checked = False
        white_taken = []
        black_taken = []
        white_score = 0
        black_score = 0
        s_coords = []
        for s in squares:
            s_coords.append(s.coords)
        active_pieces = pieces
        turn_count = 1
        refresh()
        print('  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        board_display = True
        display_board()
        print("Welcome. type 'h' for help, 'q' to quit.\n")
        
        new_game = False
    else:
        display_board()


    p_names = []
    for p in active_pieces:
        set_moves(p)
        if p.t == turn:
            p_names.append(p.name)

    refresh() 

    while True:
        inp = input("> ").lower()
        if inp == 'q' or inp == 'quit':
            quits = input("Quit? This game cannot be restored. (Y/N) \n> ")
            if quits.lower() == 'y':
                running = False
            else:
                continue
            running = False
            break
            
        elif inp == 'h' or inp == 'help':
            show_help()
        elif inp == 'b' or inp == 'board':
            toggle_board_display()
        elif ' ' not in inp and inp in s_coords:
            s = squares[s_coords.index(inp)]
            p = s.piece
            if not p in pieces or p.t != turn:
                print("Invalid piece selection.")
                continue
            print("Selected: " + p.name + " at " + s.coords + ".")
            if p.show_dests == []:
                print('Piece cannot move.')
            else:
                print('Can move to: '+ ', '.join(p.show_dests))
            continue

        else:
            try:
                pick_piece, pick_dest = inp.split(" ")
            except:
                continue
            if pick_piece not in s_coords:
                print("Invalid piece selection.")
                continue
            s = squares[s_coords.index(pick_piece)]
            p = s.piece
            if not p in pieces or p.t != turn:
                print("Invalid piece selection.")
                continue
            if pick_dest == 'show' or pick_dest == 's':
                print("Selected: " + p.name + " at " + s.coords + ".")
                if p.show_dests == []:
                    print('Piece cannot move.')
                else:
                    print('Can move to: '+ ', '.join(p.show_dests))
                continue

            elif (not pick_dest in s_coords) or (not pick_dest in s.piece.show_dests):
                continue
            else:
                try:
                    d = p.dests[s.piece.show_dests.index(pick_dest)]
                    p.move((d.pos[0] - p.x, d.pos[1] - p.y))
                except InvalidMove:
                    continue
                else:
                    break

    # end turn
    for s in squares:
        if s.en_passant != None and s.en_passant.t != turn:
            s.en_passant = None
    if turn == 'black':
        turn = 'white'
    elif turn == 'white':
        turn = 'black'
    turn_count += 1
   


