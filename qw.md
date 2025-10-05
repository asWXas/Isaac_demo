好的，我们来分两部分解答您的问题：先分析您截图中的情况并提供解决方案，然后为您整理一份 Git 常用命令大全。

-----

### 第一部分：分析您当前的情况及解决办法

#### 情况分析

根据您提供的截图，我们可以解读出以下信息：

1.  **`main` (蓝色标签)**: 这是您**本地**的 `main` 分支指针，它指向最新的一个提交 `产考 direct asWXas`。
2.  **`origin/main` (紫色标签)**: 这是**远程仓库**（通常是 GitHub、GitLab 等）的 `main` 分支的快照，它指向一个较旧的提交 `01 asWXas`。
3.  **分支状态**: 您本地的 `main` 分支比远程的 `origin/main` 分支**多了 5 个提交**（从 `02 asWXas` 到 `产考 direct asWXas`）。

**结论是：** 您在本地进行了多次提交，但是还没有将这些新的变更推送到远程服务器上。这在 Git 工作流中是非常正常的情况。

#### 解决办法

您需要做的就是将本地的新提交\*\*推送（Push）\*\*到远程仓库，让远程仓库也更新到最新状态。

**推荐的操作步骤：**

1.  **（好习惯）先拉取远程更新**：在推送之前，最好先拉取一下远程仓库的最新变更，以防其他人已经推送了新的代码。推荐使用 `pull --rebase` 来保持提交历史的整洁。

    ```bash
    # 拉取远程 main 分支的最新代码，并把你本地的新提交“嫁接”在它后面
    git pull --rebase origin main
    ```

      * **如果没有冲突**: 命令会顺利执行。
      * **如果有冲突**: Git 会提示您解决冲突，解决后使用 `git add .` 和 `git rebase --continue` 继续操作。
      * **如果远程没有新代码**: 这个命令不会做任何事，直接进入下一步即可。

2.  **推送本地变更到远程仓库**：

    ```bash
    # 将本地 main 分支的提交推送到 origin 远程仓库的 main 分支
    git push origin main
    ```

执行完 `git push` 命令后，您会发现远程仓库 `origin/main` 的指针就会移动到和您本地 `main` 一样的位置，表示同步成功。

-----

### 第二部分：Git 常用命令大全

这里为您整理了一份从配置到日常使用的常用 Git 命令，并按功能分类。

#### 1\. 配置 (Configuration)

只需要在第一次使用 Git 时配置。

```bash
# 配置你的用户名
git config --global user.name "Your Name"

# 配置你的邮箱
git config --global user.email "your.email@example.com"
```

#### 2\. 创建与克隆 (Creating & Cloning)

```bash
# 在当前目录下初始化一个新的 Git 仓库
git init

# 从远程 URL 克隆一个仓库到本地
git clone [repository_url]
```

#### 3\. 基本工作流程 (The Core Workflow)

这是每天都会用到的命令。

```bash
# 查看工作区、暂存区的状态
git status

# 将文件添加到暂存区
git add <file_name>   # 添加指定文件
git add .             # 添加当前目录下所有变更

# 将暂存区的内容提交到本地仓库
git commit -m "Your descriptive commit message"

# 查看提交历史
git log
git log --oneline --graph # 以单行和图形的方式显示，更清晰

# 查看工作区与暂存区的差异
git diff

# 查看暂存区与最新提交的差异
git diff --staged
```

#### 4\. 分支管理 (Branch Management)

```bash
# 查看所有本地分支（-a 查看所有本地和远程分支）
git branch
git branch -a

# 创建一个新分支
git branch <branch_name>

# 切换到指定分支
git checkout <branch_name>
# 或者使用新命令 (推荐)
git switch <branch_name>

# 创建并立即切换到新分支
git checkout -b <new_branch_name>
# 或者使用新命令 (推荐)
git switch -c <new_branch_name>

# 将指定分支的变更合并到当前分支
git merge <branch_name>

# 删除一个已经合并的分支
git branch -d <branch_name>
# 强制删除一个分支（即使还没合并）
git branch -D <branch_name>
```

#### 5\. 远程仓库操作 (Working with Remotes)

```bash
# 查看配置的所有远程仓库
git remote -v

# 添加一个新的远程仓库
git remote add <remote_name> <repository_url> # 通常远程仓库名叫 origin

# 从远程仓库拉取最新数据（但还不合并）
git fetch <remote_name>

# 从远程仓库拉取最新数据并合并到本地分支 (fetch + merge)
git pull <remote_name> <branch_name>

# 将本地分支的提交推送到远程仓库
git push <remote_name> <branch_name>
```

#### 6\. 撤销与修改 (Undoing Changes)

这些命令要小心使用！

```bash
# 修改最后一次的提交信息
git commit --amend

# 撤销工作区的修改（恢复到最近一次提交的状态）
git restore <file_name>

# 将文件从暂存区撤销，但保留工作区的修改
git restore --staged <file_name>

# 重置 HEAD 指针到某个提交，用来撤销提交（危险！）
# --soft: 只移动 HEAD 指针，保留暂存区和工作区
git reset --soft <commit_hash>
# --mixed (默认): 移动 HEAD，重置暂存区，但保留工作区
git reset --mixed <commit_hash>
# --hard: 彻底回退，暂存区和工作区的修改都会丢失！
git reset --hard <commit_hash>

# 创建一个新的提交来“反转”某个历史提交的效果，更安全
git revert <commit_hash>
```

#### 7\. 储藏 (Stashing)

当你需要临时切换分支，但又不想提交当前不完整的代码时非常有用。

```bash
# 将当前工作区和暂存区的修改临时保存起来
git stash

# 查看所有储藏的列表
git stash list

# 恢复最近一次的储藏，并从储藏列表中删除它
git stash pop

# 恢复最近一次的储藏，但保留它在储藏列表中
git stash apply

# 删除所有储藏
git stash clear
```

希望这份总结能帮助您解决当前的问题，并让您对 Git 的日常使用更加得心应手！