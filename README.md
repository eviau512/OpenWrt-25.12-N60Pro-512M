# Build N60 Pro 512M (OpenWrt 25.12.x 适配版)

本项目用于通过 GitHub Actions 云端编译磊科 **Netcore N60 Pro**（硬件改装 **512MB SPI-NAND**）的官方 OpenWrt **v25.12.x**（兼容 `v25.12.1`、`v25.12.2`、`v25.12.3`、`v25.12.4`、`v25.12.5` 以及 `openwrt-25.12` 稳定分支）固件。

---

## 🌟 固件内置特性与预装软件

* **完整版 `wpad`（基于 OpenSSL）**：
  * 替换默认精简版 `wpad-basic-mbedtls`，改用全功能 `wpad`。
  * 完整支持 **802.11s Mesh 组网**、**802.11k/v/r 无缝快速漫游**、**WPA3-Personal (SAE) / WPA3-Enterprise**。
* **LuCI Web 管理界面与 Argon 现代化主题**：
  * 完整集成 LuCI 控制面板及中文语言包。
  * 内置流行的 **`luci-theme-argon`** 现代化毛玻璃主题以及 **`luci-app-argon-config`** 主题个性化配置插件（支持深色模式、自定义登录壁纸、毛玻璃特效等）。
* **PassWall + Sing-Box 原生源码集成内置**：
  * 直接集成官方 [openwrt-passwall](https://github.com/Openwrt-Passwall/openwrt-passwall) 与 [openwrt-passwall-packages](https://github.com/Openwrt-Passwall/openwrt-passwall-packages) 源码进行原生交叉编译，与固件系统完全融为一体。
  * 固件出厂即预装：
    * `luci-app-passwall` + `luci-i18n-passwall-zh-cn`（中文管理界面）
    * `sing-box`（高性能代理核心）
    * `chinadns-ng`（智能国内/海外 DNS 分流）
    * `dns2socks`、`tcping`、`v2ray-geodata`（GeoIP / GeoSite 规则库）
  * 内核已完整编译并集成 `kmod-nft-tproxy`、`kmod-ipt-tproxy`、`kmod-tun`、`ipset`、`iptables` 等全部转发与透明代理底层驱动。
* **开箱即用 APK 软件源与公钥预置**：
  * 固件同时预置了 `/etc/apk/keys/openwrt-passwall-build.pem` 签名公钥与 `/etc/apk/repositories.d/passwall.list` 在线软件源。
  * 刷机启动后，也可以直接通过 Web 界面或终端 `apk add` / `apk update` 在线安装或更新其他组件（如 Xray、Hysteria 等），无需手动配置密钥。

---

## 📌 问题背景与失败分析

### 1. 为什么原项目（XIAOZHAOXSXH/Build-N60-Pro-512M）在 25.12.3+ 失效？
* **根本原因**：OpenWrt 官方在 `v25.12.3` 中为 `filogic` 目标添加了新机型（如 `netcraze_nap-630` 等），并在随后的 `v25.12.4` 和 `v25.12.5` 中进一步扩充了设备列表。
* 原项目的补丁文件（`0001-mediatek-filogic-add-netcore-n60-pro-512rom.patch`）基于 `v25.12.1` 的上下文行生成，当目标文件（`filogic.mk`、`uboot-envtools`、`platform.sh`）因新机型加入而发生行偏移时，工作流中的 `git apply --check` 直接报错中断。

### 2. 为什么先前的适配尝试（YangZJ781/Build-N60-Pro-512M-25.12.5）固件无法启动？
* **镜像打包规则错误**：MediaTek MT7986 平台采用 UBI + FIT 结构启动（U-Boot 挂载 UBI 分区并读取 `fit` 卷内的 Kernel + SquashFS 镜像）。先前尝试误将 `filogic.mk` 中的 FIT 规则删除，改成了 `IMAGE/sysupgrade.bin := sysupgrade-tar`（生成了错误的 tar 升级包），导致 U-Boot 根本无法引导。
* **设备树 (DTS) 破坏**：原尝试删除了 DTS 中的 `chosen { bootargs = "root=/dev/fit0 rootwait"; rootdisk = <&ubi_rootdisk>; };` 以及 UBI 分区内的 `compatible = "linux,ubi";` 和 `volumes { ... fit ... }` 节点，并且错误引入了不适用的 `nmbm` 配置。这使得 Linux 内核在启动时既无法识别 UBI，也找不到 root 根文件系统。
* **基础网络与固件脚本缺失**：原尝试移除了所有 `base-files`（`01_leds`、`02_network`、`11_fix_wifi_mac`、`platform.sh`）对 `netcore,n60-pro-512rom` 的支持，即便内核启动也无法识别网口及分配 MAC 地址。

---

## 🛠 本次适配方案与关键修复

1. **重构通用兼容补丁**：
   * 精准选取在 OpenWrt 25.12 全系列中恒定存在的上下文锚点（以 `netcore,n60` 和 `netcore,n60-pro` 为锚）。
   * 补丁已通过对 `v25.12.1`、`v25.12.2`、`v25.12.3`、`v25.12.4`、`v25.12.5` 及 `openwrt-25.12` 分支的实机 `git apply --check` 严格测试，全部 **100% 无错应用**。

2. **恢复完整的 MT7986 官方 FIT/UBI 引导链**：
   * 在 `filogic.mk` 中正确定义 `Device/netcore_n60-pro-512rom`，生成标准的 `sysupgrade.itb`（Kernel + RootFS FIT）与 `recovery.itb`（TFTP 救援镜像）。
   * 保持 U-Boot 与 BL2 引导固件的正确编译与依赖（`mt7986-bl2 spim-nand-ddr4` 和 `mt7986-bl31-uboot netcore_n60-pro`）。

3. **完整 512MB SPI-NAND 分区定义**：
   * 严格对应硬改 512MB 闪存分区，UBI 分区范围扩展至 `reg = <0x0580000 0x1fa80000>`（共 506.5 MB），使系统可使用完整的 ~450MB+ Overlay 可用空间。
   * 保留 `root=/dev/fit0` 与 UBI `fit` 卷的自动挂载机制。

4. **完整适配基础配置脚本**：
   * `01_leds`：正常驱动电源灯、网络灯与状态指示灯。
   * `02_network`：正确绑定 4 个千兆 LAN 口与 1 个 2.5G WAN 口（eth1）。
   * `11_fix_wifi_mac`：正确计算并分配无线物理网卡 MAC 地址。
   * `platform.sh`：正确注册固件升级校验与刷写逻辑。

---

## 🚀 使用指南

### 1. 仓库文件结构

```
├── .github/workflows/
│   └── build-openwrt-n60-pro-512rom.yml   # 自动化云编译工作流
├── configs/
│   └── netcore_n60-pro-512rom.config     # 512M 机型专属 .config 配置文件
├── files/                                # 预置进固件 rootfs 的系统文件
│   └── etc/apk/
│       ├── keys/openwrt-passwall-build.pem
│       └── repositories.d/passwall.list
├── patches/
│   └── 0001-mediatek-filogic-add-netcore-n60-pro-512rom.patch # 25.12.x 通用适配补丁
├── scripts/
│   └── fetch_passwall_packages.py        # 自动抓取并校验 PassWall 预编译包
└── README.md
```

### 2. 编译方法

1. **Fork 本仓库** 到你自己的 GitHub 账号下。
2. 进入仓库页面的 **Actions** 选项卡。
3. 在左侧选择 **`build-openwrt-n60-pro-512rom`**。
4. 点击右侧 **Run workflow**：
   * `OpenWrt Git Tag or Branch to build`：可保持默认 `v25.12.5`，或手动输入任意版本（如 `v25.12.3`、`v25.12.4` 或分支 `openwrt-25.12`）。
   * `Pre-install PassWall + Sing-Box from SourceForge`：默认勾选（设置为 `true`），直接把 PassWall + Sing-Box 预装进固件。
5. 编译完成后，在 Actions 运行结果的 **Artifacts** 处下载固件压缩包。

### 3. 生成的固件说明

| 文件名格式 | 用途说明 |
| :--- | :--- |
| `*-squashfs-sysupgrade.itb` | **日常升级固件**（在 OpenWrt Web 页面或 U-Boot 网页控制台直接刷入） |
| `*-initramfs-recovery.itb` | **救援/救砖镜像**（供 TFTP 网络恢复时引导启动） |
| `*-preloader.bin` | MT7986 DDR4 SPI-NAND BL2 引导程序 |
| `*-bl31-uboot.fip` | MT7986 ATF BL31 + U-Boot FIP 固件 |

---

## 🖧 闪存分区规划（512MB SPI-NAND）

```
0x00000000 - 0x00100000 (1MB)   : BL2 (Preloader)
0x00100000 - 0x00180000 (512KB) : u-boot-env (环境变量)
0x00180000 - 0x00380000 (2MB)   : Factory (无线校准数据及 MAC 地址)
0x00380000 - 0x00580000 (2MB)   : FIP (BL31 + U-Boot)
0x00580000 - 0x20000000 (506.5M): UBI (包含 fit 卷以及可动态利用的 rootfs_data)
```
