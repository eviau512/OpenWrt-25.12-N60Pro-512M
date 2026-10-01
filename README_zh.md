# Netcore N60 Pro (512MB ROM) OpenWrt 25.12.x 固件构建

[English](README.md) | [中文](README_zh.md)

本项目提供磊科 Netcore N60 Pro 路由器（硬件改装 512MB SPI-NAND 闪存）适配 OpenWrt 25.12.x 版本的构建配置与工作流，兼容 `v25.12.1`、`v25.12.2`、`v25.12.3`、`v25.12.4`、`v25.12.5` 及 `openwrt-25.12` 分支。

---

## 固件特性

- **闪存空间**：适配 512MB SPI-NAND，UBI 分区范围设为 `0x0580000` 至 `0x20000000`（506.5 MB），可用 Overlay 空间约 450MB+。
- **无线组件**：预装完整版 `wpad`（基于 OpenSSL），替代精简版 `wpad-basic-mbedtls`，支持 802.11s Mesh、802.11k/v/r 快速漫游及 WPA3。
- **管理界面**：集成 LuCI Web 控制面板、`luci-theme-argon` 主题及简体中文语言包。
- **代理支持**：内置 PassWall 及 Sing-Box 核心（包含 `sing-box`、`chinadns-ng`、`dns2socks`、`tcping`、`v2ray-geodata`）。已排除 Rust、Xray、Shadowsocks 等额外组件以缩短构建时间并精简固件体积。
- **包管理器**：预置 APK 签名公钥及软件源配置，便于后续通过 APK v3 在线更新组件。

---

## 适配说明

### 25.12.3+ 上游变更
官方在 `v25.12.3` 及后续版本中增加了新的 Filogic 设备，导致原补丁由于上下文行偏移而无法应用。本项目补丁使用 `netcore,n60` 和 `netcore,n60-pro` 作为锚点，可直接应用于 25.12 全系列。

### 镜像格式与引导流程
MediaTek MT7986 平台使用 UBI + FIT 结构引导（从 UBI 卷读取 Kernel + RootFS FIT 镜像）。将固件打包为 `sysupgrade-tar` 会导致无法启动。本项目保持官方标准的 `sysupgrade.itb` 与 `recovery.itb` 规则。

---

## 目录结构

```
├── .github/workflows/
│   └── build-openwrt-n60-pro-512rom.yml   # GitHub Actions 工作流
├── configs/
│   └── netcore_n60-pro-512rom.config     # 机型 .config 配置文件
├── files/                                # 预置进 rootfs 的文件
│   └── etc/apk/
│       ├── keys/openwrt-passwall-build.pem
│       └── repositories.d/passwall.list
├── patches/
│   └── 0001-mediatek-filogic-add-netcore-n60-pro-512rom.patch # 设备补丁
├── scripts/
│   └── fetch_passwall_packages.py        # PassWall 预编译包抓取脚本
├── README.md                             # 英文文档
└── README_zh.md                          # 中文文档
```

---

## 构建方法

### GitHub Actions
1. Fork 本仓库。
2. 进入仓库页面的 **Actions** 标签页。
3. 选择 **`build-openwrt-n60-pro-512rom`** 并点击 **Run workflow**。
4. 指定需要构建的 OpenWrt Git Tag 或分支（默认 `v25.12.5`）。
5. 运行完毕后在 Artifacts 中下载固件。

### 本地编译
```bash
git clone -b v25.12.5 --depth=1 https://github.com/openwrt/openwrt.git
cd openwrt
git apply /path/to/patches/0001-mediatek-filogic-add-netcore-n60-pro-512rom.patch
./scripts/feeds update -a && ./scripts/feeds install -a

git clone --depth=1 https://github.com/jerrykuku/luci-theme-argon.git package/luci-theme-argon
git clone --depth=1 https://github.com/Openwrt-Passwall/openwrt-passwall.git package/openwrt-passwall
git clone --depth=1 https://github.com/Openwrt-Passwall/openwrt-passwall-packages.git package/openwrt-passwall-packages
rm -rf package/openwrt-passwall-packages/{shadowsocks-rust,shadowsocksr-libev,xray-core,xray-plugin,v2ray-plugin,simple-obfs,hysteria,naiveproxy,shadow-tls}

cp /path/to/configs/netcore_n60-pro-512rom.config .config
cp -r /path/to/files/. files/
make defconfig
make download -j$(nproc)
make -j$(nproc)
```

---

## 固件文件说明

| 文件名 | 用途 |
| :--- | :--- |
| `*-squashfs-sysupgrade.itb` | 系统升级固件（通过 LuCI 界面或 U-Boot 网页刷入） |
| `*-initramfs-recovery.itb` | TFTP 救援恢复镜像 |
| `*-preloader.bin` | MT7986 DDR4 SPI-NAND BL2 引导加载器 |
| `*-bl31-uboot.fip` | MT7986 ATF BL31 + U-Boot FIP 固件 |

---

## 闪存分区划分（512MB SPI-NAND）

```
0x00000000 - 0x00100000 (1MB)   : BL2 (Preloader)
0x00100000 - 0x00180000 (512KB) : u-boot-env (U-Boot 环境变量)
0x00180000 - 0x00380000 (2MB)   : Factory (无线校准数据及 MAC 地址)
0x00380000 - 0x00580000 (2MB)   : FIP (BL31 + U-Boot)
0x00580000 - 0x20000000 (506.5M): UBI (包含 Kernel FIT 卷及 rootfs_data)
```
