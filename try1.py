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

class AStarSolver(MazeSolver):
    def __init__(self, maze: List[List[MazeCell]]):
        super().__init__(maze)
        import heapq
        self.open_set = []
        self.g_score = {}
        self.f_score = {}
        self.heapq = heapq
        self.counter = 0  # Unique counter for heapq tiebreaker

    def heuristic(self, cell: MazeCell) -> int:
        # Manhattan distance
        return abs(cell.x - self.end.x) + abs(cell.y - self.end.y)

    def solve(self):
        start = self.start
        self.g_score[(start.x, start.y)] = 0
        self.f_score[(start.x, start.y)] = self.heuristic(start)
        self.counter += 1
        self.heapq.heappush(self.open_set, (self.f_score[(start.x, start.y)], self.counter, start))
        self.visited.add((start.x, start.y))
        while self.open_set:
            _, _, self.current_cell = self.heapq.heappop(self.open_set)
            if self.current_cell == self.end:
                self.path = self.reconstruct_path(self.current_cell)
                self.solution_found = True
                yield True
                return True
            special_target = self.process_special_cell(self.current_cell)
            if special_target:
                if (special_target.x, special_target.y) not in self.visited:
                    special_target.parent = self.current_cell
                    self.visited.add((special_target.x, special_target.y))
                    self.g_score[(special_target.x, special_target.y)] = self.g_score[(self.current_cell.x, self.current_cell.y)] + 1
                    self.f_score[(special_target.x, special_target.y)] = self.g_score[(special_target.x, special_target.y)] + self.heuristic(special_target)
                    self.counter += 1
                    self.heapq.heappush(self.open_set, (self.f_score[(special_target.x, special_target.y)], self.counter, special_target))
                yield False
                continue
            for neighbor in self.get_neighbors(self.current_cell):
                if (neighbor.x, neighbor.y) not in self.visited:
                    tentative_g = self.g_score[(self.current_cell.x, self.current_cell.y)] + 1
                    if ((neighbor.x, neighbor.y) not in self.g_score) or (tentative_g < self.g_score[(neighbor.x, neighbor.y)]):
                        neighbor.parent = self.current_cell
                        self.g_score[(neighbor.x, neighbor.y)] = tentative_g
                        self.f_score[(neighbor.x, neighbor.y)] = tentative_g + self.heuristic(neighbor)
                        self.counter += 1
                        self.heapq.heappush(self.open_set, (self.f_score[(neighbor.x, neighbor.y)], self.counter, neighbor))
                        self.visited.add((neighbor.x, neighbor.y))
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
            row.append(MazeCell(j, i, cell_type))  # FIXED: x=j (col), y=i (row)
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
        self.original_maze = maze
        self.rows = len(maze)
        self.cols = len(maze[0]) if self.rows > 0 else 0
        
        # Calculate max viewable area
        screen_info = pygame.display.Info()
        max_width = screen_info.current_w - 100
        max_height = screen_info.current_h - 200
        
        # Each panel gets a third of the width
        self.cell_size = min(BASE_CELL_SIZE, 
                            max_width // (3 * max(1, self.cols)), 
                            max_height // max(1, self.rows))
        
        self.view_width = min(max_width // 3, self.cols * self.cell_size)
        self.view_height = min(max_height, self.rows * self.cell_size)
        
        # Set up viewport
        self.window_width = self.view_width * 3
        self.window_height = self.view_height + 150
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption("Maze Solver Visualizer: BFS vs DFS vs A*")
        
        # Create three solvers with independent maze copies
        import copy
        self.bfs_solver = BFSSolver(copy.deepcopy(maze))
        self.dfs_solver = DFSSolver(copy.deepcopy(maze))
        self.astar_solver = AStarSolver(copy.deepcopy(maze))
        self.bfs_gen = None
        self.dfs_gen = None
        self.astar_gen = None
        self.visualizing = False
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 20)
        self.big_font = pygame.font.SysFont('Arial', 32, bold=True)
        
        # Buttons
        self.buttons = [
            Button(self.window_width//2 - 60, self.view_height + 20, 120, 40, "Start", START_BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR)
        ]

    def handle_events(self) -> bool:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                self.window_width, self.window_height = event.w, event.h
                self.view_width = self.window_width // 3
                self.view_height = self.window_height - 150
                self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
                self.cell_size = min(BASE_CELL_SIZE, self.view_width // max(1, self.cols), self.view_height // max(1, self.rows))
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_click = True
        # Handle Start button
        if mouse_click and not self.visualizing:
            for button in self.buttons:
                if button.is_clicked(mouse_pos, mouse_click):
                    if button.text == "Start":
                        self.bfs_solver = BFSSolver([ [MazeCell(cell.x, cell.y, cell.type) for cell in row] for row in self.original_maze])
                        self.dfs_solver = DFSSolver([ [MazeCell(cell.x, cell.y, cell.type) for cell in row] for row in self.original_maze])
                        self.astar_solver = AStarSolver([ [MazeCell(cell.x, cell.y, cell.type) for cell in row] for row in self.original_maze])
                        self.bfs_gen = self.bfs_solver.solve()
                        self.dfs_gen = self.dfs_solver.solve()
                        self.astar_gen = self.astar_solver.solve()
                        self.visualizing = True
        return True

    def update(self):
        # Each algorithm should run independently until it finds the end
        if self.visualizing:
            if self.bfs_gen is not None and not self.bfs_solver.solution_found:
                try:
                    next(self.bfs_gen)
                except StopIteration:
                    self.bfs_gen = None
            if self.dfs_gen is not None and not self.dfs_solver.solution_found:
                try:
                    next(self.dfs_gen)
                except StopIteration:
                    self.dfs_gen = None
            if self.astar_gen is not None and not self.astar_solver.solution_found:
                try:
                    next(self.astar_gen)
                except StopIteration:
                    self.astar_gen = None
            # Only stop visualizing when all are done
            if ((self.bfs_solver.solution_found or self.bfs_gen is None) and
                (self.dfs_solver.solution_found or self.dfs_gen is None) and
                (self.astar_solver.solution_found or self.astar_gen is None)):
                self.visualizing = False

    def draw_cell(self, cell: MazeCell, rect: pygame.Rect, solver=None):
        # Draw a cell for a given solver (BFS or DFS)
        if solver:
            if cell == solver.current_cell:
                color = CURRENT_COLOR
            elif cell in solver.path:
                color = PATH_COLOR_FINAL
            elif (cell.x, cell.y) in solver.visited:
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
        # Draw BFS panel (left)
        for i in range(self.rows):
            for j in range(self.cols):
                cell = self.bfs_solver.maze[i][j]
                x = j * self.cell_size
                y = i * self.cell_size
                if 0 <= x < self.view_width and 0 <= y < self.view_height:
                    rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    self.draw_cell(cell, rect, solver=self.bfs_solver)
        # Draw DFS panel (middle)
        for i in range(self.rows):
            for j in range(self.cols):
                cell = self.dfs_solver.maze[i][j]
                x = self.view_width + j * self.cell_size
                y = i * self.cell_size
                if self.view_width <= x < self.view_width * 2 and 0 <= y < self.view_height:
                    rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    self.draw_cell(cell, rect, solver=self.dfs_solver)
        # Draw A* panel (right)
        for i in range(self.rows):
            for j in range(self.cols):
                cell = self.astar_solver.maze[i][j]
                x = self.view_width * 2 + j * self.cell_size
                y = i * self.cell_size
                if self.view_width * 2 <= x < self.window_width and 0 <= y < self.view_height:
                    rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                    self.draw_cell(cell, rect, solver=self.astar_solver)
        # Draw panel titles
        bfs_title = self.big_font.render("BFS", True, (0, 0, 128))
        dfs_title = self.big_font.render("DFS", True, (128, 0, 0))
        astar_title = self.big_font.render("A*", True, (0, 128, 0))
        self.screen.blit(bfs_title, (self.view_width//2 - bfs_title.get_width()//2, 10))
        self.screen.blit(dfs_title, (self.view_width + self.view_width//2 - dfs_title.get_width()//2, 10))
        self.screen.blit(astar_title, (self.view_width*2 + self.view_width//2 - astar_title.get_width()//2, 10))
        # Draw buttons
        for button in self.buttons:
            button.check_hover(pygame.mouse.get_pos())
            button.color = DISABLED_COLOR if self.visualizing else START_BUTTON_COLOR
            button.draw(self.screen)
        # Draw info for all solvers
        bfs_status = "Solved!" if self.bfs_solver.solution_found else "Solving..." if self.visualizing else "Ready"
        dfs_status = "Solved!" if self.dfs_solver.solution_found else "Solving..." if self.visualizing else "Ready"
        astar_status = "Solved!" if self.astar_solver.solution_found else "Solving..." if self.visualizing else "Ready"
        bfs_steps = self.font.render(f"BFS | Steps: {self.bfs_solver.steps} | {bfs_status}", True, TEXT_COLOR)
        dfs_steps = self.font.render(f"DFS | Steps: {self.dfs_solver.steps} | {dfs_status}", True, TEXT_COLOR)
        astar_steps = self.font.render(f"A* | Steps: {self.astar_solver.steps} | {astar_status}", True, TEXT_COLOR)
        self.screen.blit(bfs_steps, (20, self.view_height + 70))
        self.screen.blit(dfs_steps, (self.view_width + 20, self.view_height + 70))
        self.screen.blit(astar_steps, (self.view_width*2 + 20, self.view_height + 70))
        # Solved effects
        if self.bfs_solver.solution_found:
            color = (0, 255, 0) if (pygame.time.get_ticks() // 300) % 2 == 0 else (255, 255, 0)
            pygame.draw.rect(self.screen, color, (0, 0, self.view_width, self.view_height), 10)
        if self.dfs_solver.solution_found:
            color = (0, 255, 0) if (pygame.time.get_ticks() // 300) % 2 == 0 else (255, 255, 0)
            pygame.draw.rect(self.screen, color, (self.view_width, 0, self.view_width, self.view_height), 10)
        if self.astar_solver.solution_found:
            color = (0, 255, 0) if (pygame.time.get_ticks() // 300) % 2 == 0 else (255, 255, 0)
            pygame.draw.rect(self.screen, color, (self.view_width*2, 0, self.view_width, self.view_height), 10)
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
    ######
    #we tryed to make the maze solver visualizer more efficient and user-friendly
    #by reducing the cell size, optimizing the drawing logic, and improving the UI