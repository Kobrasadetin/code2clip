from __future__ import annotations
from typing import Dict, Set

# --- Presets Definition ---

NONE = set()

GLOBAL_LEAN = {
    ".git", ".hg", ".svn", ".vscode", ".idea", ".vs", ".cache", "tmp", ".tmp",
    "logs", "coverage", "node_modules", "__pycache__", "dist", "build", "out",
    "bin", "obj", "target", "Debug", "Release"
}

WEB_NODE = GLOBAL_LEAN.union({
    ".next", ".nuxt", ".output", ".vercel", ".expo", ".angular", ".svelte-kit",
    ".parcel-cache", ".webpack", ".rollup.cache", ".turbo", ".nx",
    ".pnpm-store", ".yarn", ".pnp.*", "bower_components"
})

PYTHONIC = GLOBAL_LEAN.union({
    ".venv", "venv", "env", ".env", ".tox", ".nox", ".ipynb_checkpoints",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".eggs", "*.egg-info",
    "_build", "site"
})

JVM_ANDROID = GLOBAL_LEAN.union({
    "target", "build", ".gradle", ".mvn", "app/build", ".cxx", "captures"
})

DOTNET_UNITY = GLOBAL_LEAN.union({
    "x64", "x86", "ARM", "ARM64", "TestResults", "BenchmarkDotNet.Artifacts",
    "Library", "Logs", "Temp", "Obj", "Build", "Builds", "UserSettings"
})

C_CPP_CMAKE = GLOBAL_LEAN.union({
    "cmake-build-*", "CMakeFiles", "CMakeCache.txt", "_deps", ".deps",
    ".conan", "vcpkg_installed", "vcpkg_downloads"
})

APPLE_SWIFT_XCODE = GLOBAL_LEAN.union({
    ".build", "DerivedData", "Pods", "Carthage/Build", "*.xcworkspace",
    "*.xcodeproj"
})

# --- Public API ---

DEFAULT_IGNORE_PRESET = "Global-Lean"

IGNORE_PRESETS: Dict[str, Set[str]] = {
    "None": NONE,
    "Global-Lean": GLOBAL_LEAN,
    "Web/Node": WEB_NODE,
    "Pythonic": PYTHONIC,
    "JVM/Android": JVM_ANDROID,
    ".NET/Unity": DOTNET_UNITY,
    "C/C++/CMake": C_CPP_CMAKE,
    "Apple/Swift/Xcode": APPLE_SWIFT_XCODE,
    "Custom": set()  # "Custom" preset is managed by user text
}

def parse_ignore_list(text: str) -> Set[str]:
    """Converts a comma-separated string into a set of folder names."""
    return {item.strip() for item in text.split(",") if item.strip()}


def get_ignore_set(
    preset_name: str,
    custom_text: str,
    presets: Dict[str, Set[str]] = IGNORE_PRESETS
) -> Set[str]:
    """
    Returns the correct ignore set based on the preset name.
    If the preset is "Custom", it parses the custom text.
    """
    if preset_name == "Custom":
        return parse_ignore_list(custom_text)
    return presets.get(preset_name, presets[DEFAULT_IGNORE_PRESET])
