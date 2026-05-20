#!/usr/bin/env python3
import os
import re
import csv
import subprocess
from pathlib import Path

# Configuration
THRESHOLDS = [200, 1000, 4000]
NS = [5000000, 10000000, 50000000, 100000000]
# limit to maximum 8 threads
MAX_AVAILABLE = os.cpu_count() or 8
MAX_THREADS = min(MAX_AVAILABLE, 8)
THREADS = list(range(1, MAX_THREADS + 1))
BIN_TEMPLATE = 'quicksort_s{thr}'
MAIN_C = 'main.c'

OUT_CSV = 'scaling_results.csv'

TIME_RE = re.compile(r'Время выполнения:\s*([0-9]+\.?[0-9]*)\s*секунд')


def compile_binary(thr):
    name = BIN_TEMPLATE.format(thr=thr)
    if Path(name).exists():
        return name
    print(f'Compiling {name} (THRESHOLD={thr})...')
    cmd = ['gcc', '-fopenmp', MAIN_C, '-O2', f'-DTHRESHOLD={thr}', '-o', name]
    subprocess.run(cmd, check=True)
    return name


def run_one(binpath, N, threads):
    env = os.environ.copy()
    env['OMP_NUM_THREADS'] = str(threads)
    cmd = [f'./{binpath}', str(N), '1']
    print(f'Running: OMP_NUM_THREADS={threads} {" ".join(cmd)}')
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, check=True, timeout=600)
    except subprocess.CalledProcessError as e:
        print('Program failed:', e)
        print(e.output)
        return None
    except subprocess.TimeoutExpired:
        print('Timeout')
        return None
    out = proc.stdout
    m = TIME_RE.search(out)
    if m:
        return float(m.group(1))
    # fallback: try to find last float in output
    nums = re.findall(r'([0-9]+\.[0-9]+)', out)
    if nums:
        return float(nums[-1])
    return None


def main():
    rows = []
    for thr in THRESHOLDS:
        binname = compile_binary(thr)
        for N in NS:
            for t in THREADS:
                time_s = run_one(binname, N, t)
                if time_s is None:
                    print(f'Run failed for TH={thr} N={N} T={t}')
                    continue
                rows.append({'threshold': thr, 'N': N, 'threads': t, 'time_seconds': time_s})
                # flush to CSV incrementally
                with open(OUT_CSV, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['threshold', 'N', 'threads', 'time_seconds'])
                    writer.writeheader()
                    writer.writerows(rows)
    print('Done. Results in', OUT_CSV)


if __name__ == '__main__':
    main()
