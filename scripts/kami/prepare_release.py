#!/usr/bin/env python3
"""Apply the Kami app identity and release version to a clean upstream checkout."""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_ID = "com.eighthundreds.kami"
REPOSITORY = "eightHundreds/Kami"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one upstream match, found {count}")
    return text.replace(old, new, 1)


def replace_pattern_once(text: str, pattern: str, replacement, label: str) -> str:
    compiled = re.compile(pattern, re.MULTILINE)
    matches = list(compiled.finditer(text))
    if len(matches) != 1:
        raise SystemExit(f"{label}: expected one upstream match, found {len(matches)}")
    return compiled.sub(replacement, text, count=1)


def main() -> None:
    run_number = int(os.environ["GITHUB_RUN_NUMBER"])
    run_attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
    if run_number < 1 or not 1 <= run_attempt <= 999:
        raise SystemExit("Invalid GitHub Actions run number or attempt.")

    build_file = ROOT / "app/build.gradle.kts"
    gradle = build_file.read_text(encoding="utf-8")

    code_pattern = r"^(\s*versionCode\s*=\s*)(\d+)(\s*)$"
    name_pattern = r'^(\s*versionName\s*=\s*)"([^"]+)"(\s*)$'
    code_match = re.search(code_pattern, gradle, re.MULTILINE)
    name_match = re.search(name_pattern, gradle, re.MULTILINE)
    if not code_match or len(list(re.finditer(code_pattern, gradle, re.MULTILINE))) != 1:
        raise SystemExit("Could not identify exactly one upstream versionCode.")
    if not name_match or len(list(re.finditer(name_pattern, gradle, re.MULTILINE))) != 1:
        raise SystemExit("Could not identify exactly one upstream versionName.")

    upstream_code = int(code_match.group(2))
    upstream_version = name_match.group(2)
    base_version = re.split(r"[-+]", upstream_version, maxsplit=1)[0].lstrip("vV")
    if not re.fullmatch(r"\d+(?:\.\d+)*", base_version):
        raise SystemExit(f"Unsupported upstream versionName: {upstream_version}")

    # Numeric suffixes keep Kami builds newer to the app's version comparator,
    # even when the upstream sync contains commits without a version bump.
    version = f"{base_version}.{run_number}.{run_attempt}"
    version_code = max(upstream_code, 1_000_000) + run_number * 1_000 + run_attempt
    if version_code > 2_100_000_000:
        raise SystemExit("Generated Android versionCode is outside the supported range.")

    gradle = replace_pattern_once(
        gradle,
        r'^(\s*applicationId\s*=\s*)"[^"]+"(\s*)$',
        lambda m: f'{m.group(1)}"{APP_ID}"{m.group(2)}',
        "applicationId",
    )
    gradle = replace_pattern_once(
        gradle,
        code_pattern,
        lambda m: f"{m.group(1)}{version_code}{m.group(3)}",
        "versionCode",
    )
    gradle = replace_pattern_once(
        gradle,
        name_pattern,
        lambda m: f'{m.group(1)}"{version}"{m.group(3)}',
        "versionName",
    )
    gradle = replace_once(
        gradle,
        'resValue("string", "app_name", "Mika Dev")',
        'resValue("string", "app_name", "Kami Dev")',
        "development app label",
    )
    build_file.write_text(gradle, encoding="utf-8")

    strings_root = ROOT / "app/src/main/res"
    string_files = sorted(strings_root.glob("values*/strings.xml"))
    default_strings = strings_root / "values/strings.xml"
    if default_strings not in string_files:
        raise SystemExit("Default app strings were not found.")
    for path in string_files:
        text = path.read_text(encoding="utf-8")
        if path == default_strings:
            text = replace_pattern_once(
                text,
                r'^(\s*<string name="app_name"[^>]*>)[^<]*(</string>\s*)$',
                r"\1Kami\2",
                "app_name",
            )
        text = text.replace("Mika", "Kami")
        path.write_text(text, encoding="utf-8")

    links_path = ROOT / "app/src/main/java/com/wangzan101/mika/about/MikaLinks.kt"
    links = links_path.read_text(encoding="utf-8")
    for old, new, label in [
        ('const val REPO = "https://github.com/wangzan101/Mika"',
         f'const val REPO = "https://github.com/{REPOSITORY}"', "repository URL"),
        ('const val REPO_LABEL = "github.com/wangzan101/Mika"',
         f'const val REPO_LABEL = "github.com/{REPOSITORY}"', "repository label"),
        ('const val LATEST_RELEASE_API = "https://api.github.com/repos/wangzan101/Mika/releases/latest"',
         f'const val LATEST_RELEASE_API = "https://api.github.com/repos/{REPOSITORY}/releases/latest"', "update API"),
    ]:
        links = replace_once(links, old, new, label)
    links_path.write_text(links, encoding="utf-8")

    checker_path = ROOT / "app/src/main/java/com/wangzan101/mika/about/UpdateChecker.kt"
    checker = checker_path.read_text(encoding="utf-8")
    checker = replace_once(
        checker,
        '.header("User-Agent", "Mika/$currentVersion")',
        '.header("User-Agent", "Kami/$currentVersion")',
        "update user agent",
    )
    checker_path.write_text(checker, encoding="utf-8")

    updater_path = ROOT / "app/src/main/java/com/wangzan101/mika/about/ApkUpdater.kt"
    updater = updater_path.read_text(encoding="utf-8")
    updater = replace_once(
        updater,
        '.setTitle("Mika ${release.version}")',
        '.setTitle("Kami ${release.version}")',
        "download notification title",
    )
    updater_path.write_text(updater, encoding="utf-8")

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as file:
            file.write(f"version={version}\n")
            file.write(f"version_code={version_code}\n")
            file.write(f"tag=v{version}\n")
    print(f"Prepared Kami {version} ({APP_ID}, versionCode {version_code}).")


if __name__ == "__main__":
    main()
