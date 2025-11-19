# Dr.R 锁定式临床科研平台封装

该项目将临床科研 Web 门户封装为 RUIYI TECH 打造的 **Dr.R** 全屏
锁定桌面应用，适用于 Ubuntu 20.04 等系统的科室一体机场景。应用
开机自启后会占据整个桌面，普通用户无法通过常见快捷键或关闭按钮
退出。

## 功能亮点

- **沉浸式 UI**：顶部状态栏显示实时状态与系统时间，侧边栏提供
  快捷导航，整体配色统一，支持高清屏幕。
- **安全锁定**：窗口无边框、强制全屏，并屏蔽 `Alt+F4`、`Esc`
  等常见退出方式，仅管理员快捷键可以解除锁定。
- **快捷入口**：预置科研门户、数据填报、分析驾驶舱等常用链接，
  默认统一指向 `http://127.0.0.1:8182/aiportal/...`，可在
  `clinical-research-platform.py` 中调整。
- **输入法辅助面板**：全屏锁定模式下也能调出额外的文字缓冲区，
  使用系统输入法录入中文后“一键注入”到当前网页光标。
- **品牌化标识**：全新的 Dr.R 图标以内嵌 Base64 形式存储，通过
  `branding_assets.py` 自动写出，UI、PyInstaller 与 Debian 包中
  保持一致，避免 PR 出现“二进制文件不支持”的提示。
- **资源打包**：通过 PyInstaller + Debian 打包脚本，一次构建后
  可得到直接安装的 `.deb` 包，包含桌面图标与 launcher。

## 快捷键

| 快捷键 | 作用 |
| ------ | ---- |
| `Ctrl + Alt + Shift + L` | 切换锁定/解锁状态 |
| `Ctrl + Alt + Shift + Q` | 在已解锁时退出应用 |
| `Ctrl + Alt + Shift + H` | 快速返回首页 |

侧边栏提供 **输入法辅助面板** 按钮，点击后可以在弹出的缓冲
窗口中使用任意系统输入法（如 fcitx/IBus）输入文本，并将内容注入
到网页当前光标位置。若需要切换系统输入法，请确保桌面环境已启用
对应输入法守护进程（`fcitx5`, `ibus-daemon` 等）。

## 运行与调试

```bash
python3 clinical-research-platform.py
```

> 提示：在无显示的服务器上可以设置 `QT_QPA_PLATFORM=offscreen`
> 运行以验证语法。

可通过参数输出版本或开发者信息，便于外部脚本读取：

```bash
python3 clinical-research-platform.py --print-version
python3 clinical-research-platform.py --print-author
```

## 构建步骤

1. 安装依赖（PyQt5、PyQtWebEngine、pyinstaller 等）。
2. （可选）若需要手动生成图标，可执行：

   ```bash
   python3 branding_assets.py --write-icon dr-r-icon.png
   ```

   `build_deb.sh` 与 PyInstaller spec 文件会在打包前自动生成
   所需的 `dr-r-icon.png`，因此无需将二进制图标纳入 Git。
3. 执行打包脚本：

   ```bash
   ./build_deb.sh 1.0.0
   ```

   - 如果未指定版本参数，会通过 `--print-version` 动态读取
     `APP_VERSION`。
   - 产物会保存在 `build/dr-r_<version>_amd64.deb`，文件包含
     `Dr.R` 图标、Desktop Entry 与 Launcher。

若在封闭网络环境中无法直接 `pip install`，可以提前在可联网环境
下载离线 wheel 包并复制到容器中再安装。

## 常见问题

- **创建拉取请求时提示 “Binary files not supported”**

  该提示来自 `git request-pull`/部分代码托管平台，当 diff 中包含
  PNG 等二进制资产时就会触发。现在图标以内嵌 Base64 存储，Git
  仓库中只留下文本文件，因此重新同步最新代码后即可消除该提示。
  如需重新生成实际 PNG，用 `python3 branding_assets.py --write-icon`
  命令即可。
