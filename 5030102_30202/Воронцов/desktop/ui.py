import pygame
import sys
from typing import Optional, Tuple, List
from main import (
    HydroRobot,
    HydroMaze,
    HydroNetCellType,
    HydroCell,
)


# Colors
COLOR_WATER = (70, 130, 180)  # Steel blue
COLOR_SHORE = (210, 180, 140)  # Tan
COLOR_SAMPLE = (255, 140, 0)  # Dark orange
COLOR_NETWORK = (34, 139, 34)  # Forest green
COLOR_BARRIER = (139, 69, 19)  # Saddle brown
COLOR_FINISH = (50, 205, 50)  # Lime green
COLOR_CHANNEL = (0, 0, 0)  # Black
COLOR_BACKGROUND = (240, 240, 240)  # Light gray
COLOR_GRID = (180, 180, 180)  # Medium gray
COLOR_ROBOT = (255, 0, 0)  # Red
COLOR_VISITED = (173, 216, 230)  # Light blue
COLOR_TEXT = (0, 0, 0)  # Black
COLOR_BUTTON = (100, 149, 237)  # Cornflower blue
COLOR_BUTTON_HOVER = (65, 105, 225)  # Royal blue

# Cell type to color mapping
CELL_TYPE_COLORS = {
    HydroNetCellType.Water: COLOR_WATER,
    HydroNetCellType.Shore: COLOR_SHORE,
    HydroNetCellType.Sample: COLOR_SAMPLE,
    HydroNetCellType.Network: COLOR_NETWORK,
    HydroNetCellType.Barrier: COLOR_BARRIER,
    HydroNetCellType.Finish: COLOR_FINISH,
    HydroNetCellType.Channel: COLOR_CHANNEL,
}


class ControlButton:
    def __init__(
        self, x: int, y: int, width: int, height: int, text: str, action=None
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.is_hovered = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        color = COLOR_BUTTON_HOVER if self.is_hovered else COLOR_BUTTON

        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, COLOR_TEXT, self.rect, 2)

        text_surface = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def update(self, mouse_pos: Tuple[int, int]):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_click(self) -> bool:
        if self.is_hovered and self.action:
            self.action()
            return True
        return False


class HydroRobotAnimation:
    def __init__(
        self,
        robot: HydroRobot,
        maze: HydroMaze,
        cell_size: int = 50,
        margin: int = 50,
    ):
        pygame.init()

        self.robot = robot
        self.maze = maze
        self.cell_size = cell_size
        self.margin = margin

        # Calculate window size
        self.width = maze.width * cell_size + 2 * margin + 200
        self.height = maze.height * cell_size + 2 * margin + 100

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("HydroRobot Path Animation")

        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)

        self.clock = pygame.time.Clock()
        self.fps = 60

        # Animation parameters
        self.animation_speed = 0.5  # seconds per cell
        self.move_elapsed_time = 0
        self.is_moving = False
        self.move_start_pos = None
        self.move_end_pos = None

        # Animation state
        self.path_iterator = None
        self.visited_cells = set()
        self.current_step = 0
        self.total_steps = 0
        self.cell_transformations = {}  # Track what each visited cell transformed to
        
        # Multi-step transformation state
        self.current_cell_transformations = []  # Queue of transformations for current cell
        self.transformation_index = 0  # Which transformation we're on
        self.transformation_delay = 0.3  # seconds to wait between transformations
        self.transformation_timer = 0  # timer for current transformation
        self.is_transforming = False  # True when we're transforming, False when moving

        # Control state
        self.is_playing = False
        self.is_paused = False
        self.is_finished = False
        self.current_message = ""
        self.message_time = 0
        self.message_duration = 2000  # ms

        # Buttons
        self.buttons = self._create_buttons()

        self.is_running = True

    def _create_buttons(self) -> List[ControlButton]:
        maze_area_width = self.maze.width * self.cell_size + 2 * self.margin
        button_x = maze_area_width + 20
        button_y = self.margin + 50
        button_width = 180
        button_height = 40
        button_spacing = 50

        buttons = [
            ControlButton(
                button_x, button_y, button_width, button_height, "Play", self.play
            ),
            ControlButton(
                button_x,
                button_y + button_spacing,
                button_width,
                button_height,
                "Pause",
                self.pause,
            ),
            ControlButton(
                button_x,
                button_y + button_spacing * 2,
                button_width,
                button_height,
                "Reset",
                self.reset,
            ),
        ]

        return buttons

    def _init_animation(self):
        """Initialize the animation by getting the path iterator"""
        self.path_iterator = self.maze.GetIterator()
        self.visited_cells = set()
        self.current_step = 0
        self.transformation_index = 0
        self.transformation_timer = 0

        # Count total reachable cells (avoiding barriers and channels)
        temp_iterator = self.maze.GetIterator()
        self.total_steps = sum(1 for _ in temp_iterator)

        # Get first cell
        if self.robot.current_cell:
            self.visited_cells.add(
                (self.robot.current_cell.x, self.robot.current_cell.y)
            )
            self.current_step = 1

    def play(self):
        if not self.is_playing:
            if self.is_finished:
                self.reset()
            if self.path_iterator is None:
                self._init_animation()
            self.is_playing = True
            self.is_paused = False

    def pause(self):
        self.is_playing = False
        self.is_paused = True

    def reset(self):
        # Reset robot to start position
        for row in self.maze.cells:
            for cell in row:
                cell.is_robot_cell = False
        self.maze.cells[0][0].is_robot_cell = True

        self.robot._current_cell = None
        self.path_iterator = None
        self.visited_cells = set()
        self.cell_transformations = {}
        self.current_cell_transformations = []
        self.transformation_index = 0
        self.transformation_timer = 0
        self.is_transforming = False
        self.current_step = 0
        self.is_playing = False
        self.is_paused = False
        self.is_finished = False
        self.is_moving = False
        self.current_message = ""

    def _get_cell_screen_pos(self, x: int, y: int) -> Tuple[int, int]:
        """Convert maze coordinates to screen coordinates"""
        screen_x = self.margin + x * self.cell_size
        screen_y = self.margin + (self.maze.height - 1 - y) * self.cell_size
        return screen_x, screen_y

    def _move_to_next_cell(self):
        """Move robot to the next cell in the path"""
        if self.path_iterator is None:
            return

        try:
            next_cell = next(self.path_iterator)

            self.move_start_pos = (
                self.robot.current_cell.x,
                self.robot.current_cell.y,
            )
            self.robot._current_cell = next_cell
            self.move_end_pos = (next_cell.x, next_cell.y)

            cell_coords = (next_cell.x, next_cell.y)
            self.visited_cells.add(cell_coords)
            
            # Just move to the cell, don't transform yet
            self.is_moving = True
            self.is_transforming = False
            self.move_elapsed_time = 0

        except StopIteration:
            self.is_playing = False
            self.is_finished = True
            self.current_message = "Animation finished! All cells processed!"
            self.message_time = pygame.time.get_ticks()

    def _start_transformations(self):
        """Start transformations on current cell after movement"""
        if not self.robot.current_cell:
            return
        
        # Determine transformations needed for this cell
        self.current_cell_transformations = []
        
        if self.robot.current_cell.cell_type == HydroNetCellType.Water:
            # Water needs 1 transformation: Water -> Sample
            self.current_cell_transformations = [
                (HydroNetCellType.Sample, "Water -> Sample")
            ]
        elif self.robot.current_cell.cell_type == HydroNetCellType.Shore:
            # Shore needs 2 transformations: Shore -> Water -> Sample
            self.current_cell_transformations = [
                (HydroNetCellType.Water, "Shore -> Water"),
                (HydroNetCellType.Sample, "Water -> Sample")
            ]
        
        self.transformation_index = 0
        self.transformation_timer = 0
        self.is_transforming = True

    def _apply_transformations(self, dt: float):
        """Apply transformations to current cell"""
        if not self.is_transforming or not self.current_cell_transformations:
            return

        self.transformation_timer += dt

        # Check if it's time to apply next transformation
        if self.transformation_timer >= self.transformation_delay:
            if self.transformation_index < len(self.current_cell_transformations):
                target_type, message = self.current_cell_transformations[self.transformation_index]
                
                # Apply transformation
                if self.robot.current_cell:
                    self.robot.current_cell.cell_type = target_type
                    cell_coords = (self.robot.current_cell.x, self.robot.current_cell.y)
                    self.cell_transformations[cell_coords] = target_type
                    self.current_message = f"{message} at ({self.robot.current_cell.x}, {self.robot.current_cell.y})"
                    self.message_time = pygame.time.get_ticks()
                
                self.transformation_index += 1
                self.transformation_timer = 0
            else:
                # All transformations done for this cell
                self.is_transforming = False
                self.current_cell_transformations = []

    def _draw_maze(self):
        # Draw grid background
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                cell = self.maze.cells[y][x]
                screen_x, screen_y = self._get_cell_screen_pos(x, y)

                # Determine color based on transformation
                cell_coords = (x, y)
                if cell_coords in self.cell_transformations:
                    # Show the transformed cell type
                    transformed_type = self.cell_transformations[cell_coords]
                    color = CELL_TYPE_COLORS.get(transformed_type, COLOR_WATER)
                else:
                    # Show original cell type
                    color = CELL_TYPE_COLORS.get(cell.cell_type, COLOR_WATER)

                pygame.draw.rect(
                    self.screen, color, (screen_x, screen_y, self.cell_size, self.cell_size)
                )
                pygame.draw.rect(
                    self.screen,
                    COLOR_GRID,
                    (screen_x, screen_y, self.cell_size, self.cell_size),
                    1,
                )

    def _draw_robot(self):
        if self.robot.current_cell is None:
            return

        if self.is_moving and self.move_start_pos and self.move_end_pos:
            # Animate robot movement
            progress = min(
                1.0,
                self.move_elapsed_time / (self.animation_speed * 1000),
            )

            start_screen = self._get_cell_screen_pos(
                self.move_start_pos[0], self.move_start_pos[1]
            )
            end_screen = self._get_cell_screen_pos(
                self.move_end_pos[0], self.move_end_pos[1]
            )

            robot_x = start_screen[0] + (end_screen[0] - start_screen[0]) * progress
            robot_y = start_screen[1] + (end_screen[1] - start_screen[1]) * progress

            if progress >= 1.0:
                self.is_moving = False
        else:
            x, y = self.robot.current_cell.x, self.robot.current_cell.y
            robot_x, robot_y = self._get_cell_screen_pos(x, y)

        # Draw robot as circle in the center of cell
        center_x = int(robot_x + self.cell_size // 2)
        center_y = int(robot_y + self.cell_size // 2)
        radius = self.cell_size // 3

        pygame.draw.circle(self.screen, COLOR_ROBOT, (center_x, center_y), radius)
        pygame.draw.circle(
            self.screen, COLOR_TEXT, (center_x, center_y), radius, 2
        )

    def _draw_ui(self):
        # Draw title
        title = self.font_large.render("HydroRobot Path Animation", True, COLOR_TEXT)
        self.screen.blit(title, (self.margin, 10))

        # Draw maze info
        maze_area_width = self.maze.width * self.cell_size + 2 * self.margin
        info_x = maze_area_width + 20
        info_y = self.margin + 200

        if self.robot.current_cell:
            pos_text = self.font_small.render(
                f"Position: ({self.robot.current_cell.x}, {self.robot.current_cell.y})",
                True,
                COLOR_TEXT,
            )
            step_text = self.font_small.render(
                f"Step: {self.current_step} / {self.total_steps}",
                True,
                COLOR_TEXT,
            )
            cell_type_text = self.font_small.render(
                f"Cell Type: {self.robot.current_cell.cell_type.name}",
                True,
                COLOR_TEXT,
            )

            self.screen.blit(pos_text, (info_x, info_y))
            self.screen.blit(step_text, (info_x, info_y + 25))
            self.screen.blit(cell_type_text, (info_x, info_y + 50))

        # Draw status
        status_y = info_y + 100
        if self.is_playing:
            status = "Status: Playing"
        elif self.is_paused:
            status = "Status: Paused"
        elif self.is_finished:
            status = "Status: Finished"
        else:
            status = "Status: Stopped"

        status_text = self.font_small.render(status, True, COLOR_TEXT)
        self.screen.blit(status_text, (info_x, status_y))

        # Draw message
        if self.current_message:
            elapsed = pygame.time.get_ticks() - self.message_time
            if elapsed < self.message_duration:
                msg_text = self.font_medium.render(
                    self.current_message, True, COLOR_TEXT
                )
                self.screen.blit(msg_text, (info_x, status_y + 50))

    def _draw_controls(self):
        for button in self.buttons:
            button.draw(self.screen, self.font_small)

    def _draw_legend(self):
        maze_area_width = self.maze.width * self.cell_size + 2 * self.margin
        legend_x = maze_area_width + 20
        legend_y = self.height - 120

        legend_title = self.font_medium.render("Legend:", True, COLOR_TEXT)
        self.screen.blit(legend_title, (legend_x, legend_y))

        cell_types = [
            (HydroNetCellType.Water, "Water"),
            (HydroNetCellType.Shore, "Shore"),
            (HydroNetCellType.Sample, "Sample"),
        ]

        for i, (cell_type, name) in enumerate(cell_types):
            color = CELL_TYPE_COLORS[cell_type]
            y_pos = legend_y + 30 + i * 18

            pygame.draw.rect(self.screen, color, (legend_x, y_pos, 15, 15))
            pygame.draw.rect(self.screen, COLOR_TEXT, (legend_x, y_pos, 15, 15), 1)

            text = self.font_small.render(name, True, COLOR_TEXT)
            self.screen.blit(text, (legend_x + 20, y_pos))

        # Visited cell legend
        pygame.draw.rect(self.screen, COLOR_VISITED, (legend_x, legend_y + 84, 15, 15))
        pygame.draw.rect(self.screen, COLOR_TEXT, (legend_x, legend_y + 84, 15, 15), 1)
        text = self.font_small.render("Visited", True, COLOR_TEXT)
        self.screen.blit(text, (legend_x + 20, legend_y + 84))

    def _handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False
                elif event.key == pygame.K_SPACE:
                    if self.is_playing:
                        self.pause()
                    else:
                        self.play()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                for button in self.buttons:
                    button.handle_click()

        # Update button hover states
        for button in self.buttons:
            button.update(mouse_pos)

    def _update(self, dt: float):
        if self.is_playing:
            if self.is_moving:
                # Update movement animation
                self.move_elapsed_time += dt * 1000
                # Check if movement is complete
                if self.move_elapsed_time >= (self.animation_speed * 1000):
                    self.is_moving = False
                    self.move_elapsed_time = 0
                    # Now start transformations
                    self._start_transformations()
            elif self.is_transforming:
                # Apply transformations
                self._apply_transformations(dt)
            else:
                # No more transformations, move to next cell
                self.current_step += 1
                self._move_to_next_cell()

    def run(self):
        while self.is_running:
            dt = self.clock.tick(self.fps) / 1000.0

            self._handle_events()
            self._update(dt)

            # Draw everything
            self.screen.fill(COLOR_BACKGROUND)

            self._draw_maze()
            self._draw_robot()
            self._draw_ui()
            self._draw_controls()
            self._draw_legend()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


def launch_animation(robot: HydroRobot, maze: HydroMaze):
    """Launch the HydroRobot animation"""
    animation = HydroRobotAnimation(robot, maze)
    animation.run()


if __name__ == "__main__":
    from main import HydroRobot, HydroMaze, HydroNetCellType

    # Create a maze
    maze = HydroMaze(width=10, height=10)
    maze.InitializeMaze(HydroNetCellType.Water, 10, 10)

    # Set robot starting position
    maze.cells[0][0].is_robot_cell = True

    # Create robot
    robot = HydroRobot(maze)

    # Launch animation
    launch_animation(robot, maze)
