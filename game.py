#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Liinux 地牢：终端回合制地牢，只使用 Python 标准库。"""

import curses
import sys

FLOORS = [
    [
        "#####################",
        "#@....#.............#",
        "#.....####.#####....#",
        "#.k...#.....p.#.....#",
        "#.....#..........g..#",
        "#.............#.....#",
        "#.....#...###########",
        "#.....#.............#",
        "#...g...............#",
        "#.....#.......D....>#",
        "#####################",
    ],
    [
        "#####################",
        "#@..#...p...#.......#",
        "#...#...........k...#",
        "#........g..#.......#",
        "#...####.####.......#",
        "#...#.......#...G...#",
        "#...........#.......#",
        "#...#.......####.####",
        "#...........#.......#",
        "#...........#..D...>#",
        "#####################",
    ],
    [
        "#####################",
        "#@........#.........#",
        "#..p......#.........#",
        "#.........#.........#",
        "#####.###############",
        "#.........#.........#",
        "#.g.......#......g..#",
        "#...................#",
        "#.....k...#...G.....#",
        "#.........#.....D..>#",
        "#####################",
    ],
]

ENEMIES = {
    "g": {"name": "哥布林", "hp": 8, "atk": 2, "score": 15},
    "G": {"name": "守卫", "hp": 14, "atk": 4, "score": 40},
}


def parse_floor(rows):
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("地图宽度不一致")
    grid = [list(row) for row in rows]
    player = None
    stairs = None
    enemies = []
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == "@":
                player = (y, x)
                grid[y][x] = "."
            elif ch == ">":
                stairs = (y, x)
                grid[y][x] = "."
            elif ch in ENEMIES:
                spec = ENEMIES[ch]
                enemies.append({
                    "y": y, "x": x, "kind": ch,
                    "name": spec["name"], "hp": spec["hp"],
                    "max": spec["hp"], "atk": spec["atk"], "score": spec["score"],
                })
                grid[y][x] = "."
    if player is None or stairs is None:
        raise ValueError("地图缺少玩家或楼梯")
    return grid, player, stairs, enemies


def los(grid, start, end):
    y0, x0 = start
    y1, x1 = end
    dy, dx = abs(y1 - y0), abs(x1 - x0)
    sy = 1 if y0 < y1 else -1
    sx = 1 if x0 < x1 else -1
    err = dx - dy
    y, x = y0, x0
    while (y, x) != (y1, x1):
        if (y, x) != start and grid[y][x] in ("#", "D"):
            return False
        doubled = 2 * err
        if doubled > -dy:
            err -= dy
            x += sx
        if doubled < dx:
            err += dx
            y += sy
    return True


def visible_cells(grid, origin, radius=5):
    height, width = len(grid), len(grid[0])
    found = {origin}
    y0, x0 = origin
    for y in range(max(0, y0 - radius), min(height, y0 + radius + 1)):
        for x in range(max(0, x0 - radius), min(width, x0 + radius + 1)):
            if max(abs(y - y0), abs(x - x0)) > radius:
                continue
            if los(grid, origin, (y, x)):
                found.add((y, x))
    return found


class Dungeon:
    def __init__(self):
        self.floor_index = 0
        self.hp = 26
        self.max_hp = 26
        self.atk = 5
        self.keys = 0
        self.potions = 0
        self.score = 0
        self.moves = 0
        self.message = "找钥匙 k，开门 D，下楼 >"
        self.log = []
        self.grid = []
        self.player = (1, 1)
        self.stairs = (1, 1)
        self.enemies = []
        self.seen = set()
        self.load_floor(0)

    def note(self, text):
        self.message = text
        self.log.append(text)
        self.log = self.log[-4:]

    def load_floor(self, index):
        self.floor_index = index
        self.grid, self.player, self.stairs, self.enemies = parse_floor(FLOORS[index])
        self.seen = set()
        self.look()
        self.note(f"进入第 {index + 1} 层")

    def look(self):
        self.seen |= visible_cells(self.grid, self.player)

    def enemy_at(self, y, x):
        for enemy in self.enemies:
            if enemy["hp"] > 0 and enemy["y"] == y and enemy["x"] == x:
                return enemy
        return None

    def living(self):
        return [enemy for enemy in self.enemies if enemy["hp"] > 0]

    def occupied(self, y, x, ignore=None):
        if (y, x) == self.player:
            return True
        for enemy in self.living():
            if enemy is ignore:
                continue
            if enemy["y"] == y and enemy["x"] == x:
                return True
        return False

    def pickup(self, y, x):
        tile = self.grid[y][x]
        if tile == "k":
            self.keys += 1
            self.grid[y][x] = "."
            self.note(f"捡到钥匙，现在有 {self.keys} 把")
        elif tile == "p":
            self.potions += 1
            self.grid[y][x] = "."
            self.note(f"捡到药水，按 F 喝。库存 {self.potions}")

    def strike(self, enemy):
        enemy["hp"] -= self.atk
        if enemy["hp"] <= 0:
            self.score += enemy["score"]
            self.note(f"打败了{enemy['name']}，+{enemy['score']}")
            return
        self.note(f"击中{enemy['name']}，它还剩 {enemy['hp']} 血")

    def drink(self):
        if self.potions <= 0:
            self.note("没有药水")
            return "empty"
        self.potions -= 1
        healed = min(10, self.max_hp - self.hp)
        self.hp += healed
        self.note(f"喝药 +{healed}，生命 {self.hp}/{self.max_hp}")
        return "drink"

    def try_move(self, dy, dx):
        y, x = self.player
        ny, nx = y + dy, x + dx
        tile = self.grid[ny][nx]
        if tile == "#":
            self.note("前面是墙")
            return "blocked"
        enemy = self.enemy_at(ny, nx)
        if enemy:
            self.strike(enemy)
            return "hit"
        if tile == "D":
            if self.keys <= 0:
                self.note("门锁着，需要钥匙 k")
                return "locked"
            self.keys -= 1
            self.grid[ny][nx] = "."
            self.player = (ny, nx)
            self.note("用钥匙开了门")
            return "door"
        self.player = (ny, nx)
        self.pickup(ny, nx)
        if (ny, nx) == self.stairs and self.grid[ny][nx] == ".":
            if self.floor_index + 1 >= len(FLOORS):
                self.score += 80 + self.hp
                self.note("逃出地牢")
                return "win"
            self.score += 30
            self.hp = min(self.max_hp, self.hp + 4)
            self.load_floor(self.floor_index + 1)
            return "next"
        if self.message.startswith("捡到") or self.message.startswith("用钥匙"):
            return "item"
        self.note("继续探索")
        return "move"

    def enemy_step(self, enemy):
        if enemy["hp"] <= 0:
            return
        y, x = enemy["y"], enemy["x"]
        py, px = self.player
        if abs(py - y) + abs(px - x) == 1:
            self.hp = max(0, self.hp - enemy["atk"])
            self.note(f"{enemy['name']}打中你，-{enemy['atk']}，生命 {max(self.hp, 0)}")
            return
        seen = visible_cells(self.grid, (y, x), radius=6)
        if (py, px) not in seen:
            return
        options = []
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if self.grid[ny][nx] in ("#", "D"):
                continue
            if self.occupied(ny, nx, ignore=enemy):
                continue
            options.append((abs(ny - py) + abs(nx - px), ny, nx))
        if not options:
            return
        options.sort()
        if options[0][0] >= abs(y - py) + abs(x - px):
            return
        enemy["y"], enemy["x"] = options[0][1], options[0][2]

    def enemies_act(self):
        for enemy in self.living():
            self.enemy_step(enemy)
            if self.hp <= 0:
                self.note("你倒下了")
                return "dead"
        return "ok"

    def act(self, command):
        if command == "f":
            result = self.drink()
        elif command == ".":
            self.note("原地等待")
            result = "wait"
        elif command in "wasd":
            delta = {"w": (-1, 0), "s": (1, 0), "a": (0, -1), "d": (0, 1)}[command]
            result = self.try_move(*delta)
        else:
            return "ignored"
        self.moves += 1
        if result == "win":
            return "win"
        if result != "next":
            self.look()
        if result == "win":
            return "win"
        if self.enemies_act() == "dead" or self.hp <= 0:
            return "dead"
        self.look()
        return result


def reachable(grid):
    """通用钥匙。没钥匙不能过门。检查不靠怪物也能走到楼梯。"""
    height, width = len(grid), len(grid[0])
    keys, doors = [], []
    start = None
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == "@":
                start = (y, x)
            elif ch == "k":
                keys.append((y, x))
            elif ch == "D":
                doors.append((y, x))
    key_index = {pos: bit for bit, pos in enumerate(keys)}
    door_index = {pos: bit for bit, pos in enumerate(doors)}
    seen = {(start, 0, 0)}
    stack = [(start, 0, 0)]
    while stack:
        (y, x), keys_mask, open_mask = stack.pop()
        if grid[y][x] == ">":
            return True
        held = bin(keys_mask).count("1")
        spent = bin(open_mask).count("1")
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if not (0 <= ny < height and 0 <= nx < width):
                continue
            tile = grid[ny][nx]
            if tile == "#":
                continue
            new_keys, new_open = keys_mask, open_mask
            if tile == "D" and not (open_mask & (1 << door_index[(ny, nx)])):
                if held - spent <= 0:
                    continue
                new_open |= 1 << door_index[(ny, nx)]
            if tile == "k":
                new_keys |= 1 << key_index[(ny, nx)]
            state = ((ny, nx), new_keys, new_open)
            if state not in seen:
                seen.add(state)
                stack.append(state)
    return False


def self_test():
    for index, rows in enumerate(FLOORS, 1):
        width = len(rows[0])
        if any(len(row) != width for row in rows):
            raise SystemExit(f"第 {index} 层宽度不一致")
        grid, player, stairs, enemies = parse_floor(rows)
        raw = [list(row) for row in rows]
        if not reachable(raw):
            raise SystemExit(f"第 {index} 层楼梯走不到")
        print(
            f"第 {index} 层 OK  尺寸 {width}x{len(rows)}"
            f"  敌人 {len(enemies)}  起点 {player}  楼梯 {stairs}"
        )
    fight = Dungeon()
    fight.player = (1, 1)
    fight.enemies = [{
        "y": 1, "x": 2, "kind": "g", "name": "哥布林",
        "hp": 8, "max": 8, "atk": 3, "score": 15,
    }]
    fight.grid = [list("###"), list("#.."), list("###")]
    fight.grid[1][1] = "."
    before = fight.score
    fight.act("d")
    if fight.enemies[0]["hp"] >= 8 or fight.score <= before and fight.enemies[0]["hp"] > 0:
        # 一击至少掉血
        if fight.enemies[0]["hp"] != 3 and fight.enemies[0]["hp"] > 0:
            raise SystemExit(f"攻击伤害不对: {fight.enemies[0]['hp']}")
    door = Dungeon()
    door.keys = 0
    door.grid = [list(row) for row in ("#####", "#@D.>", "#####")]
    door.player = (1, 1)
    door.stairs = (1, 4)
    door.enemies = []
    door.grid[1][1] = "."
    if door.act("d") != "locked":
        raise SystemExit("没钥匙不该开门")
    door.keys = 1
    door.player = (1, 1)
    opened = door.act("d")
    if door.grid[1][2] == "D" or door.keys != 0:
        raise SystemExit(f"开门失败 {opened} keys={door.keys}")
    potion = Dungeon()
    potion.hp = 10
    potion.potions = 1
    potion.act("f")
    if potion.hp != 20 or potion.potions != 0:
        raise SystemExit(f"喝药失败 hp={potion.hp} n={potion.potions}")
    print("self-test passed")


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
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)
    curses.init_pair(5, curses.COLOR_YELLOW, -1)
    curses.init_pair(6, curses.COLOR_WHITE, -1)
    curses.init_pair(7, curses.COLOR_MAGENTA, -1)
    curses.init_pair(8, curses.COLOR_BLUE, -1)


def put(stdscr, y, x, text, attr=0):
    height, width = stdscr.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    stdscr.addnstr(y, max(x, 0), text, max(0, width - max(x, 0) - 1), attr)


def draw_title(stdscr, best):
    stdscr.erase()
    lines = [
        "=============================",
        "         LIINUX 地牢",
        "=============================",
        "",
        "  三层地牢。打败怪物，找钥匙开门，",
        "  走到楼梯 > 下楼。第三层的楼梯是出口。",
        "",
        "  g 哥布林    G 守卫",
        "  k 钥匙      D 门      p 药水",
        "",
        "  WASD / 方向键    移动，撞上怪物即攻击",
        "  F                喝药水（+10）",
        "  .                等待一回合",
        "  R                重开    Q 退出",
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
    need_h = len(game.grid) + 8
    need_w = len(game.grid[0]) + 4
    if height < need_h or width < need_w:
        put(stdscr, 0, 0, f"终端太小，请至少拉到 {need_w}x{need_h}")
        stdscr.refresh()
        return
    title = (
        f" Liinux 地牢  第 {game.floor_index + 1}/{len(FLOORS)} 层"
        f"  HP {game.hp}/{game.max_hp}  ATK {game.atk}"
        f"  钥匙 {game.keys}  药 {game.potions}"
        f"  分数 {game.score}  最高 {best}"
    )
    put(stdscr, 0, 0, title, curses.A_BOLD)
    color = curses.has_colors()
    view = visible_cells(game.grid, game.player)
    for y, row in enumerate(game.grid):
        for x, ch in enumerate(row):
            here = (y, x)
            if here not in game.seen:
                continue
            dim = here not in view
            shown, attr = ch, 0
            if ch == "#":
                shown = "#"
                attr = curses.color_pair(1) if color else 0
            elif ch == "D":
                shown = "D"
                attr = curses.color_pair(5) if color else 0
            elif ch == "k":
                shown = "k"
                attr = curses.color_pair(5) if color else 0
            elif ch == "p":
                shown = "p"
                attr = curses.color_pair(3) if color else 0
            elif here == game.stairs:
                shown = ">"
                attr = curses.color_pair(3) if color else 0
            else:
                shown = "·" if dim else "."
            if dim:
                attr |= curses.A_DIM
            if not dim:
                enemy = game.enemy_at(y, x)
                if enemy:
                    shown = enemy["kind"]
                    attr = curses.color_pair(4) | curses.A_BOLD if color else curses.A_BOLD
            if here == game.player:
                shown = "@"
                attr = curses.color_pair(2) | curses.A_BOLD if color else curses.A_BOLD
            try:
                stdscr.addch(y + 2, x + 2, shown, attr)
            except curses.error:
                pass
    put(stdscr, len(game.grid) + 3, 2, "移动 WASD / 方向键   F 喝药   . 等待   R 重开   Q 退出")
    base = len(game.grid) + 4
    for index, line in enumerate(game.log[-3:]):
        put(stdscr, base + index, 2, line, curses.A_BOLD if index == len(game.log[-3:]) - 1 else 0)
    stdscr.refresh()


def draw_end(stdscr, game, best, won):
    stdscr.erase()
    lines = [
        "=============================",
        "           逃出地牢" if won else "           探索失败",
        "=============================",
        "",
        f"  到达层数：{game.floor_index + 1}",
        f"  得分：{game.score}",
        f"  步数：{game.moves}",
        f"  最高分：{max(best, game.score)}",
        "",
        "  Y 再玩一局     Q 退出",
    ]
    for index, line in enumerate(lines):
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
        game = Dungeon()
        won = False
        while True:
            draw_game(stdscr, game, best)
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                return
            if key in (ord("r"), ord("R")):
                game = Dungeon()
                continue
            command = {
                curses.KEY_UP: "w", curses.KEY_DOWN: "s",
                curses.KEY_LEFT: "a", curses.KEY_RIGHT: "d",
                ord("w"): "w", ord("W"): "w",
                ord("s"): "s", ord("S"): "s",
                ord("a"): "a", ord("A"): "a",
                ord("d"): "d", ord("D"): "d",
                ord("f"): "f", ord("F"): "f",
                ord("."): ".",
            }.get(key)
            if command is None:
                continue
            result = game.act(command)
            if result == "win":
                won = True
                break
            if result == "dead":
                break
        new_score = game.score if won else game.score
        best = save_best(new_score)
        while True:
            draw_end(stdscr, game, best, won)
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
