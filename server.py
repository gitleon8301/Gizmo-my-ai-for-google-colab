# patched server.py
# -----------------
# Usage: BEFORE pasting this file, BACKUP the original server.py to server.py.bak
#        (cp server.py server.py.bak)
#
# This wrapper:
# 1) ensures a compatible Gradio is installed (best-effort)
# 2) monkeypatches theme Base.set to tolerate/ignore unexpected kwargs
# 3) executes the original server.py from server.py.bak so the repo's original behavior continues
#
# NOTE: If you forget to create server.py.bak, this script will exit with instructions.

import os
import sys
import subprocess
import importlib
import inspect
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.join(HERE, "server.py.bak")

def ensure_backup_exists():
    if not os.path.exists(BACKUP):
        print("ERROR: Backup not found:", BACKUP)
        print("Please first back up the original server.py with:")
        print("  cp server.py server.py.bak")
        sys.exit(1)

def pip_install(packages):
    """Run pip install for packages (list or str). Returns True on success, False otherwise."""
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + (packages if isinstance(packages, list) else [packages])
        print("Running:", " ".join(cmd))
        subprocess.check_call(cmd)
        return True
    except Exception as e:
        print("pip install failed:", e)
        return False

def ensure_gradio_pinned():
    """Ensure a compatible Gradio version is available (best-effort)."""
    try:
        import gradio as gr
        ver = getattr(gr, "__version__", None)
        print("Found gradio version:", ver)
        # If version appears incompatible, try to pin. We treat 3.41.2 as compatible.
        if not ver or not ver.startswith("3.41"):
            print("Attempting to pin gradio to 3.41.2 (compatible with this UI).")
            # uninstall possible conflicting packages first (best-effort)
            try:
                subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "gradio", "gradio_client"], check=False)
            except Exception:
                pass
            ok = pip_install(["gradio==3.41.2", "gradio_client==0.5.0"])
            if ok:
                # reload gradio module
                try:
                    import importlib
                    importlib.invalidate_caches()
                    if "gradio" in sys.modules:
                        del sys.modules["gradio"]
                    import gradio as gr2
                    print("Gradio pinned and reloaded, version:", getattr(gr2, "__version__", None))
                except Exception as e:
                    print("Warning: could not reload gradio after install:", e)
            else:
                print("Warning: failed to pin gradio; continuing (may still fail).")
    except Exception:
        # no gradio installed
        print("Gradio not importable; attempting to install the required version.")
        pip_install(["gradio==3.41.2", "gradio_client==0.5.0"])
        # don't necessarily reload; proceed to monkeypatch attempt

def safe_monkeypatch_theme_set():
    """
    Monkeypatch Gradio theme classes' set(...) method so that unexpected keyword arguments are ignored.
    This wraps the original set method and, if it raises TypeError due to unexpected kwargs,
    it filters kwargs to the subset accepted by the original function signature.
    """
    try:
        import gradio
    except Exception as e:
        print("Gradio import failed for monkeypatching:", e)
        return

    tried = []
    def wrap_set(orig):
        def new_set(self, *args, **kwargs):
            try:
                return orig(self, *args, **kwargs)
            except TypeError as e:
                # Attempt to filter kwargs by signature parameters
                try:
                    sig = inspect.signature(orig)
                    allowed = {k: v for k, v in kwargs.items() if k in sig.parameters}
                    return orig(self, *args, **allowed)
                except Exception:
                    # Give original error if filtering fails
                    raise
        return new_set

    # Candidate modules / classes where Base/Theme classes may live across gradio versions
    candidates = [
        ("gradio.themes", "Base"),
        ("gradio.themes", "Theme"),
        ("gradio.themes.base", "Base"),
        ("gradio.themes.base", "Theme"),
        ("gradio.themes.default", "DefaultTheme"),
    ]

    for modpath, clsname in candidates:
        try:
            mod = importlib.import_module(modpath)
            if hasattr(mod, clsname):
                cls = getattr(mod, clsname)
                if hasattr(cls, "set"):
                    try:
                        orig = cls.set
                        cls.set = wrap_set(orig)
                        tried.append(f"{modpath}.{clsname}")
                    except Exception as e:
                        print("Could not wrap", modpath, clsname, ":", e)
        except Exception:
            # module not present in this gradio version; ignore
            continue

    if tried:
        print("Patched theme.set on:", tried)
    else:
        print("No theme class patched (no matching classes found).")

def execute_original_server():
    """Load and exec the backed-up original server.py in the same globals so behavior is preserved."""
    print("Executing original server from backup:", BACKUP)
    with open(BACKUP, "r", encoding="utf-8") as f:
        code = f.read()
    # Execute in a fresh globals dict but preserve common names
    server_globals = {
        "__name__": "__main__",
        "__file__": BACKUP,
        "__package__": None,
        "__cached__": None,
        "__doc__": None,
    }
    # copy current environment variables in case original relies on them
    server_globals.update(globals())
    try:
        exec(compile(code, BACKUP, "exec"), server_globals)
    except SystemExit:
        # allow normal sys.exit from original to terminate
        raise
    except Exception:
        print("ERROR: original server crashed after compatibility fixes. Traceback below:")
        traceback.print_exc()
        # propagate error code
        sys.exit(1)

def main():
    ensure_backup_exists()
    # Step 1: ensure a compatible gradio is available (best-effort)
    ensure_gradio_pinned()
    # Step 2: apply monkeypatch to tolerate unexpected theme kwargs
    safe_monkeypatch_theme_set()
    # Step 3: execute original server main logic from backup
    execute_original_server()

if __name__ == "__main__":
    main()
