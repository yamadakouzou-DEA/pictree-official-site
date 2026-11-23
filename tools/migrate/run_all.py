import json, sys, urllib.request, concurrent.futures as cf
sys.path.insert(0, "/tmp/gen")
import gen
SITE = gen.SITE
ids = []
for t in ["news", "season", "event"]:
    page = 1
    while True:
        req = urllib.request.Request(f"{SITE}/wp-json/wp/v2/{t}?per_page=100&page={page}&_fields=id", headers=gen.UA)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                batch = json.loads(r.read())
        except Exception:
            break
        if not batch: break
        ids += [(t, b["id"]) for b in batch]
        page += 1
print("total", len(ids), flush=True)
results, errors = [], []
def job(x):
    try: return gen.build(*x)
    except Exception as e: errors.append((x, str(e))); return None
with cf.ThreadPoolExecutor(6) as ex:
    for r in ex.map(job, ids):
        if r: results.append(r)
json.dump(results, open("/tmp/gen/index.json", "w"), ensure_ascii=False, indent=0)
json.dump(errors, open("/tmp/gen/errors.json", "w"), ensure_ascii=False, indent=0)
print("done", len(results), "errors", len(errors), flush=True)
