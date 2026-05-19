import threading


class GameChecker:
    def __init__(self, board_size=15):
        self.board_size = board_size
        self.directions = [
            (0, 1),
            (1, 0),
            (1, 1),
            (1, -1)
        ]
        self._lock = threading.Lock()
        self.check_result = None
        self.is_checking = False

    def check_win(self, board, row, col, player):
        for dx, dy in self.directions:
            count = 1
            for i in range(1, 5):
                r, c = row + dx * i, col + dy * i
                if 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == player:
                    count += 1
                else:
                    break
            for i in range(1, 5):
                r, c = row - dx * i, col - dy * i
                if 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == player:
                    count += 1
                else:
                    break
            if count >= 5:
                return True
        return False

    def check_draw(self, board):
        empty_count = 0
        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] == 0:
                    empty_count += 1
        if empty_count == 0:
            return True
        if not self._has_possible_win(board):
            return True
        return False

    def _has_possible_win(self, board):
        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i][j] != 0:
                    player = board[i][j]
                    if self._can_win_from(board, i, j, player):
                        return True
        return False

    def _can_win_from(self, board, row, col, player):
        for dx, dy in self.directions:
            count = 1
            empty_spaces = 0
            for i in range(1, 5):
                r, c = row + dx * i, col + dy * i
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if board[r][c] == player:
                        count += 1
                    elif board[r][c] == 0:
                        empty_spaces += 1
                    else:
                        break
                else:
                    break
            for i in range(1, 5):
                r, c = row - dx * i, col - dy * i
                if 0 <= r < self.board_size and 0 <= c < self.board_size:
                    if board[r][c] == player:
                        count += 1
                    elif board[r][c] == 0:
                        empty_spaces += 1
                    else:
                        break
                else:
                    break
            if count + empty_spaces >= 5:
                return True
        return False

    def check_game_state_async(self, board, row, col, player, callback):
        def check_thread():
            with self._lock:
                self.is_checking = True
                try:
                    if self.check_win(board, row, col, player):
                        result = ('win', player)
                    elif self.check_draw(board):
                        result = ('draw', None)
                    else:
                        result = ('continue', None)
                    self.check_result = result
                    if callback:
                        callback(result)
                finally:
                    self.is_checking = False

        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
        return thread

    def get_last_result(self):
        with self._lock:
            return self.check_result


checker = GameChecker()
