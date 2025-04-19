import pygame
import random
import time
import sys
from pygame.locals import *

# 初始化pygame
pygame.init()

# 游戏常量
SCREEN_SIZE = (800, 700)
MAX_LEVEL = 15  # 总关卡改为15关
FPS = 60

# 专业配色方案
COLORS = {
    "background": (245, 245, 245),
    "card_back": (79, 129, 189),
    "card_front": (255, 255, 255),
    "matched": (67, 160, 71),
    "selected": (244, 67, 54),
    "text": (33, 33, 33),
    "timer": (3, 169, 244),
    "warning": (255, 152, 0),
    "level": (156, 39, 176)
}

class DifficultyManager:
    """难度管理系统（新版）"""
    def __init__(self):
        self.current_level = 1
        self.max_moves = None
        self.time_limit = None
    
    def calculate_grid_size(self):
        """根据关卡返回网格尺寸"""
        if self.current_level == 1:
            return 2    # 2x2
        elif self.current_level == 2:
            return 4    # 4x4
        else:            # 第3关及之后都是6x6
            return 6
    
    def calculate_max_moves(self):
        """设置翻转次数限制"""
        if 1 <= self.current_level <= 8:   # 前8关不限制次数
            return None
        elif 9 <= self.current_level <= 15: # 9-15关限制100次
            return 100
    
    def calculate_time_limit(self):
        """设置时间限制"""
        if 1 <= self.current_level <= 4:    # 前4关不限时
            return None
        elif 5 <= self.current_level <= 8:  # 5-8关时间限制
            return 300 - (self.current_level - 5) * 50  # 从60秒开始每关减10秒
        elif 9 <= self.current_level <= 15: # 9-15关时间限制
            return 120 - (self.current_level - 9) * 30   # 从50秒开始每关减5秒
    
    def level_up(self):
        self.current_level = min(self.current_level + 1, MAX_LEVEL)
        self.max_moves = self.calculate_max_moves()
        self.time_limit = self.calculate_time_limit()

class Card:
    """卡片类（优化版）"""
    def __init__(self, x, y, size, value):
        self.rect = pygame.Rect(x, y, size, size)
        self.value = value
        self.face_up = False
        self.matched = False
        self.size = size
    
    def draw(self, surface):
        border_color = COLORS["selected"] if self.face_up and not self.matched else COLORS["background"]
        pygame.draw.rect(surface, (200, 200, 200), self.rect.move(3, 3), border_radius=5)
        pygame.draw.rect(surface, border_color, self.rect.inflate(4, 4), border_radius=7)
        
        if self.matched:
            pygame.draw.rect(surface, COLORS["matched"], self.rect, border_radius=5)
        elif self.face_up:
            pygame.draw.rect(surface, COLORS["card_front"], self.rect, border_radius=5)
            font = pygame.font.SysFont("Arial", max(20, self.size // 3))
            text = font.render(str(self.value), True, COLORS["text"])
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)
        else:
            pygame.draw.rect(surface, COLORS["card_back"], self.rect, border_radius=5)

class MemoryGame:
    """游戏主逻辑（新版）"""
    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.grid_size = difficulty.calculate_grid_size()
        self.validate_grid_size()
        self.cards = []
        self.selected = []
        self.moves_left = int(difficulty.max_moves) if difficulty.max_moves is not None else float('inf')
        self.start_time = time.time()
        self.last_flip_time = 0
        self.init_game()
    
    def validate_grid_size(self):
        """确保网格尺寸为偶数"""
        if self.grid_size % 2 != 0:
            self.grid_size += 1
    
    def init_game(self):
        """初始化游戏板"""
        card_count = self.grid_size ** 2
        pairs = list(range(1, (card_count // 2) + 1)) * 2
        random.shuffle(pairs)
        
        card_size = min(80, (SCREEN_SIZE[0] - 100) // self.grid_size - 10)
        margin = 5
        
        start_x = (SCREEN_SIZE[0] - (card_size + margin) * self.grid_size) // 2
        start_y = 120
        
        self.cards = []
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x = start_x + j * (card_size + margin)
                y = start_y + i * (card_size + margin)
                self.cards.append(Card(x, y, card_size, pairs[i * self.grid_size + j]))
    
    def handle_click(self, pos):
        if time.time() - self.last_flip_time < 0.5:  # 防止快速连点
            return
        
        for card in self.cards:
            if card.rect.collidepoint(pos) and not card.matched and not card.face_up:
                if len(self.selected) >= 2:
                    return
                
                card.face_up = True
                self.selected.append(card)
                self.last_flip_time = time.time()
                
                if len(self.selected) == 2:
                    if self.difficulty.max_moves is not None:
                        self.moves_left -= 1
                    self.check_match()
                return
    
    def check_match(self):
        if self.selected[0].value == self.selected[1].value:
            self.selected[0].matched = True
            self.selected[1].matched = True
            self.selected = []
        else:
            pygame.time.set_timer(USEREVENT + 1, 1000, loops=1)
    
    def update(self):
        if all(card.matched for card in self.cards):
            return "win"
        if self.moves_left <= 0:
            return "lose"
        if self.difficulty.time_limit is not None and time.time() - self.start_time > self.difficulty.time_limit:
            return "timeout"
        return "playing"
    
    def draw(self, surface):
        surface.fill(COLORS["background"])
        
        # 绘制游戏信息
        font = pygame.font.SysFont("Arial", 24)
        info_y = 20
        surface.blit(font.render(f"Level: {self.difficulty.current_level}", 
                          True, COLORS["level"]), (20, info_y))
        surface.blit(font.render(f"Moves: {self.moves_left}", 
                          True, COLORS["text"]), (20, info_y + 40))
        if self.difficulty.time_limit is not None:
            surface.blit(font.render(f"Time: {int(self.difficulty.time_limit - (time.time() - self.start_time))}s", 
                              True, COLORS["timer"]), (SCREEN_SIZE[0] - 150, info_y))
        
        # 绘制卡片
        for card in self.cards:
            card.draw(surface)

def show_message(surface, text, color, duration=2):
    font = pygame.font.SysFont("Arial", 48, bold=True)
    text_surf = font.render(text, True, color)
    rect = text_surf.get_rect(center=(SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2))
    
    overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 180))
    surface.blit(overlay, (0, 0))
    surface.blit(text_surf, rect)
    pygame.display.flip()
    time.sleep(duration)

def main():
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("记忆大师 - 升级版")
    clock = pygame.time.Clock()
    difficulty = DifficultyManager()
    
    while difficulty.current_level <= MAX_LEVEL:
        game = MemoryGame(difficulty)
        result = "playing"
        
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    game.handle_click(event.pos)
                if event.type == USEREVENT + 1:  # 定时翻回卡片
                    for card in game.selected:
                        card.face_up = False
                    game.selected = []
            
            result = game.update()
            game.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)
            
            if result != "playing":
                break
        
        if result == "win":
            show_message(screen, "闯关成功！", COLORS["matched"])
            difficulty.level_up()
        else:
            show_message(screen, f"游戏结束！原因：{'时间用尽' if result == 'timeout' else '次数用尽'}", 
                          COLORS["warning"], 3)
            break
    
    # 通关所有关卡后显示特殊信息
    if difficulty.current_level > MAX_LEVEL:
        show_message(screen, "恭喜通关所有关卡！", COLORS["level"], 5)
    
    pygame.quit()

if __name__ == "__main__":
    main()