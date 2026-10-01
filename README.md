# OpenWrt 25.12.x for Netcore N60 Pro (512MB ROM)

[English](README.md) | [中文](README_zh.md)

OpenWrt 25.12.x firmware build support for Netcore N60 Pro routers modded with 512MB SPI-NAND flash. Compatible with `v25.12.1`, `v25.12.2`, `v25.12.3`, `v25.12.4`, `v25.12.5`, and the `openwrt-25.12` maintenance branch.

---

## Features

- **Flash Partitioning**: Configured for 512MB SPI-NAND with UBI partition allocated from `0x0580000` to `0x20000000` (506.5 MB), providing ~450MB+ persistent storage overlay.
- **Wireless**: Full OpenSSL-based `wpad` replacing `wpad-basic-mbedtls`, supporting 802.11s mesh, 802.11k/v/r fast roaming, and WPA3 Personal/Enterprise.
- **Web Interface**: LuCI with `luci-theme-argon` and Simplified Chinese language pack (`CONFIG_LUCI_LANG_zh_Hans`).
- **Proxy Services**: PassWall with Sing-Box core (`sing-box`, `chinadns-ng`, `dns2socks`, `tcping`, `v2ray-geodata`). Non-essential engines (Rust, Xray, Shadowsocks) are excluded to minimize build time and image size.
- **Package Management**: Pre-installed APK public key and repository configuration for online package updates via APK v3.

---

## Technical Notes

### Upstream Changes in 25.12.3+
OpenWrt added new Filogic targets in `v25.12.3` through `v25.12.5`, causing line offset rejections in earlier patches (`0001-mediatek-filogic-add-netcore-n60-pro-512rom.patch`). The patch in this repository uses stable anchors (`netcore,n60` / `netcore,n60-pro`) across all 25.12 releases.

### Bootloader and Image Format
MT7986 Filogic uses a U-Boot FIT architecture reading a kernel + rootfs FIT image from a UBI volume. Attempts to package firmware as `sysupgrade-tar` fail to boot on standard U-Boot. This project maintains the official `sysupgrade.itb` and `recovery.itb` image definitions.

---

## Repository Structure

```
├── .github/workflows/
│   └── build-openwrt-n60-pro-512rom.yml   # GitHub Actions workflow
├── configs/
│   └── netcore_n60-pro-512rom.config     # OpenWrt .config file
├── files/                                # Rootfs overlay files
│   └── etc/apk/
│       ├── keys/openwrt-passwall-build.pem
│       └── repositories.d/passwall.list
├── patches/
│   └── 0001-mediatek-filogic-add-netcore-n60-pro-512rom.patch # Target patch
├── scripts/
│   └── fetch_passwall_packages.py        # PassWall package fetch utility
├── README.md                             # English documentation
└── README_zh.md                          # Chinese documentation
```

---

## Building

### GitHub Actions
1. Fork this repository.
2. Go to the **Actions** tab.
3. Select **`build-openwrt-n60-pro-512rom`** and click **Run workflow**.
4. Specify the OpenWrt Git tag/branch (defaults to `v25.12.5`).
5. Download artifacts from the completed run.

### Local Build
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

## Output Artifacts

| Filename | Purpose |
| :--- | :--- |
| `*-squashfs-sysupgrade.itb` | System upgrade image for LuCI web interface or U-Boot web recovery |
| `*-initramfs-recovery.itb` | TFTP recovery image |
| `*-preloader.bin` | MT7986 DDR4 SPI-NAND BL2 bootloader |
| `*-bl31-uboot.fip` | MT7986 ATF BL31 + U-Boot FIP image |

---

## Flash Layout (512MB SPI-NAND)

```
0x00000000 - 0x00100000 (1MB)   : BL2 (Preloader)
0x00100000 - 0x00180000 (512KB) : u-boot-env (U-Boot environment)
0x00180000 - 0x00380000 (2MB)   : Factory (Calibration data & MAC addresses)
0x00380000 - 0x00580000 (2MB)   : FIP (BL31 + U-Boot)
0x00580000 - 0x20000000 (506.5M): UBI (Kernel FIT volume & rootfs_data)
```
