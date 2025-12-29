"""
HydroRobot Application Launcher
Запуск анимации обхода робота по карте
"""

import random
from main import HydroRobot, HydroMaze, HydroNetCellType
from ui import launch_animation


def create_sample_maze() -> tuple:
    """
    Create a sample maze with water, shore, and barriers
    Создает пример лабиринта с водой, берегом и преградами
    """
    maze = HydroMaze(width=12, height=10)
    maze.InitializeMaze(HydroNetCellType.Water, 12, 10)

    # Add some shores
    for x in range(2, 5):
        maze.cells[5][x].cell_type = HydroNetCellType.Shore

    # Add barriers
    maze.cells[3][6].cell_type = HydroNetCellType.Barrier
    maze.cells[3][7].cell_type = HydroNetCellType.Barrier

    # Add finish point
    maze.cells[9][11].cell_type = HydroNetCellType.Finish

    # Set robot starting position
    maze.cells[0][0].is_robot_cell = True

    return maze


def generate_random_maze(width: int, height: int) -> HydroMaze:
    """
    Generate a random maze with random obstacles
    Генерирует случайный лабиринт с препятствиями
    """
    maze = HydroMaze(width=width, height=height)
    maze.InitializeMaze(HydroNetCellType.Water, width, height)

    # Add random barriers (about 15% of cells)
    barrier_count = int(width * height * 0.15)
    for _ in range(barrier_count):
        x = random.randint(1, width - 2)  # Exclude borders
        y = random.randint(1, height - 2)
        if not (x == 0 and y == 0):  # Don't place barrier at start
            maze.cells[y][x].cell_type = HydroNetCellType.Barrier

    # Add random shores (about 10% of cells)
    shore_count = int(width * height * 0.10)
    for _ in range(shore_count):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        if maze.cells[y][x].cell_type == HydroNetCellType.Water:
            maze.cells[y][x].cell_type = HydroNetCellType.Shore

    # Add finish point at random location
    finish_x = width - 1
    finish_y = height - 1
    maze.cells[finish_y][finish_x].cell_type = HydroNetCellType.Finish

    # Set robot starting position
    maze.cells[0][0].is_robot_cell = True

    return maze


def get_maze_size() -> tuple:
    """
    Get maze dimensions from user input
    Получить размеры лабиринта от пользователя
    """
    print("\nEnter maze dimensions:")
    while True:
        try:
            width = int(input("Width (min 5, max 30): "))
            height = int(input("Height (min 5, max 30): "))
            
            if 5 <= width <= 30 and 5 <= height <= 30:
                return width, height
            else:
                print("Invalid dimensions. Please enter values between 5 and 30.")
        except ValueError:
            print("Invalid input. Please enter numeric values.")


def get_maze_type() -> str:
    """
    Choose between sample or random maze
    Выбрать между примером и случайной картой
    """
    print("\nChoose maze type:")
    print("1 - Sample maze (predefined)")
    print("2 - Random maze (generated)")
    
    while True:
        choice = input("Select (1 or 2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("Invalid choice. Please enter 1 or 2.")


def main():
    """Main application entry point"""
    print("=" * 50)
    print("HydroRobot Path Animation")
    print("=" * 50)

    # Choose maze type
    maze_type = get_maze_type()

    if maze_type == '1':
        print("\nCreating sample maze...")
        maze = create_sample_maze()
    else:
        # Get dimensions for random maze
        width, height = get_maze_size()
        print(f"\nGenerating random maze {width}x{height}...")
        maze = generate_random_maze(width, height)

    # Create robot
    robot = HydroRobot(maze)

    print("Maze created successfully!")
    print(f"Maze size: {maze.width} x {maze.height}")
    print(f"Robot starting position: (0, 0)")
    print("\nControls:")
    print("  Play/Pause - Start or pause the animation")
    print("  Reset - Reset robot to start position")
    print("  Space - Toggle play/pause")
    print("  ESC - Exit")
    print("\n" + "=" * 50)
    print("Launching animation...")
    print("=" * 50 + "\n")

    # Launch the animation
    launch_animation(robot, maze)


if __name__ == "__main__":
    main()
