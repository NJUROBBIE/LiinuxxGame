# Liinux 夺旗

在终端里走迷宫：捡完本关全部金币 `$`，再走到旗帜 `E`。一共 3 关。

仓库地址：https://github.com/NJUROBBIE/LiinuxxGame

只使用 Python 3 标准库，不需要 `pip install`。

## 运行

```bash
cd ~/LiinuxxGame
python3 game.py
```

也可以：

```bash
chmod +x game.py
./game.py
```

## 操作

| 按键 | 作用 |
| --- | --- |
| W A S D 或方向键 | 移动 |
| R | 重开本关 |
| Q | 退出 |
| Y | 通关后再玩一局 |

金币 +10 分，过关 +50 分。最高分写在当前目录的 `highscore.txt`（已加入 `.gitignore`，不会提交）。

## 自测关卡

```bash
python3 game.py --self-test
```

## 建议的两次提交

在 WSL 的 Ubuntu 里操作，方便截图。先配置自己的名字和邮箱（邮箱尽量和 GitHub 一致）：

```bash
git config --global user.name "NJUROBBIE"
git config --global user.email "你的邮箱"
```

第一次只提交游戏：

```bash
cd ~
mkdir LiinuxxGame
cd LiinuxxGame
git init
# 把 game.py 和 .gitignore 放进这个目录
git add game.py .gitignore
git commit -m "feat: 添加终端夺旗小游戏"
```

第二次补上说明再推送：

```bash
# 把 README.md 放进目录
git add README.md
git commit -m "docs: 补充运行说明"
git branch -M main
git remote add origin https://github.com/NJUROBBIE/LiinuxxGame.git
git push -u origin main
```

之后改代码只需：

```bash
git add .
git commit -m "说明这次改了什么"
git push
```

查看记录：

```bash
git status
git log --oneline
git remote -v
```
