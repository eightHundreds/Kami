#!/usr/bin/env python3
"""Apply the Kami identity to an upstream release checkout."""
from __future__ import annotations
import os, re
from pathlib import Path
ROOT = Path(os.environ.get("KAMI_SOURCE_DIR", Path(__file__).resolve().parents[2]))
APP_ID = "com.eighthundreds.kami"
REPOSITORY = "eightHundreds/Kami"
def replace_once(text, old, new, label):
    if text.count(old) != 1: raise SystemExit(f"{label}: expected one upstream match, found {text.count(old)}")
    return text.replace(old, new, 1)
def replace_pattern_once(text, pattern, replacement, label):
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    if len(matches) != 1: raise SystemExit(f"{label}: expected one upstream match, found {len(matches)}")
    return re.sub(pattern, replacement, text, count=1, flags=re.MULTILINE)
def main():
    run_number = int(os.environ["GITHUB_RUN_NUMBER"]); run_attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
    build_file = ROOT / "app/build.gradle.kts"; gradle = build_file.read_text(encoding="utf-8")
    code_pattern = r"^(\s*versionCode\s*=\s*)(\d+)(\s*)$"
    name_pattern = r'^(\s*versionName\s*=\s*)"([^"]+)"(\s*)$'
    code = re.search(code_pattern, gradle, re.MULTILINE); name = re.search(name_pattern, gradle, re.MULTILINE)
    if not code or not name: raise SystemExit("Could not identify upstream versionCode/versionName")
    upstream_version = name.group(2); tag = os.environ["KAMI_RELEASE_TAG"]
    version = tag.lstrip("vV")
    if not re.fullmatch(r"\d+(?:\.\d+)*", version): raise SystemExit(f"Unsupported release tag: {tag}")
    version_code = max(int(code.group(2)), 1_000_000) + run_number * 1_000 + run_attempt
    gradle = replace_pattern_once(gradle, r'^(\s*applicationId\s*=\s*)"[^"]+"(\s*)$', lambda m:f'{m.group(1)}"{APP_ID}"{m.group(2)}', "applicationId")
    gradle = replace_pattern_once(gradle, code_pattern, lambda m:f"{m.group(1)}{version_code}{m.group(3)}", "versionCode")
    gradle = replace_pattern_once(gradle, name_pattern, lambda m:f'{m.group(1)}"{version}"{m.group(3)}', "versionName")
    gradle = replace_once(gradle, 'resValue("string", "app_name", "Mika Dev")', 'resValue("string", "app_name", "Kami Dev")', "development app label")
    build_file.write_text(gradle, encoding="utf-8")
    strings_root = ROOT / "app/src/main/res"; files = sorted(strings_root.glob("values*/strings.xml")); default = strings_root / "values/strings.xml"
    if default not in files: raise SystemExit("Default app strings were not found")
    for path in files:
        text = path.read_text(encoding="utf-8")
        if path == default: text = replace_pattern_once(text, r'^(\s*<string name="app_name"[^>]*>)[^<]*(</string>\s*)$', r"\1Kami\2", "app_name")
        path.write_text(text.replace("Mika", "Kami"), encoding="utf-8")
    links_path = ROOT / "app/src/main/java/com/wangzan101/mika/about/MikaLinks.kt"; links = links_path.read_text(encoding="utf-8")
    for old,new,label in [
      ('const val REPO = "https://github.com/wangzan101/Mika"',f'const val REPO = "https://github.com/{REPOSITORY}"',"repository URL"),
      ('const val REPO_LABEL = "github.com/wangzan101/Mika"',f'const val REPO_LABEL = "github.com/{REPOSITORY}"',"repository label"),
      ('const val LATEST_RELEASE_API = "https://api.github.com/repos/wangzan101/Mika/releases/latest"',f'const val LATEST_RELEASE_API = "https://api.github.com/repos/{REPOSITORY}/releases/latest"',"update API")]: links=replace_once(links,old,new,label)
    links_path.write_text(links,encoding="utf-8")
    for rel,old,new,label in [
      ("about/UpdateChecker.kt",'.header("User-Agent", "Mika/$currentVersion")','.header("User-Agent", "Kami/$currentVersion")',"update user agent"),
      ("about/ApkUpdater.kt",'.setTitle("Mika ${release.version}")','.setTitle("Kami ${release.version}")',"download notification title")]:
        p=ROOT/"app/src/main/java/com/wangzan101/mika"/rel; p.write_text(replace_once(p.read_text(encoding="utf-8"),old,new,label),encoding="utf-8")
    output=os.environ.get("GITHUB_OUTPUT")
    if output:
      with open(output,"a",encoding="utf-8") as f: f.write(f"version={version}\nversion_code={version_code}\ntag={tag}\n")
    print(f"Prepared Kami {version} ({APP_ID}, versionCode {version_code}).")
if __name__ == "__main__": main()
