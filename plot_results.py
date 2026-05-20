#!/usr/bin/env python3
"""
plot_results.py

Читает `scaling_results.csv`, строит графики времени и ускорения (PNG + SVG)
и выводит краткую сводку по результатам (лучший порог для каждого N и макс ускорение).

Требования: pandas, matplotlib. Установите через:
    python3 -m pip install --user pandas matplotlib

Запуск:
    python3 plot_results.py

Файлы на выходе: scaling_time.png, scaling_speedup.png, scaling_time.svg, scaling_speedup.svg
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def read_results(path: Path):
    if not path.exists():
        print(f'Файл {path} не найден', file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(path)
    return df


def compute_speedup(df: pd.DataFrame):
    # baseline time for threads==1 for each (threshold, N)
    baselines = df[df['threads'] == 1].set_index(['threshold', 'N'])['time_seconds']
    def sp(row):
        return baselines.loc[(row['threshold'], row['N'])] / row['time_seconds']
    df['speedup'] = df.apply(sp, axis=1)
    return df


def plot_and_save(df: pd.DataFrame, out_png: str, out_svg: str, metric: str, ylabel: str, title: str, add_ideal=False):
    plt.figure(figsize=(10, 6))
    for thr in sorted(df['threshold'].unique()):
        s = df[(df['threshold'] == thr)].sort_values('threads')
        # if metric is time_seconds, multiple N will overlap; caller should pass df filtered per N
        plt.plot(s['threads'], s[metric], marker='o', label=f'TH={thr}')

    if add_ideal:
        threads = sorted(df['threads'].unique())
        plt.plot(threads, threads, color='k', linestyle='--', label='Линейное ускорение')

    plt.xlabel('Число потоков')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(loc='best', fontsize='small')
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.savefig(out_svg)
    plt.close()
    print(f'Saved {out_png} and {out_svg}')


def plot_all_n(df: pd.DataFrame, out_png: str, out_svg: str, metric: str, ylabel: str, title: str, add_ideal=False):
    plt.figure(figsize=(12, 7))
    for thr in sorted(df['threshold'].unique()):
        for n in sorted(df['N'].unique()):
            s = df[(df['threshold'] == thr) & (df['N'] == n)].sort_values('threads')
            label = f'TH={thr} N={n}'
            plt.plot(s['threads'], s[metric], marker='o', label=label)

    if add_ideal and metric == 'speedup':
        threads = sorted(df['threads'].unique())
        plt.plot(threads, threads, color='k', linestyle='--', label='Линейное ускорение')

    plt.xlabel('Число потоков')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(loc='best', fontsize='small')
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.savefig(out_svg)
    plt.close()
    print(f'Saved {out_png} and {out_svg}')


def summarize(df: pd.DataFrame):
    # For each N find threshold with best speedup at max threads
    max_threads = df['threads'].max()
    summary_lines = []
    for n in sorted(df['N'].unique()):
        sub_n = df[df['N'] == n]
        best_row = sub_n[sub_n['threads'] == max_threads].sort_values('speedup', ascending=False).iloc[0]
        best_thr = best_row['threshold']
        best_speedup = best_row['speedup']
        baseline_time = sub_n[sub_n['threads'] == 1]['time_seconds'].iloc[0]
        par_time = best_row['time_seconds']
        summary_lines.append((n, best_thr, best_speedup, baseline_time, par_time))

    print('\nSummary:')
    print('N\tBest_TH\tSpeedup@Tmax\tTime@1T(s)\tTime@Tmax(s)')
    for n, thr, spd, t1, tmax in summary_lines:
        print(f'{n}\t{thr}\t{spd:.2f}\t\t{t1:.6f}\t{tmax:.6f}')

    # Global notes
    avg_speedups = df.groupby(['threshold'])['speedup'].mean()
    print('\nAverage speedup by threshold (all N, all threads):')
    for thr, avg in avg_speedups.items():
        print(f'  TH={thr}: {avg:.3f}')


def main():
    csv_path = Path('scaling_results.csv')
    df = read_results(csv_path)
    df = compute_speedup(df)

    # Показываем только выбранные пороги и исключаем N=50000000
    selected_thresholds = [200, 1000, 200000]
    df = df[df['threshold'].isin(selected_thresholds)]
    df = df[df['N'] != 50000000]

    # Для каждого N создаём отдельные графики времени и ускорения
    for n in sorted(df['N'].unique()):
        df_n = df[df['N'] == n]
        png_time = f'scaling_time_N{n}.png'
        svg_time = f'scaling_time_N{n}.svg'
        plot_and_save(df_n, png_time, svg_time, metric='time_seconds', ylabel='Время выполнения (с)', title=f'Время выполнения, N={n}')

        png_sp = f'scaling_speedup_N{n}.png'
        svg_sp = f'scaling_speedup_N{n}.svg'
        plot_and_save(df_n, png_sp, svg_sp, metric='speedup', ylabel='Ускорение', title=f'Ускорение, N={n}', add_ideal=True)

    # Общие графики по всем N
    plot_all_n(df, 'scaling_time_allN.png', 'scaling_time_allN.svg', metric='time_seconds', ylabel='Время выполнения (с)', title='Время выполнения для всех N')
    plot_all_n(df, 'scaling_speedup_allN.png', 'scaling_speedup_allN.svg', metric='speedup', ylabel='Ускорение', title='Ускорение для всех N', add_ideal=True)

    # Дополнительно: общая таблица-резюме
    summarize(df)


if __name__ == '__main__':
    main()
