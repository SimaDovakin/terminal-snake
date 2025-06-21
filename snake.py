import random
import select
import sys
import termios
from time import sleep
import tty


DIRECTIONS = {
    "\x1b[A": (-1, 0),
    "\x1b[B": (1, 0),
    "\x1b[C": (0, 1),
    "\x1b[D": (0, -1),
}


def prepare_stdin() -> list:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    return old_settings


def set_stdin_old_settings(old_settings: list):
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)


def get_key(timeout: float = 0.1) -> str:
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)

    if not rlist:
        return ""

    key = sys.stdin.read(1)
    if key == "\x1b":
        key += sys.stdin.read(2)

    return key


def clean_screen():
    print("\x1b[2J", end="")


def move_cursor(line: int = 1, col: int = 1):
    print(f"\x1b[{line};{col}H", end="")


def hide_cursor():
    print("\x1b[?25l", end="")


def show_cursor():
    print("\x1b[?25h", end="")


def draw_borders(width: int, height: int):
    for line in (1, height):
        for col in range(1, width + 1):
            move_cursor(line, col)
            wall_char = "-"
            if (line, col) in {(1, 1), (1, width), (height, 1), (height, width)}:
                wall_char = "+"

            print(wall_char, end="")

    for line in range(2, height):
        for col in (1, width):
            move_cursor(line, col)
            print("|", end="")


def draw_cursor(dline: int, dcol: int):
    cursor = ""
    if dline == 1:
        cursor = "v"
    elif dline == -1:
        cursor = "^"
    elif dcol == 1:
        cursor = ">"
    elif dcol == -1:
        cursor = "<"

    print(f"\x1b[33m{cursor}\x1b[0m", end="")


def is_position_valid(
    position: tuple[int, int], horizontal_range: range, vertical_range: range
) -> bool:
    line, col = position
    return line in vertical_range and col in horizontal_range


def move_snake(
    snake: list[tuple[int, int, int, int]],
    food_position: tuple[int, int],
    horizontal_range: range,
    vertical_range: range,
) -> tuple[list[tuple[int, int, int, int]], bool]:
    moved_snake: list[tuple[int, int, int, int]] = []

    head_line, head_col, head_dline, head_dcol = snake[0]
    moved_head = (head_line + head_dline, head_col + head_dcol, head_dline, head_dcol)
    moved_head_line, moved_head_col, previous_dline, previous_dcol = moved_head

    if not is_position_valid(
        (moved_head_line, moved_head_col), horizontal_range, vertical_range
    ):
        return snake, True

    for cell_line, cell_col, *_ in snake:
        if (moved_head_line, moved_head_col) == (cell_line, cell_col):
            return snake, True

    moved_snake.append(moved_head)

    for cell_line, cell_col, cell_dline, cell_dcol in snake[1:]:
        moved_cell_line, moved_cell_col = cell_line + cell_dline, cell_col + cell_dcol
        moved_snake.append(
            (moved_cell_line, moved_cell_col, previous_dline, previous_dcol)
        )
        previous_dline, previous_dcol = cell_dline, cell_dcol

    if (moved_head_line, moved_head_col) == food_position:
        moved_snake.append(snake[-1])

    return moved_snake, False


def turn_snake(snake: list[tuple[int, int, int, int]], direction: tuple[int, int]):
    dline, dcol = direction
    opposite_direction = (-dline, -dcol)
    head_line, head_col, head_dline, head_dcol = snake[0]

    if opposite_direction == (head_dline, head_dcol):
        return

    snake[0] = (head_line, head_col, dline, dcol)


def draw_snake(snake: list[tuple[int, int, int, int]]):
    for cell_line, cell_col, *_ in snake:
        move_cursor(cell_line, cell_col)
        print("\x1b[32m#\x1b[0m", end="")


def draw_food(position: tuple[int, int]):
    line, col = position
    move_cursor(line, col)
    print("\x1b[31m@\x1b[0m", end="")


def init_snake() -> list[tuple[int, int, int, int]]:
    return [
        (15, 25, 0, 1),
        (15, 24, 0, 1),
        (15, 23, 0, 1),
    ]


def get_free_cells(
    snake: list[tuple[int, int, int, int]],
    horizontal_range: range,
    vertical_range: range,
) -> set[tuple[int, int]]:
    snake_cells = {(line, col) for line, col, _, _ in snake}
    return {
        (line, col)
        for line in vertical_range
        for col in horizontal_range
        if (line, col) not in snake_cells
    }


def choose_food_position(free_cells: set[tuple[int, int]]) -> tuple[int, int]:
    return random.choice(list(free_cells))


def update_scores(score: int, highest_score: int) -> tuple[int, int]:
    score += 1
    if score > highest_score:
        highest_score = score
    return score, highest_score


def show_scores(score: int, highest_score: int, line: int, col: int):
    move_cursor(line, col)
    print("Score:", end="")
    move_cursor(line + 1, col)
    print(score, end="")
    move_cursor(line + 2, col)
    print("Highest Score:", end="")
    move_cursor(line + 3, col)
    print(highest_score, end="")


def show_keyboard_controls(line: int, col: int):
    move_cursor(line, col)
    print("Keyboard controls:", end="")
    move_cursor(line + 1, col)
    print("Arrow keys - Move", end="")
    move_cursor(line + 2, col)
    print("P - Pause", end="")
    move_cursor(line + 3, col)
    print("R - Resume", end="")


def main():
    score, highest_score = 0, 0
    width, height = 50, 30
    is_pause = False
    is_game_over = False
    horizontal_range, vertical_range = range(2, width), range(2, height)
    timeout = 0.2
    snake = init_snake()
    free_cells = get_free_cells(snake, horizontal_range, vertical_range)
    food_position = choose_food_position(free_cells)

    old_settings = prepare_stdin()

    hide_cursor()
    try:
        while True:
            clean_screen()
            draw_borders(width, height)
            show_scores(score, highest_score, 1, width + 2)
            show_keyboard_controls(6, width + 2)

            draw_food(food_position)
            draw_snake(snake)

            if is_pause:
                move_cursor(height // 2, width // 2 - 2)
                print("\x1b[33mPause\x1b[0m", end="")
                move_cursor(height // 2 + 1, width // 2 - 8)
                print("\x1b[33mPress R to resume\x1b[0m", end="")

            if is_game_over:
                move_cursor(height // 2, width // 2 - 5)
                print("\x1b[31mGame Over!\x1b[0m", end="")
                move_cursor(height // 2 + 1, width // 2 - 8)
                print("\x1b[31mPress R to resume\x1b[0m", end="")

            sys.stdout.flush()

            key = get_key(0.0)
            if key == "q":
                break
            elif key == "p" and not is_pause:
                is_pause = True
            elif key == "r" and is_pause:
                is_pause = False
            elif key == "r" and is_game_over:
                score = 0
                snake = init_snake()
                free_cells = get_free_cells(snake, horizontal_range, vertical_range)
                food_position = choose_food_position(free_cells)
                is_game_over = False
                continue
            elif key in DIRECTIONS:
                turn_snake(snake, DIRECTIONS[key])

            if is_pause:
                sleep(timeout)
                continue

            if is_game_over:
                sleep(timeout)
                continue

            last_cell_line, last_cell_col, *_ = snake[-1]
            snake, is_reach_obstacle = move_snake(
                snake, food_position, horizontal_range, vertical_range
            )

            if is_reach_obstacle:
                is_game_over = True
                continue

            free_cells.remove((snake[0][0], snake[0][1]))
            if (snake[0][0], snake[0][1]) == food_position:
                score, highest_score = update_scores(score, highest_score)
                food_position = choose_food_position(free_cells)
            else:
                free_cells.add((last_cell_line, last_cell_col))

            sleep(timeout)

    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        move_cursor(height + 1, 1)
        set_stdin_old_settings(old_settings)


if __name__ == "__main__":
    main()
