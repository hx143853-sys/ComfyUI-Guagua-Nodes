# ComfyUI Guagua Nodes

这是一个 ComfyUI 自定义节点仓库，所有节点在 ComfyUI 中显示时都会自动带上 `Guagua🐸` 前缀。

## 当前节点

- `Guagua🐸 Seedream 5.0 Image`
- `Guagua🐸 Style Prompt Preset`
- `Guagua🐸 Qwen Multimodal`
- `Guagua🐸 Text Join`
- `Guagua🐸 Prompt Builder`

## 安装方式

把整个项目目录放到你的 ComfyUI `custom_nodes` 目录下，例如：

```text
ComfyUI\custom_nodes\ComfyUI-Guagua-Nodes
```

然后在 ComfyUI 的 Python 环境中安装依赖：

```powershell
pip install -r requirements.txt
```

建议使用正在运行 ComfyUI 的那套 Python，例如 Linux/AutoDL 常见环境可以写成：

```bash
python -m pip install -r requirements.txt
```

最后重启 ComfyUI。

## 节点说明

### 1. Guagua🐸 Seedream 5.0 Image

用途：调用火山方舟 Seedream 5.0 模型做文生图、图生图或多图融合，输出 `IMAGE`。

输入：

- `api_key`: 火山方舟 API Key
- `prompt`: 文生图提示词
- `model`: Seedream 模型下拉，当前包含 `doubao-seedream-5-0-lite-260128`、`doubao-seedream-5-0-260128`、`doubao-seedream-4-5-251128`
- 可选 `IMAGE` 输入：不连线时是文生图；连 1 张图时按图生图提交；连入批量 `IMAGE` 时按多图融合提交，当前上限为 10 张参考图
- `resolution`: 会直接作为请求里的 `size` 提交，当前支持 `2K` / `3K`
- `aspect_ratio`: 当前仅为兼容旧工作流保留，不再参与 Seedream 5.0 请求体
- `output_format`: 输出图片格式，当前支持 `png` / `jpeg`
- `seed`: 当前仅为兼容旧工作流保留，不再参与 Seedream 5.0 请求体
- `guidance_scale`: 当前仅为兼容旧工作流保留，不再参与 Seedream 5.0 请求体
- `watermark`: 是否加水印

### 2. Guagua🐸 Style Prompt Preset

用途：给基础提示词拼接风格化英文描述，输出 `STRING`。

分类：

- `空`
- `真人摄影`
- `动漫`
- `3D`

内置 30 个精选预设，界面是中文名称，输出为英文详细风格词。

新增预设：

- `动漫 / 美漫风格`
- `动漫 / 超级英雄美漫`
- `动漫 / 漫画封面`
- `动漫 / 黑色漫画`
- `动漫 / 复古银时代美漫`
- `动漫 / 独立漫画风`

### 3. Guagua🐸 Qwen Multimodal

用途：统一处理 Qwen 文本问答、图片分析、视频分析，输出 `STRING`。

输入：

- `api_key`: 阿里云百炼 DashScope API Key
- `task_mode`: `text_chat` / `image_analysis` / `video_analysis`
- `model`: 文本模型或视觉模型
- `system_prompt`
- `user_prompt`
- 可选 `IMAGE` 输入
- 可选 `image_path_or_url`
- 可选 `video_path_or_url`

规则：

- `text_chat` 仅允许 `qwen-plus` / `qwen-turbo` / `qwen-max`
- `image_analysis` 和 `video_analysis` 仅允许视觉模型
- `image_analysis` 会优先使用连接进来的 `IMAGE`

## 目录结构

- `__init__.py`: ComfyUI 入口
- `nodes/`: 节点、共享 API 工具、风格预设数据
- `tests/`: 无网单元测试
- `scripts/new_guagua_node.ps1`: 新建节点模板脚本
- `publish_to_github.ps1`: 提交并推送到 GitHub

## 测试

运行全部单元测试：

```powershell
python -m unittest discover -s tests
```

## 推送工作流

这个仓库已经连接到 GitHub，后续每完成一个节点都可以直接提交并推送：

```powershell
powershell -ExecutionPolicy Bypass -File .\publish_to_github.ps1 -Message "Add Guagua🐸 node"
```

如果你想快速生成一个新节点模板：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\new_guagua_node.ps1 -NodeSlug prompt_cleaner -NodeTitle "Prompt Cleaner"
```
