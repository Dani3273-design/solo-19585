import pygame
import sys
import os
import threading
from .setting import settings
from .count import counter
from .check import checker
from .ai import ai


class Button:
    def __init__(self, x, y, width, height, text, callback, color=(70, 130, 180), hover_color=(100, 149, 237), text_color=(255, 255, 255), font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font_size = font_size
        self.hovered = False

    def draw(self, screen, font):
        current_color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=10)
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False


class GomokuUI:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.width = 1000
        self.height = 750
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("人机对战五子棋")

        self.board_size = 15
        self.cell_size = 40
        self.board_padding = 40
        self.board_width = self.cell_size * (self.board_size - 1)
        self.board_x = (self.width - self.board_width) // 2 + 80
        self.board_y = (self.height - self.board_width) // 2

        self.colors = {
            'bg': (245, 245, 220),
            'board': (222, 184, 135),
            'line': (139, 90, 43),
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'text': (51, 51, 51),
            'accent': (70, 130, 180)
        }

        self.fonts = self._load_fonts()
        self.sound = self._load_sound()

        self.current_page = 'home'
        self.board = [[0] * self.board_size for _ in range(self.board_size)]
        self.current_player = 1
        self.player_color = 1
        self.ai_color = 2
        self.game_over = False
        self.game_result = None
        self.winner = None
        self.waiting_for_ai = False
        self.check_result_pending = None

        self.buttons = {
            'home': [],
            'settings': [],
            'choose': [],
            'game': [],
            'end': []
        }

        self._init_buttons()
        counter.on_timeout = self._on_timeout

        self.ui_lock = threading.Lock()

    def _load_fonts(self):
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf'
        ]

        selected_font = None
        for path in font_paths:
            if os.path.exists(path):
                selected_font = path
                break

        fonts = {}
        if selected_font:
            fonts['title'] = pygame.font.Font(selected_font, 48)
            fonts['subtitle'] = pygame.font.Font(selected_font, 32)
            fonts['normal'] = pygame.font.Font(selected_font, 24)
            fonts['small'] = pygame.font.Font(selected_font, 18)
        else:
            fonts['title'] = pygame.font.SysFont(None, 48)
            fonts['subtitle'] = pygame.font.SysFont(None, 32)
            fonts['normal'] = pygame.font.SysFont(None, 24)
            fonts['small'] = pygame.font.SysFont(None, 18)

        return fonts

    def _load_sound(self):
        try:
            sound_path = os.path.join(os.path.dirname(__file__), 'drop.wav')
            if os.path.exists(sound_path):
                return pygame.mixer.Sound(sound_path)
        except Exception:
            pass
        try:
            import array
            import math
            frequency = 800
            duration = 0.1
            sample_rate = 44100
            n_samples = int(duration * sample_rate)
            buf = array.array('h')
            for i in range(n_samples):
                t = i / sample_rate
                envelope = max(0, 1 - t / duration)
                value = int(32767 * envelope * math.sin(2 * math.pi * frequency * t))
                buf.append(value)
            sound = pygame.mixer.Sound(buffer=buf)
            sound.set_volume(0.3)
            return sound
        except Exception:
            pass
        return None

    def _play_sound(self):
        if self.sound and settings.get_sound():
            try:
                self.sound.play()
            except Exception:
                pass

    def _init_buttons(self):
        btn_width = 200
        btn_height = 50
        center_x = (self.width - btn_width) // 2

        self.buttons['home'] = [
            Button(center_x, 380, btn_width, btn_height, "开始游戏", self._goto_choose, font_size=28),
            Button(center_x, 460, btn_width, btn_height, "设置", self._goto_settings, font_size=28)
        ]

        self.buttons['settings'] = [
            Button(self.width // 2 - 60, 520, 120, 40, "返回", self._goto_home, font_size=22)
        ]

        self.buttons['choose'] = [
            Button(self.width // 2 - 200, 380, 150, 50, "黑棋", lambda: self._start_game(1), font_size=26),
            Button(self.width // 2 + 50, 380, 150, 50, "白棋", lambda: self._start_game(2), font_size=26),
            Button(self.width // 2 - 60, 480, 120, 40, "返回", self._goto_home, font_size=22)
        ]

        self.buttons['game'] = [
            Button(self.width - 140, 20, 120, 35, "返回主页", self._goto_home, font_size=18)
        ]

        self.buttons['end'] = [
            Button(self.width // 2 - 200, 500, 150, 50, "再来一局", self._restart_game, font_size=24),
            Button(self.width // 2 + 50, 500, 150, 50, "设置", self._goto_settings, font_size=24)
        ]

    def _goto_home(self):
        self.current_page = 'home'
        self._reset_game()

    def _goto_settings(self):
        self.current_page = 'settings'

    def _goto_choose(self):
        self.current_page = 'choose'

    def _start_game(self, player_color):
        self.player_color = player_color
        self.ai_color = 3 - player_color
        self.current_page = 'game'
        self._reset_game()
        self._start_new_game()

    def _reset_game(self):
        self.board = [[0] * self.board_size for _ in range(self.board_size)]
        self.current_player = 1
        self.game_over = False
        self.game_result = None
        self.winner = None
        self.waiting_for_ai = False
        self.check_result_pending = None
        counter.reset()

    def _start_new_game(self):
        counter.start_game()
        if self.ai_color == 1:
            self._ai_move()
        else:
            counter.start_move()

    def _restart_game(self):
        self._reset_game()
        self.current_page = 'game'
        self._start_new_game()

    def _on_timeout(self):
        if not self.game_over and not self.waiting_for_ai:
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'action': 'do_timeout'}))

    def _do_timeout(self):
        if not self.game_over and not self.waiting_for_ai:
            self.game_over = True
            self.game_result = 'timeout'
            self.winner = self.ai_color
            counter.stop_game()

    def _handle_click(self, pos):
        if self.game_over or self.waiting_for_ai:
            return

        x, y = pos
        if not (self.board_x - self.cell_size // 2 <= x <= self.board_x + self.board_width + self.cell_size // 2 and
                self.board_y - self.cell_size // 2 <= y <= self.board_y + self.board_width + self.cell_size // 2):
            return

        col = round((x - self.board_x) / self.cell_size)
        row = round((y - self.board_y) / self.cell_size)

        if 0 <= row < self.board_size and 0 <= col < self.board_size and self.board[row][col] == 0:
            self._make_move(row, col, self.current_player)

    def _make_move(self, row, col, player):
        self.board[row][col] = player
        self._play_sound()
        counter.stop_move()

        def check_callback(result):
            status, winner = result
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, {
                'action': 'check_result',
                'status': status,
                'winner': winner,
                'player': player
            }))

        checker.check_game_state_async(
            [row[:] for row in self.board],
            row, col, player,
            check_callback
        )

    def _process_check_result(self, data):
        status = data['status']
        winner = data['winner']
        player = data['player']

        if status == 'win':
            self.game_over = True
            self.game_result = 'win'
            self.winner = winner
            counter.stop_game()
        elif status == 'draw':
            self.game_over = True
            self.game_result = 'draw'
            self.winner = None
            counter.stop_game()
        else:
            if player == self.player_color:
                self.current_player = self.ai_color
                self._ai_move()
            else:
                counter.increment_round()
                self.current_player = self.player_color
                counter.start_move()

    def _ai_move(self):
        if self.game_over:
            return

        self.waiting_for_ai = True

        def ai_callback(move):
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, {
                'action': 'ai_move',
                'move': move
            }))

        board_copy = [row[:] for row in self.board]
        ai.get_move_async(
            board_copy,
            self.ai_color,
            settings.get_difficulty(),
            counter.get_round_count(),
            ai_callback
        )

    def _process_ai_move(self, move):
        self.waiting_for_ai = False
        if move and not self.game_over:
            row, col = move
            self._make_move(row, col, self.ai_color)

    def _handle_settings_click(self, pos):
        center_x = self.width // 2

        difficulty_rects = [
            pygame.Rect(center_x - 120, 205, 80, 40),
            pygame.Rect(center_x - 20, 205, 80, 40),
            pygame.Rect(center_x + 80, 205, 80, 40)
        ]

        for i, rect in enumerate(difficulty_rects):
            if rect.collidepoint(pos):
                settings.set_difficulty(i + 1)
                return

        sound_rect = pygame.Rect(center_x - 40, 305, 80, 40)
        if sound_rect.collidepoint(pos):
            settings.set_sound(not settings.get_sound())

    def draw(self):
        self.screen.fill(self.colors['bg'])

        if self.current_page == 'home':
            self._draw_home()
        elif self.current_page == 'settings':
            self._draw_settings()
        elif self.current_page == 'choose':
            self._draw_choose()
        elif self.current_page == 'game':
            self._draw_game()
        elif self.current_page == 'end':
            self._draw_end()

        pygame.display.flip()

    def _draw_home(self):
        title = self.fonts['title'].render("人机对战五子棋", True, self.colors['text'])
        title_rect = title.get_rect(center=(self.width // 2, 120))
        self.screen.blit(title, title_rect)

        instructions = [
            "游戏规则：",
            "1. 黑棋先行，双方交替落子",
            "2. 先将五子连成一线者获胜",
            "3. 每步限时15秒，超时判负",
            "4. 支持三种AI难度等级"
        ]

        y = 190
        for instr in instructions:
            text = self.fonts['small'].render(instr, True, self.colors['text'])
            text_rect = text.get_rect(center=(self.width // 2, y))
            self.screen.blit(text, text_rect)
            y += 28

        for btn in self.buttons['home']:
            btn.draw(self.screen, self.fonts['normal'])

    def _draw_settings(self):
        title = self.fonts['subtitle'].render("游戏设置", True, self.colors['text'])
        title_rect = title.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title, title_rect)

        difficulty_label = self.fonts['normal'].render("AI难度：", True, self.colors['text'])
        self.screen.blit(difficulty_label, (self.width // 2 - 280, 215))

        center_x = self.width // 2
        difficulty_rects = [
            pygame.Rect(center_x - 120, 205, 80, 40),
            pygame.Rect(center_x - 20, 205, 80, 40),
            pygame.Rect(center_x + 80, 205, 80, 40)
        ]

        for i, rect in enumerate(difficulty_rects):
            color = (100, 149, 237) if settings.get_difficulty() == i + 1 else (200, 200, 200)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 100, 100), rect, 2, border_radius=8)
            text = self.fonts['normal'].render(f"等级{i + 1}", True, self.colors['text'])
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

        sound_label = self.fonts['normal'].render("落子声音：", True, self.colors['text'])
        self.screen.blit(sound_label, (self.width // 2 - 280, 315))

        sound_rect = pygame.Rect(center_x - 40, 305, 80, 40)
        color = (100, 149, 237) if settings.get_sound() else (200, 200, 200)
        pygame.draw.rect(self.screen, color, sound_rect, border_radius=8)
        pygame.draw.rect(self.screen, (100, 100, 100), sound_rect, 2, border_radius=8)
        sound_text = "开启" if settings.get_sound() else "关闭"
        text = self.fonts['normal'].render(sound_text, True, self.colors['text'])
        text_rect = text.get_rect(center=sound_rect.center)
        self.screen.blit(text, text_rect)

        for btn in self.buttons['settings']:
            btn.draw(self.screen, self.fonts['normal'])

    def _draw_choose(self):
        title = self.fonts['subtitle'].render("选择你的棋子", True, self.colors['text'])
        title_rect = title.get_rect(center=(self.width // 2, 150))
        self.screen.blit(title, title_rect)

        hint = self.fonts['small'].render("黑棋先行", True, (150, 150, 150))
        hint_rect = hint.get_rect(center=(self.width // 2, 200))
        self.screen.blit(hint, hint_rect)

        pygame.draw.circle(self.screen, self.colors['black'], (self.width // 2 - 125, 300), 35)
        pygame.draw.circle(self.screen, self.colors['white'], (self.width // 2 + 125, 300), 35)
        pygame.draw.circle(self.screen, (150, 150, 150), (self.width // 2 + 125, 300), 35, 2)

        for btn in self.buttons['choose']:
            btn.draw(self.screen, self.fonts['normal'])

    def _draw_game(self):
        self._draw_board()
        self._draw_pieces()
        self._draw_game_info()

        for btn in self.buttons['game']:
            btn.draw(self.screen, self.fonts['small'])

    def _draw_board(self):
        pygame.draw.rect(self.screen, self.colors['board'],
                         (self.board_x - self.board_padding, self.board_y - self.board_padding,
                          self.board_width + self.board_padding * 2, self.board_width + self.board_padding * 2))

        for i in range(self.board_size):
            start_x = self.board_x
            start_y = self.board_y + i * self.cell_size
            end_x = self.board_x + self.board_width
            end_y = start_y
            pygame.draw.line(self.screen, self.colors['line'], (start_x, start_y), (end_x, end_y), 1)

            start_x = self.board_x + i * self.cell_size
            start_y = self.board_y
            end_x = start_x
            end_y = self.board_y + self.board_width
            pygame.draw.line(self.screen, self.colors['line'], (start_x, start_y), (end_x, end_y), 1)

        star_points = [(3, 3), (3, 11), (7, 7), (11, 3), (11, 11)]
        for row, col in star_points:
            x = self.board_x + col * self.cell_size
            y = self.board_y + row * self.cell_size
            pygame.draw.circle(self.screen, self.colors['line'], (x, y), 4)

    def _draw_pieces(self):
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.board[row][col] != 0:
                    x = self.board_x + col * self.cell_size
                    y = self.board_y + row * self.cell_size
                    color = self.colors['black'] if self.board[row][col] == 1 else self.colors['white']
                    pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 2 - 2)
                    if self.board[row][col] == 2:
                        pygame.draw.circle(self.screen, (150, 150, 150), (x, y), self.cell_size // 2 - 2, 1)

    def _draw_game_info(self):
        round_text = self.fonts['normal'].render(f"回合: {counter.get_round_count() + 1}", True, self.colors['text'])
        self.screen.blit(round_text, (20, 20))

        remaining = counter.get_remaining_time()
        time_color = (255, 0, 0) if remaining <= 5 else self.colors['text']
        time_text = self.fonts['normal'].render(f"剩余时间: {remaining}秒", True, time_color)
        self.screen.blit(time_text, (20, 55))

        current_text = "你的回合" if self.current_player == self.player_color else "AI思考中..."
        text_color = self.colors['accent'] if self.current_player == self.player_color else (200, 100, 100)
        turn_text = self.fonts['normal'].render(current_text, True, text_color)
        self.screen.blit(turn_text, (20, 90))

        player_color_text = "黑棋" if self.player_color == 1 else "白棋"
        color_text = self.fonts['small'].render(f"你执: {player_color_text}", True, self.colors['text'])
        self.screen.blit(color_text, (20, 125))

        if self.waiting_for_ai:
            thinking = self.fonts['normal'].render("AI思考中...", True, (200, 100, 100))
            thinking_rect = thinking.get_rect(center=(self.width // 2, 30))
            self.screen.blit(thinking, thinking_rect)

    def _draw_end(self):
        self._draw_board()
        self._draw_pieces()

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(self.width // 2 - 250, self.height // 2 - 200, 500, 400)
        pygame.draw.rect(self.screen, (250, 250, 250), panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, self.colors['accent'], panel_rect, 3, border_radius=15)

        if self.game_result == 'win':
            if self.winner == self.player_color:
                result_text = "恭喜你获胜！"
                result_color = (34, 139, 34)
            else:
                result_text = "AI获胜，再接再厉！"
                result_color = (200, 50, 50)
        elif self.game_result == 'draw':
            result_text = "平局！"
            result_color = (100, 100, 100)
        else:
            result_text = "超时判负！"
            result_color = (200, 50, 50)

        title = self.fonts['subtitle'].render("游戏结束", True, self.colors['text'])
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 140))
        self.screen.blit(title, title_rect)

        result = self.fonts['normal'].render(result_text, True, result_color)
        result_rect = result.get_rect(center=(self.width // 2, self.height // 2 - 80))
        self.screen.blit(result, result_rect)

        rounds = counter.get_round_count()
        total_time = counter.get_total_time()
        minutes = total_time // 60
        seconds = total_time % 60

        info1 = self.fonts['normal'].render(f"回合数: {rounds} 轮", True, self.colors['text'])
        info1_rect = info1.get_rect(center=(self.width // 2, self.height // 2 - 20))
        self.screen.blit(info1, info1_rect)

        info2 = self.fonts['normal'].render(f"总耗时: {minutes}分{seconds}秒", True, self.colors['text'])
        info2_rect = info2.get_rect(center=(self.width // 2, self.height // 2 + 20))
        self.screen.blit(info2, info2_rect)

        for btn in self.buttons['end']:
            btn.draw(self.screen, self.fonts['normal'])

    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    counter.stop_game()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = pygame.mouse.get_pos()
                    if self.current_page == 'home':
                        for btn in self.buttons['home']:
                            if btn.handle_event(event):
                                break
                    elif self.current_page == 'settings':
                        self._handle_settings_click(pos)
                        for btn in self.buttons['settings']:
                            if btn.handle_event(event):
                                break
                    elif self.current_page == 'choose':
                        for btn in self.buttons['choose']:
                            if btn.handle_event(event):
                                break
                    elif self.current_page == 'game':
                        for btn in self.buttons['game']:
                            if btn.handle_event(event):
                                break
                        if not self.game_over:
                            self._handle_click(pos)
                    elif self.current_page == 'end':
                        for btn in self.buttons['end']:
                            if btn.handle_event(event):
                                break
                elif event.type == pygame.MOUSEMOTION:
                    for page_buttons in self.buttons.values():
                        for btn in page_buttons:
                            btn.handle_event(event)
                elif event.type == pygame.USEREVENT:
                    action = event.__dict__.get('action')
                    if action == 'check_result':
                        self._process_check_result(event.__dict__)
                    elif action == 'ai_move':
                        move = event.__dict__.get('move')
                        self._process_ai_move(move)
                    elif action == 'do_timeout':
                        self._do_timeout()

            if self.game_over and self.current_page == 'game':
                self.current_page = 'end'

            self.draw()
            clock.tick(30)

        pygame.quit()
        sys.exit()
