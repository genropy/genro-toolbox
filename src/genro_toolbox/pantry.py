# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""Pantry — lightweight syntactic sugar over importlib.metadata.

Runtime capability check for optional Python dependencies. Works everywhere —
development, installed packages, Docker containers. No configuration files needed.

Usage via genro_toolbox::

    from genro_toolbox import pantry

    if pantry.has("numpy"):
        import numpy as np

    PIL = pantry["pillow"]          # raise if missing
    np = pantry.get("numpy")        # None if missing

    @pantry("pillow", "numpy")
    def process(path):
        ...
"""

import contextlib
import functools
import importlib
import importlib.metadata
import types
from collections.abc import Callable, Generator


class Pantry:
    """Runtime capability check for any installed Python package.

    Works everywhere — development, installed packages, Docker containers.
    No configuration files needed.
    """

    _UNRESOLVED = object()
    _MISSING = object()

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._lazy: dict[str, object] = {}
        self._hidden: set[str] = set()

    # ------------------------------------------------------------------
    # Core: probe on demand
    # ------------------------------------------------------------------

    def _probe(self, pkg: str) -> dict:
        """Probe a package and cache the result.

        First checks distribution metadata (pip name). If not found,
        falls back to trying a direct import — this handles modules
        installed by other packages (e.g. ``past`` from ``future``).
        """
        if pkg in self._cache:
            return self._cache[pkg]
        dist = self._get_distribution(pkg)
        module_name = self._resolve_module_name(pkg, dist)
        version = None
        available = dist is not None
        if dist is not None:
            with contextlib.suppress(Exception):
                version = dist.metadata["Version"]
        elif self._can_import(module_name):
            available = True
        entry = {
            "pkg_name": pkg,
            "module_name": module_name,
            "module": None,
            "version": version,
            "available": available,
        }
        self._cache[pkg] = entry
        return entry

    def _can_import(self, module_name: str) -> bool:
        """Return ``True`` if *module_name* is importable, without keeping it loaded."""
        try:
            importlib.import_module(module_name)
            return True
        except Exception:
            return False

    def _get_distribution(self, pkg_name: str) -> importlib.metadata.Distribution | None:
        """Return the distribution for *pkg_name*, or ``None``."""
        try:
            return importlib.metadata.distribution(pkg_name)
        except (importlib.metadata.PackageNotFoundError, ValueError):
            return None

    def _resolve_module_name(
        self, pkg_name: str, dist: importlib.metadata.Distribution | None = None
    ) -> str:
        """Map a pip package name to the importable top-level module name."""
        if dist is None:
            return pkg_name.replace("-", "_")

        top_level = dist.read_text("top_level.txt")
        first = next((ln for ln in (top_level or "").splitlines() if ln.strip()), None)
        if first:
            return first.strip()

        if dist.files:
            for fp in dist.files:
                parts = fp.parts
                if len(parts) == 2 and parts[1] == "__init__.py":
                    return parts[0]
            for fp in dist.files:
                parts = fp.parts
                if len(parts) == 1 and fp.suffix == ".py" and not fp.stem.startswith("_"):
                    return fp.stem

        return pkg_name.replace("-", "_")

    def _load_module(self, entry: dict) -> types.ModuleType | None:
        """Import the module for a probe entry. Cached after first call."""
        if entry.get("module") is not None:
            return entry["module"]
        if not entry.get("available"):
            return None
        try:
            mod = importlib.import_module(entry["module_name"])
            entry["module"] = mod
            return mod
        except Exception:
            entry["available"] = False
            return None

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def has(self, *pkgs: str) -> bool:
        """Return ``True`` if all listed packages are installed.

        Uses distribution metadata only — does not import the module::

            pantry.has("numpy")
            pantry.has("numpy", "pandas")  # all must be installed
        """
        return all(
            pkg not in self._hidden and self._probe(pkg).get("available", False)
            for pkg in pkgs
        )

    def get(self, pkg: str, default: object = _MISSING) -> types.ModuleType | None:
        """Return the imported module for *pkg*.

        The module is imported lazily on first access.
        Without *default*, returns ``None`` when unavailable.
        With *default*, returns *default* instead.
        """
        if pkg in self._hidden:
            return None if default is self._MISSING else default
        entry = self._probe(pkg)
        if not entry.get("available"):
            return None if default is self._MISSING else default
        mod = self._load_module(entry)
        if mod is None:
            return None if default is self._MISSING else default
        return mod

    def __getitem__(self, key: str) -> types.ModuleType:
        """Return a module (or lazy-resolved object) for *key*.

        Checks lazy imports first, then installed packages::

            PIL = pantry["pillow"]
            User = pantry["myapp.models.User"]  # if lazy_import'd
        """
        if key in self._lazy:
            obj = self._lazy[key]
            if obj is self._UNRESOLVED:
                obj = self._resolve_lazy(key)
                self._lazy[key] = obj
            return obj

        mod = self.get(key)
        if mod is None:
            raise RuntimeError(
                f"Package '{key}' is not available. "
                f"Install with: pip install {key}"
            )
        return mod

    def version(self, pkg: str) -> str | None:
        """Return the installed version of *pkg*, or ``None``."""
        return self._probe(pkg).get("version")

    # ------------------------------------------------------------------
    # Lazy import (own modules — circular import breaker)
    # ------------------------------------------------------------------

    def lazy_import(self, *paths: str) -> None:
        """Register dotted paths for deferred import.

        Use this for your **own project modules** to break circular imports.
        The actual import happens on first ``pantry["path"]`` access::

            pantry.lazy_import("myapp.models.User", "myapp.db.Session")
            User = pantry["myapp.models.User"]
        """
        for path in paths:
            if path not in self._lazy:
                self._lazy[path] = self._UNRESOLVED

    def _resolve_lazy(self, path: str) -> object:
        """Import and resolve a dotted path."""
        try:
            return importlib.import_module(path)
        except ImportError:
            pass

        dot = path.rfind(".")
        if dot < 0:
            raise RuntimeError(f"Lazy import failed: no module named '{path}'")

        parent_path, attr_name = path[:dot], path[dot + 1 :]
        try:
            parent = importlib.import_module(parent_path)
        except ImportError:
            raise RuntimeError(
                f"Lazy import failed: no module named '{parent_path}'"
            ) from None
        try:
            return getattr(parent, attr_name)
        except AttributeError:
            raise RuntimeError(
                f"Lazy import failed: '{parent_path}' has no attribute '{attr_name}'"
            ) from None

    # ------------------------------------------------------------------
    # Decorator
    # ------------------------------------------------------------------

    def __call__(self, *pkgs: str) -> Callable:
        """Decorator that guards a function behind one or more packages.

        Raises ``RuntimeError`` at call-time when any required package is missing::

            @pantry("pillow", "numpy")
            def process(path):
                ...
        """

        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def wrapper(*args: object, **kwargs: object) -> object:
                missing = [p for p in pkgs if not self.has(p)]
                if missing:
                    raise RuntimeError(
                        f"{fn.__qualname__} requires: {', '.join(missing)}. "
                        f"Install with: pip install {' '.join(missing)}"
                    )
                return fn(*args, **kwargs)

            return wrapper

        return decorator

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def report(self, *pkgs: str) -> str:
        """Return a formatted summary of queried packages.

        Without arguments, reports all packages that have been checked
        in this session. With arguments, probes and reports those packages::

            print(pantry.report())
            print(pantry.report("numpy", "pandas", "pillow"))
        """
        if pkgs:
            for pkg in pkgs:
                self._probe(pkg)
            entries = [self._cache[p] for p in pkgs if p in self._cache]
        else:
            entries = list(self._cache.values())

        lines: list[str] = ["pantry report"]

        if not entries:
            lines.append("(no packages queried)")
            return "\n".join(lines)

        rows: list[tuple[str, str, str, str]] = []
        for entry in entries:
            pkg = str(entry.get("pkg_name", ""))
            module_name = str(entry.get("module_name", pkg))
            ver = str(entry.get("version") or "-")
            ok = "\u2713" if entry.get("available") and pkg not in self._hidden else "\u2717"
            rows.append((pkg, module_name, ver, ok))

        headers = ("package", "module", "version", "ok")
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        COL_SEPARATOR_WIDTH = 2  # "  " between columns
        TABLE_PADDING = 4        # "  " left + right padding
        total_width = sum(col_widths) + COL_SEPARATOR_WIDTH * (len(headers) - 1) + TABLE_PADDING
        sep = "\u2500" * total_width

        lines.append(sep)
        header_line = "  ".join(
            h.ljust(w) for h, w in zip(headers, col_widths, strict=True)
        )
        lines.append(header_line)
        for row in rows:
            lines.append(
                "  ".join(cell.ljust(w) for cell, w in zip(row, col_widths, strict=True))
            )
        lines.append(sep)

        available = sum(1 for r in rows if r[3] == "\u2713")
        lines.append(f"available: {available}/{len(rows)}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        checked = len(self._cache)
        available = sum(1 for e in self._cache.values() if e.get("available"))
        return f"Pantry({available}/{checked} available)"

    # ------------------------------------------------------------------
    # Testing helpers
    # ------------------------------------------------------------------

    @contextlib.contextmanager
    def simulate_missing(self, *pkgs: str) -> Generator[None]:
        """Context manager that temporarily hides packages.

        Useful for testing fallback behavior when optional deps are missing::

            with pantry.simulate_missing("numpy"):
                assert pantry.has("numpy") is False
            # numpy is available again
        """
        self._hidden.update(pkgs)
        try:
            yield
        finally:
            self._hidden.difference_update(pkgs)
