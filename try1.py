import pygame
import sys
from collections import deque
from enum import Enum
from typing import List, Tuple, Optional

# Constants
BASE_CELL_SIZE = 20  # Reduced size to fit large mazes
WALL_COLOR = (0, 0, 0)
PATH_COLOR = (255, 255, 255)
START_COLOR = (0, 255, 0)
END_COLOR = (255, 0, 0)
VISITED_COLOR = (173, 216, 230)
CURRENT_COLOR = (255, 255, 0)
PATH_COLOR_FINAL = (128, 0, 128)
SPECIAL_COLOR = (255, 165, 0)
TEXT_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (240, 240, 240)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (100, 150, 200)
BUTTON_TEXT_COLOR = (255, 255, 255)
START_BUTTON_COLOR = (50, 150, 50)
DISABLED_COLOR = (100, 100, 100)

class TileType(Enum):
    WALL = '#'
    PATH = ' '
    START = 'S'
    END = 'E'
    TELEPORT = 'T'
    PENALTY = 'P'

class MazeCell:
    def __init__(self, x: int, y: int, cell_type: TileType):
        self.x = x
        self.y = y
        self.type = cell_type
        self.visited = False
        self.in_path = False
        self.parent = None
        self.special_data = {}

    def __str__(self):
        return f"({self.x},{self.y}) {self.type.name}"

class MazeSolver:
    def __init__(self, maze: List[List[MazeCell]]):
        self.maze = maze
        self.visited = set()
        self.steps = 0
        self.path = []
        self.start = None
        self.end = None
        self.solution_found = False
        self.current_cell = None
        self.initialize_maze()

    def initialize_maze(self):
        for row in self.maze:
            for cell in row:
                if cell.type == TileType.START:
                    self.start = cell
                elif cell.type == TileType.END:
                    self.end = cell
        
        if not self.start or not self.end:
            raise ValueError("Maze must have both start and end points")

    def get_neighbors(self, cell: MazeCell) -> List[MazeCell]:
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
        
        for dx, dy in directions:
            x, y = cell.x + dx, cell.y + dy
            if 0 <= x < len(self.maze[0]) and 0 <= y < len(self.maze):
                neighbor = self.maze[y][x]  # FIXED: correct row/col order
                if neighbor.type != TileType.WALL:
                    neighbors.append(neighbor)
        
        return neighbors

    def reconstruct_path(self, cell: MazeCell) -> List[MazeCell]:
        path = []
        while cell:
            path.append(cell)
            cell = cell.parent
        return path[::-1]  # Reverse to get start to end

    def process_special_cell(self, cell: MazeCell) -> Optional[MazeCell]:
        if cell.type == TileType.TELEPORT:
            for row in self.maze:
                for other_cell in row:
                    if other_cell.type == TileType.TELEPORT and other_cell != cell:
                        # Mark both teleports as visited to prevent infinite bouncing
                        self.visited.add((cell.x, cell.y))
                        self.visited.add((other_cell.x, other_cell.y))
                        return other_cell
        return None

    def solve(self):
        raise NotImplementedError("Subclasses must implement solve method")

class BFSSolver(MazeSolver):
    def __init__(self, maze: List[List[MazeCell]]):
        super().__init__(maze)
        self.queue = deque()

    def solve(self):
        self.queue.append(self.start)
        self.visited.add((self.start.x, self.start.y))
        
        while self.queue:
            self.current_cell = self.queue.popleft()
            
            if self.current_cell == self.end:
                self.path = self.reconstruct_path(self.current_cell)
                self.solution_found = True
                yield True  # Yield once more so UI can update
                return True
            
            special_target = self.process_special_cell(self.current_cell)
            if special_target:
                if (special_target.x, special_target.y) not in self.visited:
                    special_target.parent = self.current_cell
                    self.visited.add((special_target.x, special_target.y))
                    self.queue.append(special_target)
                continue
            
            for neighbor in self.get_neighbors(self.current_cell):
                if (neighbor.x, neighbor.y) not in self.visited:
                    self.visited.add((neighbor.x, neighbor.y))
                    neighbor.parent = self.current_cell
                    self.queue.append(neighbor)
            
            self.steps += 1
            yield False
        
        return False

class DFSSolver(MazeSolver):
    def __init__(self, maze: List[List[MazeCell]]):
        super().__init__(maze)
        self.stack = []

    def solve(self):
        self.stack.append(self.start)
        self.visited.add((self.start.x, self.start.y))
        
        while self.stack:
            self.current_cell = self.stack.pop()
            
            if self.current_cell == self.end:
                self.path = self.reconstruct_path(self.current_cell)
                self.solution_found = True
                yield True  # Yield once more so UI can update
                return True
            
            special_target = self.process_special_cell(self.current_cell)
            if special_target:
                if (special_target.x, special_target.y) not in self.visited:
                    special_target.parent = self.current_cell
                    self.visited.add((special_target.x, special_target.y))
                    self.stack.append(special_target)
                continue
            
            for neighbor in self.get_neighbors(self.current_cell):
                if (neighbor.x, neighbor.y) not in self.visited:
                    self.visited.add((neighbor.x, neighbor.y))
                    neighbor.parent = self.current_cell
                    self.stack.append(neighbor)
            
            self.steps += 1
            yield False
        
        return False

def load_maze(filename: str) -> List[List[MazeCell]]:
    try:
        with open(filename, 'r') as f:
            lines = [line.strip('\n') for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: Could not find {filename}")
        print("Please create a maze.txt file in the same directory")
        sys.exit(1)
    
    if not lines:
        print("Error: maze.txt is empty")
        sys.exit(1)
    
    maze = []
    for i, line in enumerate(lines):
        row = []
        for j, char in enumerate(line):
            try:
                cell_type = TileType(char)
            except ValueError:
                print(f"Warning: Invalid character '{char}' at row {i}, column {j} - treating as path")
                cell_type = TileType.PATH
            row.append(MazeCell(i, j, cell_type))
        maze.append(row)
    
    return maze

class Button:
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, color: Tuple[int, int, int], 
                 hover_color: Tuple[int, int, int], text_color: Tuple[int, int, int]):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont('Arial', 24)
        self.is_hovered = False

    def draw(self, surface: pygame.Surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=5)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos: Tuple[int, int]) -> bool:
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def is_clicked(self, mouse_pos: Tuple[int, int], mouse_click: bool) -> bool:
        return self.rect.collidepoint(mouse_pos) and mouse_click

class MazeViewer:
    def __init__(self, maze: List[List[MazeCell]]):
        pygame.init()
        self.maze = maze
        self.rows = len(maze)
        self.cols = len(maze[0]) if self.rows > 0 else 0
        
        # Calculate max viewable area
        screen_info = pygame.display.Info()
        max_width = screen_info.current_w - 100
        max_height = screen_info.current_h - 200
        
        # Calculate cell size that fits the maze
        self.cell_size = min(BASE_CELL_SIZE, 
                            max_width // max(1, self.cols), 
                            max_height // max(1, self.rows))
        
        # Set up viewport
        self.view_width = min(max_width, self.cols * self.cell_size)
        self.view_height = min(max_height, self.rows * self.cell_size)
        
        # Scroll position
        self.scroll_x = 0
        self.scroll_y = 0
        
        # Create window (RESIZABLE)
        self.window_width = self.view_width
        self.window_height = self.view_height + 150  # Space for controls
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption("Maze Solver Visualizer")
        
        # Create buttons
        self.buttons = [
            Button(20, self.view_height + 20, 100, 40, "BFS", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR),
            Button(140, self.view_height + 20, 100, 40, "DFS", BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR),
            Button(260, self.view_height + 20, 100, 40, "Start", START_BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR)
        ]
        
        self.solver = None
        self.solver_gen = None  # Store the generator
        self.visualizing = False
        self.dragging = False
        self.last_mouse_pos = (0, 0)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 20)

    def handle_events(self) -> bool:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.VIDEORESIZE:
                # Handle window resize
                self.window_width, self.window_height = event.w, event.h
                self.view_width = self.window_width
                self.view_height = self.window_height - 150
                self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
                # Optionally, recalculate cell_size to fit new window
                self.cell_size = min(BASE_CELL_SIZE, 
                                    self.view_width // max(1, self.cols), 
                                    self.view_height // max(1, self.rows))
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_click = True
                if event.button == 1:  # Left click
                    self.last_mouse_pos = mouse_pos
                    if mouse_pos[1] < self.view_height:  # Click on maze area
                        self.dragging = True
                
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
                    
            if event.type == pygame.MOUSEMOTION and self.dragging:
                dx = mouse_pos[0] - self.last_mouse_pos[0]
                dy = mouse_pos[1] - self.last_mouse_pos[1]
                self.scroll_x = max(0, min(self.scroll_x - dx, self.cols * self.cell_size - self.view_width))
                self.scroll_y = max(0, min(self.scroll_y - dy, self.rows * self.cell_size - self.view_height))
                self.last_mouse_pos = mouse_pos
        
        # Handle button clicks
        if mouse_click and not self.visualizing:
            for button in self.buttons:
                if button.is_clicked(mouse_pos, mouse_click):
                    if button.text == "BFS":
                        self.solver = BFSSolver(self.maze)
                        self.solver_gen = None
                    elif button.text == "DFS":
                        self.solver = DFSSolver(self.maze)
                        self.solver_gen = None
                    elif button.text == "Start" and self.solver:
                        self.solver_gen = self.solver.solve()  # Create the generator
                        self.visualizing = True
        
        return True

    def update(self):
        if self.visualizing and self.solver and self.solver_gen:
            try:
                # Only advance if not solved
                if not self.solver.solution_found:
                    next(self.solver_gen)
                    pygame.time.delay(100)  # Slightly faster visualization
                else:
                    self.visualizing = False  # Stop animation when solved
            except StopIteration:
                self.visualizing = False

    def draw_cell(self, cell: MazeCell, rect: pygame.Rect):
        if self.solver:
            # Always show the current cell as yellow, even if it's the end cell
            if cell == self.solver.current_cell:
                color = CURRENT_COLOR
            elif cell in self.solver.path:
                color = PATH_COLOR_FINAL
            elif (cell.x, cell.y) in self.solver.visited:
                color = VISITED_COLOR
            elif cell.type == TileType.START:
                color = START_COLOR
            elif cell.type == TileType.END:
                color = END_COLOR
            elif cell.type in (TileType.TELEPORT, TileType.PENALTY):
                color = SPECIAL_COLOR
            elif cell.type == TileType.WALL:
                color = WALL_COLOR
            else:
                color = PATH_COLOR
        else:
            if cell.type == TileType.START:
                color = START_COLOR
            elif cell.type == TileType.END:
                color = END_COLOR
            elif cell.type in (TileType.TELEPORT, TileType.PENALTY):
                color = SPECIAL_COLOR
            elif cell.type == TileType.WALL:
                color = WALL_COLOR
            else:
                color = PATH_COLOR
        
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)
        
        # Add labels for special cells
        if cell.type == TileType.TELEPORT:
            text = self.font.render('T', True, TEXT_COLOR)
            self.screen.blit(text, (rect.x + rect.width//2 - 5, rect.y + rect.height//2 - 10))
        elif cell.type == TileType.PENALTY:
            text = self.font.render('P', True, TEXT_COLOR)
            self.screen.blit(text, (rect.x + rect.width//2 - 5, rect.y + rect.height//2 - 10))

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw maze (only visible portion)
        start_col = max(0, self.scroll_x // self.cell_size)
        end_col = min(self.cols, start_col + self.view_width // self.cell_size + 2)
        start_row = max(0, self.scroll_y // self.cell_size)
        end_row = min(self.rows, start_row + self.view_height // self.cell_size + 2)
        
        for i in range(start_row, end_row):
            for j in range(start_col, end_col):
                cell = self.maze[i][j]
                x = j * self.cell_size - self.scroll_x
                y = i * self.cell_size - self.scroll_y
                
                if 0 <= x < self.view_width and 0 <= y < self.view_height:
                    rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    self.draw_cell(cell, rect)
        
        # Draw buttons
        for button in self.buttons:
            button.check_hover(pygame.mouse.get_pos())
            if button.text == "Start":
                button.color = DISABLED_COLOR if not self.solver or self.visualizing else START_BUTTON_COLOR
            button.draw(self.screen)
        
        # Draw instructions
        instr_text = self.font.render("1. Select algorithm 2. Click Start | Drag to scroll", True, TEXT_COLOR)
        self.screen.blit(instr_text, (20, self.view_height + 70))
        
        # Draw solver info
        if self.solver:
            algo_name = "BFS" if isinstance(self.solver, BFSSolver) else "DFS"
            status = "Solved!" if self.solver.solution_found else "Solving..." if self.visualizing else "Ready"
            steps_text = self.font.render(f"{algo_name} | Steps: {self.solver.steps} | {status}", True, TEXT_COLOR)
            self.screen.blit(steps_text, (20, self.view_height + 100))
            # Add effect when solved
            if self.solver.solution_found:
                # Flashing border effect
                color = (0, 255, 0) if (pygame.time.get_ticks() // 300) % 2 == 0 else (255, 255, 0)
                pygame.draw.rect(self.screen, color, (0, 0, self.window_width, self.view_height), 10)
                # Centered message
                big_font = pygame.font.SysFont('Arial', 48, bold=True)
                msg = big_font.render("MAZE SOLVED!", True, color)
                msg_rect = msg.get_rect(center=(self.window_width//2, self.view_height//2))
                self.screen.blit(msg, msg_rect)
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

def main():
    maze = load_maze("maze.txt")
    viewer = MazeViewer(maze)
    viewer.run()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()