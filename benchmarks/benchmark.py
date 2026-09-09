from pathlib import Path
from time import perf_counter
from pixelstrip.core.batch_runner import run_batch

if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("input", type=Path); p.add_argument("output", type=Path)
    p.add_argument("--workers", type=int, default=1); p.add_argument("--backend", default="rembg")
    a=p.parse_args(); t=perf_counter()
    r=run_batch(a.input,a.output,a.backend,a.workers)
    elapsed=perf_counter()-t
    print({"files":len(r),"processed":sum(x["status"]=="processed" for x in r),"failed":sum(x["status"]=="failed" for x in r),"seconds":round(elapsed,3)})
