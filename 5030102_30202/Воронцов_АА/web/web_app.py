"""
HydroRobot Web Application
Flask server for web-based visualization
"""

from flask import Flask, render_template, jsonify, request
import json
from main import HydroRobot, HydroMaze, HydroNetCellType
import random

app = Flask(__name__)

# Global state
current_maze = None
current_robot = None
current_state = {
    "cells": [],
    "robot_x": 0,
    "robot_y": 0,
    "width": 0,
    "height": 0,
}


def create_random_maze(width: int, height: int) -> HydroMaze:
    """Generate a random maze"""
    maze = HydroMaze(width=width, height=height)
    maze.InitializeMaze(HydroNetCellType.Water, width, height)

    # Add random barriers (about 15% of cells)
    barrier_count = int(width * height * 0.15)
    for _ in range(barrier_count):
        x = random.randint(1, width - 2)
        y = random.randint(1, height - 2)
        if not (x == 0 and y == 0):
            maze.cells[y][x].cell_type = HydroNetCellType.Barrier

    # Add random shores (about 10% of cells)
    shore_count = int(width * height * 0.10)
    for _ in range(shore_count):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        if maze.cells[y][x].cell_type == HydroNetCellType.Water:
            maze.cells[y][x].cell_type = HydroNetCellType.Shore

    # Add finish point at top-right
    finish_x = width - 1
    finish_y = 0
    maze.cells[finish_y][finish_x].cell_type = HydroNetCellType.Finish

    # Set robot starting position at bottom-left
    maze.cells[height - 1][0].is_robot_cell = True

    return maze


def create_sample_maze() -> HydroMaze:
    """Create a sample maze"""
    maze = HydroMaze(width=12, height=10)
    maze.InitializeMaze(HydroNetCellType.Water, 12, 10)

    for x in range(2, 5):
        maze.cells[5][x].cell_type = HydroNetCellType.Shore

    maze.cells[3][6].cell_type = HydroNetCellType.Barrier
    maze.cells[3][7].cell_type = HydroNetCellType.Barrier

    maze.cells[0][11].cell_type = HydroNetCellType.Finish
    # Robot starts from bottom-left corner
    maze.cells[9][0].is_robot_cell = True

    return maze


def cell_type_to_string(cell_type: HydroNetCellType) -> str:
    """Convert cell type to string"""
    mapping = {
        HydroNetCellType.Water: "water",
        HydroNetCellType.Shore: "shore",
        HydroNetCellType.Sample: "sample",
        HydroNetCellType.Network: "network",
        HydroNetCellType.Barrier: "barrier",
        HydroNetCellType.Finish: "finish",
        HydroNetCellType.Channel: "channel",
    }
    return mapping.get(cell_type, "water")


def get_maze_state():
    """Get current maze state as JSON"""
    cells = []
    for y in range(current_maze.height):
        row = []
        for x in range(current_maze.width):
            cell = current_maze.cells[y][x]
            row.append({
                "type": cell_type_to_string(cell.cell_type),
                "is_robot": cell.is_robot_cell,
                "x": x,
                "y": y,
            })
        cells.append(row)

    return {
        "cells": cells,
        "robot_x": current_robot.current_cell.x if current_robot.current_cell else 0,
        "robot_y": current_robot.current_cell.y if current_robot.current_cell else 0,
        "width": current_maze.width,
        "height": current_maze.height,
    }


@app.route("/")
def index():
    """Main page"""
    return render_template("index.html")


@app.route("/api/create_maze", methods=["POST"])
def create_maze():
    """Create a new maze"""
    global current_maze, current_robot
    
    data = request.json
    maze_type = data.get("type", "sample")
    
    if maze_type == "sample":
        current_maze = create_sample_maze()
    else:
        width = data.get("width", 10)
        height = data.get("height", 10)
        current_maze = create_random_maze(width, height)
    
    current_robot = HydroRobot(current_maze)
    # The robot will automatically find its starting position from is_robot_cell flag
    
    # Return maze as 2D array of cell types (as integers)
    maze_array = []
    for row in current_maze.cells:
        maze_row = []
        for cell in row:
            maze_row.append(int(cell.cell_type.value))
        maze_array.append(maze_row)
    
    return jsonify({
        "maze": maze_array,
        "robot": {
            "x": 0,
            "y": 0
        },
        "width": current_maze.width,
        "height": current_maze.height
    })


@app.route("/api/maze_state")
def maze_state():
    """Get current maze state"""
    if current_maze is None:
        return jsonify({"error": "No maze created"}), 400
    return jsonify(get_maze_state())


@app.route("/api/get_iterator")
def get_iterator():
    """Get the path iterator for animation"""
    if current_maze is None:
        return jsonify({"error": "No maze created"}), 400
    
    path = []
    iterator = current_maze.GetIteratorFromBottomLeft()
    width = current_maze.width
    
    for cell in iterator:
        # Convert x,y to linear index
        index = cell.y * width + cell.x
        path.append(index)
    
    return jsonify({"iterator": path})


@app.route("/api/apply_transformation", methods=["POST"])
def apply_transformation():
    """Apply transformation to a cell"""
    if current_maze is None:
        return jsonify({"error": "No maze created"}), 400
    
    data = request.json
    x = data.get("x")
    y = data.get("y")
    
    cell = current_maze.cells[y][x]
    original_type = cell.cell_type
    
    transformations = []
    
    if cell.cell_type == HydroNetCellType.Water:
        cell.cell_type = HydroNetCellType.Sample
        transformations.append({
            "from": "water",
            "to": "sample",
            "message": "Water -> Sample"
        })
    elif cell.cell_type == HydroNetCellType.Shore:
        cell.cell_type = HydroNetCellType.Water
        transformations.append({
            "from": "shore",
            "to": "water",
            "message": "Shore -> Water"
        })
    
    return jsonify({
        "transformations": transformations,
        "cell_type": cell_type_to_string(cell.cell_type)
    })


@app.route("/api/move_robot", methods=["POST"])
def move_robot():
    """Move robot to next cell"""
    if current_robot is None or current_robot.current_cell is None:
        return jsonify({"error": "Robot not initialized"}), 400
    
    data = request.json
    next_x = data.get("next_x")
    next_y = data.get("next_y")
    
    if current_robot.current_cell:
        current_robot.current_cell.is_robot_cell = False
    
    current_robot._current_cell = current_maze.cells[next_y][next_x]
    current_robot.current_cell.is_robot_cell = True
    
    return jsonify(get_maze_state())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
