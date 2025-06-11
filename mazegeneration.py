import random

def generate_maze(width=20, height=20):
    # Initialize grid with walls
    grid = [['#' for _ in range(width)] for _ in range(height)]
    
    # Create a path using Prim's algorithm
    walls = []
    start_x, start_y = random.randint(1, width-2), random.randint(1, height-2)
    grid[start_y][start_x] = ' '
    
    # Add neighboring walls
    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
        nx, ny = start_x + dx, start_y + dy
        if 0 < nx < width-1 and 0 < ny < height-1:
            walls.append((nx, ny, start_x, start_y))
    
    while walls:
        # Pick a random wall
        wall_x, wall_y, origin_x, origin_y = walls.pop(random.randint(0, len(walls)-1))
        
        # Check if it's still a wall
        if grid[wall_y][wall_x] != '#':
            continue
            
        # Check how many cells it would connect
        connected = 0
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
            nx, ny = wall_x + dx, wall_y + dy
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == ' ':
                connected += 1
        
        # If connecting exactly one cell, carve passage
        if connected == 1:
            grid[wall_y][wall_x] = ' '
            
            # Add new walls
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = wall_x + dx, wall_y + dy
                if 0 < nx < width-1 and 0 < ny < height-1 and grid[ny][nx] == '#':
                    walls.append((nx, ny, wall_x, wall_y))
    
    # Add special elements ensuring solvability
    empty_cells = [(x, y) for y in range(height) for x in range(width) if grid[y][x] == ' ']
    
    # 1. Start (S) and End (E) positions - ensure they're connected
    # Find all reachable cells from a random starting point
    start = random.choice(empty_cells)
    visited = set()
    stack = [start]
    
    while stack:
        x, y = stack.pop()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] in (' ', 'P', 'T'):
                stack.append((nx, ny))
    
    # Only use reachable cells for placement
    reachable_cells = list(visited)
    
    if not reachable_cells:
        # If no reachable cells (shouldn't happen with proper generation), use all empty cells
        reachable_cells = empty_cells.copy()
    
    # Place start and end in reachable cells
    start = random.choice(reachable_cells)
    reachable_cells.remove(start)
    
    # Find the farthest reachable cell from start to place end
    distances = {}
    queue = [(start, 0)]
    visited_dist = set()
    
    while queue:
        (x, y), dist = queue.pop(0)
        if (x, y) in visited_dist:
            continue
        visited_dist.add((x, y))
        distances[(x, y)] = dist
        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] in (' ', 'P', 'T'):
                queue.append(((nx, ny), dist + 1))
    
    if distances:
        end = max(distances.keys(), key=lambda pos: distances[pos])
    else:
        end = random.choice(reachable_cells) if reachable_cells else start
    
    grid[start[1]][start[0]] = 'S'
    grid[end[1]][end[0]] = 'E'
    
    # Remove start and end from empty cells if they were there
    empty_cells = [(x, y) for y in range(height) for x in range(width) 
                  if grid[y][x] == ' ' and (x, y) != start and (x, y) != end]
    
    # 2. Teleport pairs (T) - ensure both are reachable
    if len(empty_cells) >= 2:
        teleport1 = random.choice(empty_cells)
        empty_cells.remove(teleport1)
        teleport2 = random.choice(empty_cells)
        empty_cells.remove(teleport2)
        grid[teleport1[1]][teleport1[0]] = 'T'
        grid[teleport2[1]][teleport2[0]] = 'T'
    
    # 3. Penalty tiles (P) - about 5% of empty spaces, ensure they're reachable
    penalty_count = max(1, len(empty_cells) // 20)
    for _ in range(penalty_count):
        if not empty_cells:
            break
        penalty = random.choice(empty_cells)
        empty_cells.remove(penalty)
        grid[penalty[1]][penalty[0]] = 'P'
    
    return grid

def save_maze(grid, filename="maze.txt"):
    with open(filename, 'w') as f:
        for row in grid:
            f.write(''.join(row) + '\n')

if __name__ == "__main__":
    maze = generate_maze(20, 20)
    save_maze(maze)
    print("20x20 maze generated and saved to maze.txt")