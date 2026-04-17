# ComfyUI Guagua Nodes

这是一个 ComfyUI 自定义节点项目骨架，所有节点在 ComfyUI 里显示时都会自动带上 `Guagua🐸` 前缀。

## 现在已有的示例节点

- `Guagua🐸 Text Join`
- `Guagua🐸 Prompt Builder`

## 目录结构

- `__init__.py`: ComfyUI 入口
- `nodes/`: 节点注册器和节点实现
- `scripts/new_guagua_node.ps1`: 新建节点模板脚本
- `publish_to_github.ps1`: 提交并推送到 GitHub

## 安装方式

把整个项目目录放到你的 ComfyUI `custom_nodes` 下面，例如：

```text
ComfyUI\custom_nodes\ComfyUI-Guagua-Nodes
```

然后重启 ComfyUI。

## 命名规则

你以后新增节点时，只需要写节点自己的名称，比如 `Prompt Cleaner`。注册器会自动把它变成：

```text
Guagua🐸 Prompt Cleaner
```

这样可以避免以后忘记加前缀。

## 新建一个节点

示例：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\new_guagua_node.ps1 -NodeSlug prompt_cleaner -NodeTitle "Prompt Cleaner"
```

如果你想创建完后立刻提交并推送：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\new_guagua_node.ps1 -NodeSlug prompt_cleaner -NodeTitle "Prompt Cleaner" -Publish
```

## 连接 GitHub 远程仓库

第一次只需要做一次：

```powershell
git init -b main
git remote add origin https://github.com/<你的用户名>/<你的仓库名>.git
```

如果你本机已经配置了 Git 凭据，后面执行下面这条就会自动提交并推送：

```powershell
powershell -ExecutionPolicy Bypass -File .\publish_to_github.ps1 -Message "Add Guagua🐸 Prompt Cleaner"
```

## 推荐工作流

1. 用 `scripts/new_guagua_node.ps1` 生成一个新节点模板。
2. 编辑 `nodes/custom/<你的节点文件>.py`，补上真正逻辑。
3. 跑一次 `publish_to_github.ps1`，把这个节点提交并推送到 GitHub。

如果你愿意，我下一步可以继续帮你把第一个真正可用的图像类节点也做出来，并顺手接上你的 GitHub 仓库地址。
