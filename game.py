#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Liinux 夺旗：终端迷宫小游戏，只使用 Python 标准库。"""

import curses
import sys

LEVELS = [
    [
        "#####################",
        "#@..$...............#",
        "#.####.############.#",
        "#.#..#.#..........#.#",
        "#.#.##.#.########.#.#",
        "#.#....#.#......#.#.#",
        "#.######.#.####.#.#.#",
        "#........#.#..#.#.#.#",
        "#.########.#.##.#.#.#",
        "#....$.......$....#E#",
        "#####################",
    ],
    [
        "#####################",
        "#@..#......$......#.#",
        "#.#.#.#########.#.#.#",
        "#.#.#.........#.#.#.#",
        "#.#.#########.#.#.#.#",
        "#.#.#....$....#...#.#",
        "#.#.#.#######.#####.#",
        "#.#.#.#.....#.....#.#",
        "#.#...#.###.#####.#.#",
        "#.#####.#$........#.#",
        "#.......#........E#.#",
        "#####################",
    ],
    [
        "#####################",
        "#@..$.....#........$#",
        "#.#.#####.#.#####.#.#",
        "#.#.#...#.#.....#.#.#",
        "#.#.#.#.#.#####.#.#.#",
        "#.#.#.#.#.....#.#.#.#",
        "#.#...#.#.###.#...#.#",
        "#.#####.#.#.#.#####.#",
        "#.....#.#.#.#.....$.#",
        "#.###.#.#.#.#####.#.#",
        "#...$.#...#.......E.#",
        "#####################",
    ],
]


def parse_level(rows):
    grid = [list(row) for row in rows]
    player = None
    coins = set()
    exit_pos = None
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == "@":
                player = (y, x)
                grid[y][x] = "."
            elif ch == "$":
                coins.add((y, x))
            elif ch == "E":
                exit_pos = (y, x)
                grid[y][x] = "."
    if player is None or exit_pos is None or not coins:
        raise ValueError("关卡缺少玩家、旗帜或金币")
    return grid, player, coins, exit_pos


def reachable(grid, start):
    height, width = len(grid), len(grid[0])
    seen = {start}
    stack = [start]
    while stack:
        y, x = stack.pop()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if not (0 <= ny < height and 0 <= nx < width):
                continue
            if grid[ny][nx] == "#" or (ny, nx) in seen:
                continue
            seen.add((ny, nx))
            stack.append((ny, nx))
    return seen


def self_test():
    for index, rows in enumerate(LEVELS, 1):
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise SystemExit(f"第 {index} 关宽度不一致")
        grid, player, coins, exit_pos = parse_level(rows)
        missing = (coins | {exit_pos}) - reachable(grid, player)
        if missing:
            raise SystemExit(f"第 {index} 关有格子走不到: {sorted(missing)}")
        print(f"第 {index} 关 OK  金币 {len(coins)}  尺寸 {width}x{len(rows)}")
    print("self-test passed")


class Game:
    def __init__(self):
        self.level_index = 0
        self.score = 0
        self.moves = 0
        self.message = "收集全部 $ ，再走到旗帜 E"
        self.grid = []
        self.player = (1, 1)
        self.coins = set()
        self.exit_pos = (1, 1)
        self.level_score = 0
        self.load_level(0)

    def load_level(self, index):
        self.level_index = index
        self.grid, self.player, self.coins, self.exit_pos = parse_level(LEVELS[index])
        self.level_score = 0
        total = len(self.coins)
        self.message = f"第 {index + 1} 关：拿到 {total} 枚金币后走向 E"

    def restart_level(self):
        self.score -= self.level_score
        self.load_level(self.level_index)
        self.message = "本关已重开"

    def try_move(self, dy, dx):
        y, x = self.player
        ny, nx = y + dy, x + dx
        if self.grid[ny][nx] == "#":
            self.message = "前面是墙"
            return "blocked"
        self.player = (ny, nx)
        self.moves += 1
        if (ny, nx) in self.coins:
            self.coins.remove((ny, nx))
            self.score += 10
            self.level_score += 10
            if self.coins:
                self.message = f"金币 +10，还剩 {len(self.coins)} 枚"
            else:
                self.message = "金币齐了，快去旗帜 E"
            return "coin"
        if (ny, nx) == self.exit_pos:
            if self.coins:
                self.message = f"旗帜还锁着，还差 {len(self.coins)} 枚金币"
                return "locked"
            self.score += 50
            self.level_score += 50
            if self.level_index + 1 >= len(LEVELS):
                self.message = "全部通关"
                return "win"
            self.load_level(self.level_index + 1)
            self.message = f"过关 +50，进入第 {self.level_index + 1} 关"
            return "next"
        self.message = "收集全部 $ ，再走到旗帜 E"
        return "move"


def load_best():
    try:
        with open("highscore.txt", encoding="utf-8") as handle:
            return int(handle.read().strip() or "0")
    except (OSError, ValueError):
        return 0


def save_best(score):
    best = load_best()
    if score > best:
        with open("highscore.txt", "w", encoding="utf-8") as handle:
            handle.write(str(score))
        return score
    return best


def init_colors():
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_GREEN, -1)
    curses.init_pair(6, curses.COLOR_WHITE, -1)


def put(stdscr, y, x, text, attr=0):
    height, width = stdscr.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    stdscr.addnstr(y, max(x, 0), text, max(0, width - max(x, 0) - 1), attr)


def draw_title(stdscr, best):
    stdscr.erase()
    lines = [
        "=============================",
        "        LIINUX 夺旗",
        "=============================",
        "",
        "  在迷宫里捡完金币 $",
        "  再走到旗帜 E 即可过关",
        "  一共 3 关",
        "",
        "  WASD 或方向键    移动",
        "  R                重开本关",
        "  Q                退出",
        "",
        f"  历史最高分：{best}",
        "",
        "  按任意键开始",
    ]
    for index, line in enumerate(lines):
        put(stdscr, index + 1, 2, line, curses.A_BOLD if index == 1 else 0)
    stdscr.refresh()


def draw_game(stdscr, game, best):
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    need_h = len(game.grid) + 6
    need_w = len(game.grid[0]) + 4
    if height < need_h or width < need_w:
        put(stdscr, 0, 0, f"终端太小，请至少拉到 {need_w}x{need_h}")
        stdscr.refresh()
        return
    title = (
        f" Liinux 夺旗   第 {game.level_index + 1}/{len(LEVELS)} 关"
        f"   分数 {game.score}   最高 {best}"
        f"   剩余金币 {len(game.coins)}   步数 {game.moves}"
    )
    put(stdscr, 0, 0, title, curses.A_BOLD)
    color = curses.has_colors()
    for y, row in enumerate(game.grid):
        for x, ch in enumerate(row):
            shown, attr = ch, curses.color_pair(6) if color else 0
            if ch == "#":
                attr = curses.color_pair(1) if color else 0
            if (y, x) in game.coins:
                shown = "$"
                attr = (curses.color_pair(3) | curses.A_BOLD) if color else curses.A_BOLD
            elif (y, x) == game.exit_pos:
                opened = not game.coins
                shown = "E"
                if color:
                    attr = curses.color_pair(5 if opened else 4) | curses.A_BOLD
                else:
                    attr = curses.A_BOLD
            if (y, x) == game.player:
                shown = "@"
                attr = (curses.color_pair(2) | curses.A_BOLD) if color else curses.A_BOLD
            try:
                stdscr.addch(y + 2, x + 2, shown, attr)
            except curses.error:
                pass
    put(stdscr, len(game.grid) + 3, 2, "移动: WASD / 方向键     R 重开本关     Q 退出")
    put(stdscr, len(game.grid) + 4, 2, game.message, curses.A_BOLD)
    stdscr.refresh()


def draw_end(stdscr, game, best, new_best):
    stdscr.erase()
    lines = [
        "=============================",
        "           通关",
        "=============================",
        "",
        f"  得分：{game.score}",
        f"  步数：{game.moves}",
        f"  最高分：{max(best, game.score)}",
        "  刷新纪录！" if new_best else "",
        "",
        "  Y 再玩一局     Q 退出",
    ]
    for index, line in enumerate(lines):
        if line:
            put(stdscr, index + 1, 2, line, curses.A_BOLD if index == 1 else 0)
    stdscr.refresh()


def play(stdscr):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.keypad(True)
    init_colors()
    best = load_best()
    draw_title(stdscr, best)
    stdscr.getch()

    while True:
        game = Game()
        won = False
        while not won:
            draw_game(stdscr, game, best)
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                return
            if key in (ord("r"), ord("R")):
                game.restart_level()
                continue
            delta = {
                curses.KEY_UP: (-1, 0),
                curses.KEY_DOWN: (1, 0),
                curses.KEY_LEFT: (0, -1),
                curses.KEY_RIGHT: (0, 1),
                ord("w"): (-1, 0),
                ord("W"): (-1, 0),
                ord("s"): (1, 0),
                ord("S"): (1, 0),
                ord("a"): (0, -1),
                ord("A"): (0, -1),
                ord("d"): (0, 1),
                ord("D"): (0, 1),
            }.get(key)
            if delta is None:
                continue
            if game.try_move(*delta) == "win":
                won = True
        new_best = game.score > best
        best = save_best(game.score)
        while True:
            draw_end(stdscr, game, best, new_best)
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                return
            if key in (ord("y"), ord("Y")):
                break


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        self_test()
        return
    if not sys.stdout.isatty():
        print("请在终端里运行：python3 game.py")
        return
    curses.wrapper(play)


if __name__ == "__main__":
    main()
