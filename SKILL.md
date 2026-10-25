---
name: shangmei-moss-image
description: Use when drawing 上美 cel stills on local MOSS-Image.
version: 0.1.0
author: Luis Lin, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MOSS-Image, ComfyUI, shangmei, cel, 8GB]
    related_skills: [comfyui-local-deployment]
---

# 上美赛璐璐 / 本地 MOSS-Image

在已有 ComfyUI 上用本地 MOSS-Image 出上海美术电影制片厂《黑猫警长》手绘赛璐璐静帧。不下载权重、不改 ComfyUI 源码、不把这条路径用于视频。

验证环境：Windows，RTX 5060 Ti 8GB，ComfyUI 0.42.5，SFT INT8 + Qwen3.5-9B W4A8 + flux2 small VAE。768×1024、20 步、`er_sde` / `simple` / CFG 2.5，约 3 分钟一张。

## When to Use

- 用户要本地出上美、黑猫警长、手绘赛璐璐、人形动物静帧。
- 要在 8GB 显卡上跑 MOSS-Image，而不是云端或 BF16。
- Don't use for：视频、写实、3D、需要画面里出现正确文字（这套权重仍会在招牌上涂字）、Bonsai 或其他 LLM 安装。

## Prerequisites

- ComfyUI **0.42.5 或更新**，且 `object_info/CLIPLoader` 的 `type` 含 `moss_image`。v0.41.3 发布版没有原生支持，不要装仓库插件来补。
- 三份权重，字节必须对上，来源 [Comfy-Org/MOSS-Image](https://huggingface.co/Comfy-Org/MOSS-Image)：

| 文件 | 字节 | 目录 |
| --- | --- | --- |
| `moss_image_sft_int8_convrot.safetensors` | 5413698958 | `models/diffusion_models/` |
| `qwen3.5_9b_w4a8_gptq.safetensors` | 7343591088 | `models/text_encoders/` |
| `flux2-vae_small.safetensors` | 249521340 | `models/vae/` |

- 启动带 `--lowvram`。8GB 上不要同时跑 Ollama 或其他占满显存的进程。
- 用 HTTP API 提交，不要手改 workflow JSON 里的节点 id 去猜接线。

## Procedure

1. 确认服务在跑：`http://127.0.0.1:8188/system_stats` 返回 200。没有就用该安装的 venv 启动：`python main.py --port 8188 --listen 127.0.0.1 --lowvram`。完成标准：日志出现 `To see the GUI`。
2. 核对加载器能看到三份文件：`/models/diffusion_models`、`/models/text_encoders`、`/models/vae`。缺文件就停，不要换 BF16。
3. 提交 API 图，节点只用这些：`UNETLoader`（`weight_dtype=default`）、`CLIPLoader`（`type=moss_image`，`device=cpu`）、`VAELoader`、两路 `CLIPTextEncode`、`EmptyFlux2LatentImage`、`KSampler`、`VAEDecode`、`SaveImage`。完成标准：`/prompt` 返回 `node_errors` 为空。
4. 采样固定为：768×1024，seed 按张变，steps 20，cfg 2.5，sampler `er_sde`，scheduler `simple`，denoise 1。不要接 `ModelSamplingSD3`。原生模型已带 shift 5；旧插件工作流的 SD3 采样节点不能拿过来。
5. 正向提示词用下面的模板，再接一句场景。负向用固定串。一次只排一张；8GB 上不要 `batch_size>1`。
6. 轮询 `/history/<prompt_id>` 直到 `status_str=success`，再按返回的 `filename` + `subfolder` 取图。完成标准：PNG 存在，宽高为 768×1024。
7. 用 `vision_analyze` 看一眼再交付。人形、墨线、平涂能对上上美才算过。招牌乱码不算失败，但要告诉用户。

## Prompt

正向模板（整段拼在场景前）：

```
A single full-body character illustration in the exact hand-drawn cel style of Shanghai Animation Film Studio's 1984 series Black Cat Sheriff: bold even black ink contours, flat gouache color fills, slight film grain, painted scenic background, 1980s Chinese cartoon proportions, large glossy eyes, bipedal anthropomorphic animal with simple clothing folds, warm clear daylight, blank signs with no writing, no text, no letters, no logo, no watermark, no photo, no 3D, no modern anime.
```

场景只写动作和服装，不写画风。要求：一只双足站立的动物、三分之侧、尾巴可见、背景是画出来的场景而不是照片。

负向（固定）：

```
nsfw, worst quality, bad anatomy, extra limbs, extra fingers, watermark, jpeg artifact, photorealistic, realistic fur, 3d render, cgi, modern anime, chibi, blurry, text, letters, logo, signature, deformed face, writing, calligraphy
```

已跑通的四张，种子照抄，不要改采样器：

| 文件前缀 | seed | 场景 |
| --- | --- | --- |
| `otter_hawker` | 1101 | 水豚，白小贩制服白纸帽，新加坡小贩中心炒粿条 |
| `hornbill_traffic` | 2202 | 东方斑犀鸟，深蓝交警服白头盔，店屋街指挥交通 |
| `macaque_site` | 3303 | 长尾猕猴，黄盔橙色背心，组屋脚手架 |
| `eagle_port` | 4404 | 白腹海雕，海军领航员制服，集装箱码头 |

## Pitfalls

- 日志里 `No module named 'triton'` 是 INFO，不是失败。以 `/history` 的 `status_str` 为准。
- 提示词写了 no text，背景招牌仍可能出乱码。不要为此重跑，除非用户要求画面文字正确。要正确文字就换任务，不要在这套里加字。
- 不要用仓库插件工作流的 `ModelSamplingSD3`。原生权重的 shift 已经是 5。
- 不要用 `EmptyLatentImage`。潜空间是 Flux2，必须 `EmptyFlux2LatentImage`。
- BF16 DiT 约 10GB，8GB 上不要下。INT8 + W4A8 + CPU 上的文本编码器是这张卡的组合。
- 直接 `python main.py` 启动时，图片落在安装目录的 `output/`，不一定是 Desktop 配置的 output 目录。以 history 里的路径为准。
- Comfy Desktop 的 `installations.json` 可能仍写着旧版本和 `--port 8000`。以 `comfyui_version.py` 和实际监听端口为准。

## Verification

- 三份权重字节与上表一致，且 safetensors 头能解析出张量。
- `CLIPLoader` 的 type 列表含 `moss_image`。
- 一张测试图 `status_str=success`，尺寸 768×1024，肉眼能看出墨线平涂和人形动物。
