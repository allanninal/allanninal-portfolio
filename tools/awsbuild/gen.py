"""Render every spec under specs/ into /build, then rebuild the derived files."""
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from awsbuild import build_all, registry, series, thumbs  # noqa: E402
from awsbuild.apply_offers import block as offer_block  # noqa: E402


def load_specs():
    out = []
    for f in sorted((HERE / "specs").glob("day*.py")):
        spec = importlib.util.spec_from_file_location(f.stem, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out.append(mod.SPEC)
    return out


def related_for(reg, specs, slug):
    """Nine other series to cross-link from a series index."""
    pool = [{"slug": s["slug"], "name": s["name"], "tagline": s["tagline"]}
            for s in specs if s["slug"] != slug]
    pool += [{"slug": e["slug"], "name": e["name"], "tagline": e["tagline"]}
             for e in reg.values() if e["slug"] != slug]
    step = max(1, len(pool) // 9)
    return pool[::step][:9]


def main(only=None):
    reg = registry.load()
    specs = [s for s in load_specs() if not only or s["slug"] in only]
    if not specs:
        print("no specs")
        return
    for spec in specs:
        assert len(spec["parts"]) == 7, f"{spec['slug']}: {len(spec['parts'])} parts"
        ob = offer_block(spec["slug"])
        series.write(spec, related_for(reg, load_specs(), spec["slug"]), ob)
        thumbs.write(spec["slug"], spec["name"], spec.get("icons", []))
        reg[spec["slug"]] = {"slug": spec["slug"], "name": spec["name"],
                             "tagline": spec["tagline"], "date": spec["date"],
                             "parts": [{"slug": p["slug"], "title": p["title"]}
                                       for p in spec["parts"]]}
        print("wrote", spec["slug"], spec["date"])
    registry.save(reg)
    build_all.main()


if __name__ == "__main__":
    main(sys.argv[1:] or None)
