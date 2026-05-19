import threading
import random
from .check import checker


class GomokuAI:
    def __init__(self, board_size=15):
        self.board_size = board_size
        self.directions_all = [(0, 1), (1, 0), (1, 1), (1, -1)]
        self.directions_hv = [(0, 1), (1, 0)]
        self._lock = threading.Lock()

    def get_move(self, board, ai_player, difficulty, round_count):
        with self._lock:
            if difficulty == 1:
                return self._level1(board, ai_player)
            elif difficulty == 2:
                is_mistake = (round_count > 0 and round_count % 3 == 0)
                return self._level2(board, ai_player, is_mistake)
            else:
                return self._level3(board, ai_player)

    def _level1(self, board, ai_player):
        human_player = 3 - ai_player
        best_score = -1
        best_moves = []

        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] == 0:
                    score = self._evaluate_position(board, i, j, ai_player, human_player, use_diagonal=False)
                    if score > best_score:
                        best_score = score
                        best_moves = [(i, j)]
                    elif score == best_score:
                        best_moves.append((i, j))

        if best_moves:
            return random.choice(best_moves)
        return self._get_random_move(board)

    def _level2(self, board, ai_player, is_mistake):
        human_player = 3 - ai_player
        best_score = -1
        best_moves = []

        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] == 0:
                    if is_mistake:
                        score = self._evaluate_attack_only(board, i, j, ai_player)
                    else:
                        score = self._evaluate_position(board, i, j, ai_player, human_player, use_diagonal=True)
                    if score > best_score:
                        best_score = score
                        best_moves = [(i, j)]
                    elif score == best_score:
                        best_moves.append((i, j))

        if best_moves:
            return random.choice(best_moves)
        return self._get_random_move(board)

    def _level3(self, board, ai_player):
        human_player = 3 - ai_player

        win_move = self._find_winning_move(board, ai_player)
        if win_move:
            return win_move

        block_move = self._find_winning_move(board, human_player)
        if block_move:
            return block_move

        open_four_move = self._find_open_four(board, ai_player)
        if open_four_move:
            return open_four_move

        block_open_four = self._find_open_four(board, human_player)
        if block_open_four:
            return block_open_four

        best_score = -1
        best_moves = []

        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] == 0 and self._has_neighbor(board, i, j):
                    score = self._evaluate_position_strong(board, i, j, ai_player, human_player)
                    if score > best_score:
                        best_score = score
                        best_moves = [(i, j)]
                    elif score == best_score:
                        best_moves.append((i, j))

        if best_moves:
            return random.choice(best_moves)

        center = self.board_size // 2
        if board[center][center] == 0:
            return (center, center)

        return self._get_random_move(board)

    def _evaluate_position(self, board, row, col, ai_player, human_player, use_diagonal=True):
        directions = self.directions_all if use_diagonal else self.directions_hv
        score = 0

        board[row][col] = ai_player
        for dx, dy in directions:
            score += self._score_direction(board, row, col, dx, dy, ai_player)
        board[row][col] = 0

        board[row][col] = human_player
        for dx, dy in directions:
            score += self._score_direction(board, row, col, dx, dy, human_player) * 0.9
        board[row][col] = 0

        return score

    def _evaluate_attack_only(self, board, row, col, ai_player):
        score = 0
        board[row][col] = ai_player
        for dx, dy in self.directions_all:
            score += self._score_direction(board, row, col, dx, dy, ai_player)
        board[row][col] = 0
        return score

    def _evaluate_position_strong(self, board, row, col, ai_player, human_player):
        score = 0

        board[row][col] = ai_player
        for dx, dy in self.directions_all:
            score += self._score_direction_strong(board, row, col, dx, dy, ai_player)
        board[row][col] = 0

        board[row][col] = human_player
        for dx, dy in self.directions_all:
            score += self._score_direction_strong(board, row, col, dx, dy, human_player) * 0.95
        board[row][col] = 0

        center = self.board_size // 2
        distance_to_center = abs(row - center) + abs(col - center)
        score += (self.board_size - distance_to_center) * 2

        return score

    def _score_direction(self, board, row, col, dx, dy, player):
        count = 1
        open_ends = 0

        i = 1
        while True:
            r, c = row + dx * i, col + dy * i
            if 0 <= r < self.board_size and 0 <= c < self.board_size:
                if board[r][c] == player:
                    count += 1
                elif board[r][c] == 0:
                    open_ends += 1
                    break
                else:
                    break
            else:
                break
            i += 1

        i = 1
        while True:
            r, c = row - dx * i, col - dy * i
            if 0 <= r < self.board_size and 0 <= c < self.board_size:
                if board[r][c] == player:
                    count += 1
                elif board[r][c] == 0:
                    open_ends += 1
                    break
                else:
                    break
            else:
                break
            i += 1

        if count >= 5:
            return 100000
        elif count == 4:
            if open_ends == 2:
                return 10000
            elif open_ends == 1:
                return 1000
            else:
                return 100
        elif count == 3:
            if open_ends == 2:
                return 500
            elif open_ends == 1:
                return 100
            else:
                return 10
        elif count == 2:
            if open_ends == 2:
                return 50
            elif open_ends == 1:
                return 10
            else:
                return 1
        return 0

    def _score_direction_strong(self, board, row, col, dx, dy, player):
        count = 1
        open_ends = 0
        blocked = 0

        i = 1
        while True:
            r, c = row + dx * i, col + dy * i
            if 0 <= r < self.board_size and 0 <= c < self.board_size:
                if board[r][c] == player:
                    count += 1
                elif board[r][c] == 0:
                    open_ends += 1
                    break
                else:
                    blocked += 1
                    break
            else:
                blocked += 1
                break
            i += 1

        i = 1
        while True:
            r, c = row - dx * i, col - dy * i
            if 0 <= r < self.board_size and 0 <= c < self.board_size:
                if board[r][c] == player:
                    count += 1
                elif board[r][c] == 0:
                    open_ends += 1
                    break
                else:
                    blocked += 1
                    break
            else:
                blocked += 1
                break
            i += 1

        if count >= 5:
            return 1000000
        elif count == 4:
            if open_ends == 2:
                return 100000
            elif open_ends == 1:
                return 10000
            else:
                return 500
        elif count == 3:
            if open_ends == 2:
                return 5000
            elif open_ends == 1:
                return 500
            else:
                return 50
        elif count == 2:
            if open_ends == 2:
                return 200
            elif open_ends == 1:
                return 50
            else:
                return 5
        elif count == 1:
            if open_ends == 2:
                return 10
            elif open_ends == 1:
                return 2
        return 0

    def _find_winning_move(self, board, player):
        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] == 0:
                    board[i][j] = player
                    if checker.check_win(board, i, j, player):
                        board[i][j] = 0
                        return (i, j)
                    board[i][j] = 0
        return None

    def _find_open_four(self, board, player):
        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] == 0:
                    if self._is_open_four(board, i, j, player):
                        return (i, j)
        return None

    def _is_open_four(self, board, row, col, player):
        board[row][col] = player
        for dx, dy in self.directions_all:
            count = 1
            open_ends = 0

            i = 1
            while True:
                r, c = row + dx * i, col + dy * i
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if board[r][c] == player:
                        count += 1
                    elif board[r][c] == 0:
                        open_ends += 1
                        break
                    else:
                        break
                else:
                    break
                i += 1

            i = 1
            while True:
                r, c = row - dx * i, col - dy * i
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if board[r][c] == player:
                        count += 1
                    elif board[r][c] == 0:
                        open_ends += 1
                        break
                    else:
                        break
                else:
                    break
                i += 1

            if count >= 4 and open_ends >= 1:
                board[row][col] = 0
                return True

        board[row][col] = 0
        return False

    def _has_neighbor(self, board, row, col, distance=2):
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                if dx == 0 and dy == 0:
                    continue
                r, c = row + dx, col + dy
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if board[r][c] != 0:
                        return True
        return False

    def _get_random_move(self, board):
        empty_cells = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] == 0:
                    empty_cells.append((i, j))
        if empty_cells:
            return random.choice(empty_cells)
        return None

    def get_move_async(self, board, ai_player, difficulty, round_count, callback):
        def ai_thread():
            move = self.get_move(board, ai_player, difficulty, round_count)
            if callback:
                callback(move)

        thread = threading.Thread(target=ai_thread, daemon=True)
        thread.start()
        return thread


ai = GomokuAI()
