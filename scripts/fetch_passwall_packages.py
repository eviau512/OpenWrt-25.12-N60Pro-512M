#!/usr/bin/env python3
import os
import sys
import re
import argparse
import urllib.request
import urllib.error
import time

DEFAULT_FEEDS = ["passwall_luci", "passwall_packages"]
DEFAULT_PACKAGES = [
    "luci-app-passwall",
    "luci-i18n-passwall-zh-cn",
    "sing-box",
    "chinadns-ng",
    "dns2socks",
    "tcping",
    "v2ray-geoip",
    "v2ray-geosite",
    "xray-core",
]

def fetch_feed_file_links(feed, arch="aarch64_cortex-a53", release="packages-25.12", retries=3):
    url = f"https://sourceforge.net/projects/openwrt-passwall-build/files/releases/{release}/{arch}/{feed}/"
    headers = {"User-Agent": "curl/7.81.0"}
    req = urllib.request.Request(url, headers=headers)
    
    for attempt in range(1, retries + 1):
        try:
            print(f"[INFO] Fetching index for {feed} (attempt {attempt}/{retries})...")
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                matches = re.findall(r'\"download_url\":\s*\"([^\"]+)\"', html)
                links = {}
                for durl in matches:
                    parts = durl.strip().split("/")
                    # Usually: .../<filename>/download
                    fname = parts[-2] if parts[-1] == "download" else parts[-1]
                    if fname.endswith(".apk"):
                        links[fname] = durl
                return links
        except Exception as e:
            print(f"[WARN] Error fetching {url}: {e}", file=sys.stderr)
            if attempt < retries:
                time.sleep(2 * attempt)
    return {}

def download_file(url, out_path, retries=3):
    headers = {"User-Agent": "curl/7.81.0"}
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(1, retries + 1):
        try:
            print(f"[INFO] Downloading {os.path.basename(out_path)} from {url}...")
            with urllib.request.urlopen(req, timeout=60) as resp, open(out_path, "wb") as out_f:
                total_bytes = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    total_bytes += len(chunk)
            if total_bytes > 0:
                print(f"[OK] Saved {os.path.basename(out_path)} ({total_bytes} bytes)")
                return True
        except Exception as e:
            print(f"[WARN] Download attempt {attempt} failed: {e}", file=sys.stderr)
            if os.path.exists(out_path):
                os.remove(out_path)
            if attempt < retries:
                time.sleep(3 * attempt)
    return False

def main():
    parser = argparse.ArgumentParser(description="Download pre-built PassWall packages from SourceForge")
    parser.add_argument("--output-dir", required=True, help="Directory to save downloaded APKs")
    parser.add_argument("--arch", default="aarch64_cortex-a53", help="Target architecture")
    parser.add_argument("--release", default="packages-25.12", help="OpenWrt release string")
    parser.add_argument("--packages", nargs="*", default=DEFAULT_PACKAGES, help="Package names to download")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    all_links = {}
    for feed in DEFAULT_FEEDS:
        links = fetch_feed_file_links(feed, arch=args.arch, release=args.release)
        all_links.update(links)

    print(f"[INFO] Found {len(all_links)} total APK packages in feeds.")

    downloaded = []
    missing = []
    for pkg in args.packages:
        # Match exact name prefix: pkg- or pkg_
        matched_file = None
        for fname in all_links:
            if fname.startswith(f"{pkg}-") or fname.startswith(f"{pkg}_"):
                matched_file = fname
                break
        
        if not matched_file:
            print(f"[WARN] No matching APK found for requested package: {pkg}")
            missing.append(pkg)
            continue

        durl = all_links[matched_file]
        target_path = os.path.join(args.output_dir, matched_file)
        if download_file(durl, target_path):
            downloaded.append(matched_file)
        else:
            print(f"[ERROR] Failed to download {matched_file}", file=sys.stderr)
            missing.append(pkg)

    print("\n=== Download Summary ===")
    print(f"Successfully downloaded {len(downloaded)} packages:")
    for f in downloaded:
        print(f"  - {f}")
    if missing:
        print(f"Missing/failed {len(missing)} packages: {', '.join(missing)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
