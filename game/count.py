import time
import threading


class GameCounter:
    def __init__(self):
        self.round_count = 0
        self.total_time = 0
        self.move_time_limit = 15
        self.current_move_start = 0
        self.is_running = False
        self._timer_thread = None
        self._stop_timer = threading.Event()
        self.on_timeout = None
        self._lock = threading.Lock()

    def reset(self):
        with self._lock:
            self.round_count = 0
            self.total_time = 0
            self.current_move_start = 0
            self.is_running = False
            self._stop_timer.clear()

    def start_game(self):
        with self._lock:
            self.total_time = 0
            self.round_count = 0
            self.is_running = True

    def start_move(self):
        with self._lock:
            self.current_move_start = time.time()
            self._stop_timer.clear()
            if self._timer_thread and self._timer_thread.is_alive():
                self._stop_timer.set()
                self._timer_thread.join(timeout=0.5)
            self._timer_thread = threading.Thread(target=self._countdown, daemon=True)
            self._timer_thread.start()

    def _countdown(self):
        start_time = self.current_move_start
        while self.is_running and not self._stop_timer.is_set():
            elapsed = time.time() - start_time
            remaining = self.move_time_limit - elapsed
            if remaining <= 0:
                if self.on_timeout:
                    self.on_timeout()
                break
            time.sleep(0.1)

    def stop_move(self):
        with self._lock:
            self._stop_timer.set()
            if self._timer_thread and self._timer_thread.is_alive():
                self._timer_thread.join(timeout=0.5)
            move_time = time.time() - self.current_move_start
            self.total_time += move_time

    def increment_round(self):
        with self._lock:
            self.round_count += 1

    def get_remaining_time(self):
        with self._lock:
            if not self.is_running or self.current_move_start == 0:
                return self.move_time_limit
            elapsed = time.time() - self.current_move_start
            remaining = self.move_time_limit - elapsed
            return max(0, int(remaining + 1))

    def get_total_time(self):
        with self._lock:
            return int(self.total_time)

    def get_round_count(self):
        with self._lock:
            return self.round_count

    def stop_game(self):
        with self._lock:
            self.is_running = False
            self._stop_timer.set()
            if self._timer_thread and self._timer_thread.is_alive():
                self._timer_thread.join(timeout=0.5)


counter = GameCounter()
