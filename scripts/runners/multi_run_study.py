"""
Multi-Run Occupancy Study
Chạy kịch bản generic nhiều lần với occupancy ngẫu nhiên khác nhau mỗi lần.
Mục tiêu: chứng minh sự biến động của sensor data theo số người.
"""

import os
import sys
import random
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

# Add scripts to path
sys.path.append(str(Path(__file__).parent.parent))

from generators.idf_generator import IDFGenerator
from runners.run_simulation import EnergyPlusRunner
from parsers.result_parser import ResultParser
from utils.helpers import setup_logging, get_project_root, load_json, ensure_dir


class MultiRunStudy:
    """
    Chạy nhiều lần mô phỏng với occupancy schedule ngẫu nhiên,
    thu thập kết quả và vẽ biểu đồ so sánh.
    """

    def __init__(self, scenario_path: str, n_runs: int = 10,
                 energyplus_path: str = None, seed: int = None):
        """
        Args:
            scenario_path: Đường dẫn đến file scenario JSON
            n_runs: Số lần chạy mô phỏng
            energyplus_path: Đường dẫn EnergyPlus (optional)
            seed: Random seed (optional, để tái lập kết quả)
        """
        self.logger = setup_logging()
        self.project_root = get_project_root()
        self.scenario_path = scenario_path
        self.n_runs = n_runs
        self.runner = EnergyPlusRunner(energyplus_path=energyplus_path)
        self.parser = ResultParser()

        if seed is not None:
            random.seed(seed)

        # Load scenario
        self.scenario = load_json(scenario_path)
        self.scenario_name = self.scenario['scenario_name']

        # Đọc cấu hình occupancy từ scenario
        dist = (self.scenario
                .get('overrides', {})
                .get('schedules', {})
                .get('occupancy_schedule', {})
                .get('distribution', {}))

        self.base_occupancy = dist.get('base_occupancy', 8)
        self.base_probability = dist.get('base_probability', 0.6)
        self.random_range = dist.get('random_range', [8, 12])
        self.max_occupants = (self.scenario
                              .get('overrides', {})
                              .get('schedules', {})
                              .get('occupancy_data', {})
                              .get('max_occupants', 12))

        # Thư mục lưu kết quả study — mỗi lần chạy tạo 1 folder timestamp riêng
        # → tất cả IDF + output + chart gom vào 1 nơi, không bừa
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.study_dir = (self.project_root / 'outputs' / 'multi_run_study'
                         / f'study_{timestamp}')
        ensure_dir(str(self.study_dir))

        self.logger.info(
            f"MultiRunStudy: {n_runs} lần chạy | "
            f"base={self.base_occupancy}người ({self.base_probability*100:.0f}%) | "
            f"random={self.random_range[0]}-{self.random_range[1]}người ({(1-self.base_probability)*100:.0f}%)"
        )

    # ------------------------------------------------------------------
    # Tạo schedule ngẫu nhiên cho mỗi lần chạy
    # ------------------------------------------------------------------
    def _generate_random_occupancy_schedule(self) -> Dict[str, float]:
        """
        Tạo occupancy fraction cho từng giờ trong ngày làm việc.
        Theo pattern: 60% base_occupancy, 40% random trong random_range.
        Trả về dict: {hour_str: fraction}
        """
        working_hours = list(range(8, 18))  # 8h-17h
        schedule = {}

        hourly_occupants = []
        for h in working_hours:
            if random.random() < self.base_probability:
                n = self.base_occupancy
            else:
                n = random.randint(self.random_range[0], self.random_range[1])
            hourly_occupants.append(n)
            schedule[str(h)] = round(n / self.max_occupants, 4)

        # Ngoài giờ làm việc = 0
        for h in list(range(0, 8)) + list(range(18, 24)):
            schedule[str(h)] = 0.0

        return schedule, hourly_occupants

    def _build_idf_with_custom_schedule(self, schedule: Dict[str, float],
                                        run_id: int,
                                        run_output_dir: Path) -> str:
        """
        Tạo IDF với occupancy schedule tùy chỉnh cho lần chạy run_id.
        IDF được lưu trực tiếp vào run_output_dir để gom tất cả file của 1 run vào 1 nơi.
        Trả về đường dẫn IDF.
        """
        # Tạo generator từ scenario gốc
        generator = IDFGenerator(self.scenario_path)

        # Patch occupancy schedule và max_occupants
        generator.schedules['occupancy_data']['max_occupants'] = self.max_occupants

        # Ghi đè _generate_schedules để inject schedule mới
        original_generate_schedules = generator._generate_schedules

        def patched_schedules():
            sched_list = original_generate_schedules()

            # Tìm và thay thế Occupancy_Schedule
            new_occ_fields = []
            new_occ_fields.append("  Through: 12/31,          !- Field 1")
            new_occ_fields.append("  For: Weekdays,           !- Field 2")

            field_idx = 3
            for h in range(0, 24):
                frac = schedule.get(str(h), 0.0)
                until_time = f"{h+1:02d}:00"
                new_occ_fields.append(
                    f"  Until: {until_time}, {frac:.4f},       !- Field {field_idx}"
                )
                field_idx += 2

            new_occ_fields.append("  For: Weekend,            !- Field 49")
            new_occ_fields.append("  Until: 24:00, 0.0,       !- Field 50")
            new_occ_fields.append("  For: AllOtherDays,       !- Field 51")
            new_occ_fields.append("  Until: 24:00, 0.0;       !- Field 52")

            occ_schedule = (
                "Schedule:Compact,\n"
                "  Occupancy_Schedule,      !- Name\n"
                "  Fraction,                !- Schedule Type Limits Name\n"
                + "\n".join(new_occ_fields)
            )

            # Replace cái cũ
            final_list = []
            for s in sched_list:
                if 'Occupancy_Schedule' in s and 'Schedule:Compact' in s:
                    final_list.append(occ_schedule)
                else:
                    final_list.append(s)
            return final_list

        generator._generate_schedules = patched_schedules

        # Lưu IDF vào cùng folder với output của run này (thay vì outputs/idf/)
        idf_path = run_output_dir / f"{self.scenario_name}_run{run_id:03d}.idf"
        generator.generate_idf(output_path=str(idf_path))
        return str(idf_path)

    # ------------------------------------------------------------------
    # Chạy một lần mô phỏng
    # ------------------------------------------------------------------
    def _run_one(self, run_id: int) -> Dict:
        """Thực hiện 1 lần mô phỏng và trả về metrics tóm tắt."""
        self.logger.info(f"--- Run {run_id}/{self.n_runs} ---")

        # Tạo folder cho run này TRƯỚC — IDF và output đều nằm ở đây
        run_output_dir = self.study_dir / f"run_{run_id:03d}"
        ensure_dir(str(run_output_dir))

        # Tạo schedule ngẫu nhiên
        schedule, hourly_occupants = self._generate_random_occupancy_schedule()
        avg_occ = round(sum(hourly_occupants) / len(hourly_occupants), 2)
        max_occ = max(hourly_occupants)

        self.logger.info(
            f"Run {run_id}: avg_occupants={avg_occ}, max={max_occ}, "
            f"pattern={hourly_occupants}"
        )

        # Build IDF — lưu thẳng vào run_output_dir
        idf_path = self._build_idf_with_custom_schedule(schedule, run_id, run_output_dir)

        # Weather file
        weather_file_name = self.scenario.get('weather_file', 'VNM_Ho.Chi.Minh.488500_IWEC.epw')
        weather_file = self.project_root / 'data' / 'weather' / weather_file_name

        if not weather_file.exists():
            self.logger.error(f"Weather file không tìm thấy: {weather_file}")
            return None

        # Chạy mô phỏng (output cũng vào run_output_dir)
        start_t = time.time()
        result = self.runner.run_simulation(
            idf_path=idf_path,
            weather_file=str(weather_file),
            output_dir=str(run_output_dir),
            scenario_name=f"{self.scenario_name}_run{run_id:03d}"
        )
        elapsed = round(time.time() - start_t, 1)

        # Parse kết quả
        csv_path = os.path.join(run_output_dir, 'eplusout.csv')
        if not os.path.exists(csv_path):
            self.logger.warning(f"Run {run_id}: CSV không tồn tại!")
            return None

        df = self.parser.parse_csv_output(csv_path)

        # Extract metrics
        temp_cols = [c for c in df.columns if 'Zone Mean Air Temperature' in c]
        hum_cols = [c for c in df.columns if 'Zone Air Relative Humidity' in c]
        co2_cols = [c for c in df.columns if 'Zone Air CO2 Concentration' in c]
        light_cols = [c for c in df.columns if 'Zone Lights Electric Power' in c]
        cooling_cols = [c for c in df.columns if 'Zone Ideal Loads Supply Air Total Cooling Energy' in c]

        metrics = {
            'run_id': run_id,
            'avg_occupants': avg_occ,
            'max_occupants_in_run': max_occ,
            'occupancy_pattern': str(hourly_occupants),
            'elapsed_sec': elapsed,
        }

        if temp_cols:
            metrics['avg_temp_C'] = round(df[temp_cols[0]].mean(), 3)
            metrics['max_temp_C'] = round(df[temp_cols[0]].max(), 3)
        if hum_cols:
            metrics['avg_humidity_pct'] = round(df[hum_cols[0]].mean(), 3)
        if co2_cols:
            metrics['avg_co2_ppm'] = round(df[co2_cols[0]].mean(), 3)
            metrics['max_co2_ppm'] = round(df[co2_cols[0]].max(), 3)
        if light_cols:
            metrics['avg_light_W'] = round(df[light_cols[0]].mean(), 3)
        if cooling_cols:
            metrics['total_cooling_kWh'] = round(df[cooling_cols[0]].sum() / 3_600_000, 3)

        # Lưu sensor CSV của run này
        self.parser.export_sensor_csv(
            df, str(run_output_dir), f"{self.scenario_name}_run{run_id:03d}"
        )

        # Lưu schedule của run này
        with open(run_output_dir / 'occupancy_schedule.json', 'w') as f:
            json.dump({
                'run_id': run_id,
                'hourly_occupants': hourly_occupants,
                'schedule_fraction': schedule
            }, f, indent=2)

        self.logger.info(
            f"Run {run_id} ✓ | "
            f"temp={metrics.get('avg_temp_C','?')}°C | "
            f"CO2={metrics.get('avg_co2_ppm','?')}ppm | "
            f"time={elapsed}s"
        )

        return metrics

    # ------------------------------------------------------------------
    # Chạy toàn bộ study
    # ------------------------------------------------------------------
    def run(self) -> pd.DataFrame:
        """Chạy toàn bộ N lần và trả về DataFrame kết quả."""
        print(f"\n{'='*70}")
        print(f"  MULTI-RUN OCCUPANCY STUDY: {self.n_runs} lần")
        print(f"  Kịch bản: {self.scenario_name}")
        print(f"  Occupancy: base={self.base_occupancy}ng ({self.base_probability*100:.0f}%), "
              f"random={self.random_range[0]}-{self.random_range[1]}ng ({(1-self.base_probability)*100:.0f}%)")
        print(f"{'='*70}\n")

        all_metrics = []
        for i in range(1, self.n_runs + 1):
            try:
                m = self._run_one(i)
                if m:
                    all_metrics.append(m)
                    print(f"  ✓ Run {i:02d}/{self.n_runs} | "
                          f"avg_occ={m['avg_occupants']} | "
                          f"temp={m.get('avg_temp_C','?')}°C | "
                          f"CO2={m.get('avg_co2_ppm','?')}ppm")
            except Exception as e:
                self.logger.error(f"Run {i} thất bại: {e}")
                print(f"  ✗ Run {i:02d} - LỖI: {e}")

        if not all_metrics:
            print("\nKhông có kết quả nào!")
            return pd.DataFrame()

        df = pd.DataFrame(all_metrics)

        # Lưu file historical tổng hợp
        hist_path = self.study_dir / 'historical_results.csv'
        df.to_csv(hist_path, index=False)
        print(f"\n✓ Đã lưu kết quả: {hist_path}")

        # In thống kê tóm tắt
        self._print_summary(df)

        # Vẽ biểu đồ
        plot_path = self._plot_results(df)
        print(f"✓ Đã lưu biểu đồ: {plot_path}")

        return df

    # ------------------------------------------------------------------
    # In tóm tắt
    # ------------------------------------------------------------------
    def _print_summary(self, df: pd.DataFrame):
        print(f"\n{'='*70}")
        print("  THỐNG KÊ TỔNG HỢP")
        print(f"{'='*70}")
        metrics_to_show = ['avg_temp_C', 'avg_humidity_pct', 'avg_co2_ppm',
                           'max_co2_ppm', 'avg_light_W', 'total_cooling_kWh']
        for col in metrics_to_show:
            if col in df.columns:
                print(f"  {col:25s} | "
                      f"min={df[col].min():.2f} | "
                      f"max={df[col].max():.2f} | "
                      f"mean={df[col].mean():.2f} | "
                      f"std={df[col].std():.3f}")
        print(f"{'='*70}\n")

    # ------------------------------------------------------------------
    # Vẽ biểu đồ so sánh
    # ------------------------------------------------------------------
    def _plot_results(self, df: pd.DataFrame) -> str:
        """Vẽ biểu đồ so sánh các lần chạy."""
        n = len(df)
        run_ids = df['run_id'].tolist()
        x = np.arange(n)

        # Màu gradient theo số người trung bình
        occ_vals = df['avg_occupants'].values
        norm = plt.Normalize(occ_vals.min(), occ_vals.max())
        cmap = plt.cm.YlOrRd

        # ---- Layout -----
        fig = plt.figure(figsize=(18, 14), facecolor='#0F1117')
        fig.suptitle(
            f'So sánh {n} lần mô phỏng — Kịch bản: {self.scenario_name}\n'
            f'Occupancy: base={self.base_occupancy} người ({self.base_probability*100:.0f}%), '
            f'random={self.random_range[0]}-{self.random_range[1]} người ({(1-self.base_probability)*100:.0f}%)',
            fontsize=14, color='white', y=0.98, fontweight='bold'
        )

        gs = gridspec.GridSpec(3, 2, figure=fig,
                               hspace=0.55, wspace=0.35,
                               left=0.07, right=0.97,
                               top=0.92, bottom=0.07)

        axes_config = [
            (gs[0, 0], 'avg_temp_C',        'Nhiệt độ TB (°C)',      '#FF6B6B', '°C'),
            (gs[0, 1], 'avg_humidity_pct',   'Độ ẩm TB (%)',          '#4ECDC4', '%'),
            (gs[1, 0], 'avg_co2_ppm',        'CO2 TB (ppm)',          '#FFE66D', 'ppm'),
            (gs[1, 1], 'max_co2_ppm',        'CO2 Đỉnh (ppm)',        '#FF9F43', 'ppm'),
            (gs[2, 0], 'avg_light_W',        'Công suất đèn TB (W)',  '#A29BFE', 'W'),
            (gs[2, 1], 'total_cooling_kWh',  'Tổng năng lượng làm lạnh (kWh)', '#55EFC4', 'kWh'),
        ]

        for gs_loc, col, title, color, unit in axes_config:
            if col not in df.columns:
                continue

            ax = fig.add_subplot(gs_loc)
            ax.set_facecolor('#1A1D27')

            values = df[col].values

            # Bars với gradient theo occupancy
            colors_bar = [cmap(norm(o)) for o in occ_vals]
            bars = ax.bar(x, values, color=colors_bar, edgecolor='none',
                          width=0.7, zorder=3)

            # Đường trung bình
            mean_val = values.mean()
            ax.axhline(mean_val, color=color, linewidth=1.5,
                       linestyle='--', alpha=0.8, zorder=4,
                       label=f'Trung bình: {mean_val:.2f} {unit}')

            # Dải ± std
            std_val = values.std()
            ax.axhspan(mean_val - std_val, mean_val + std_val,
                       alpha=0.1, color=color, zorder=2)

            # Style
            ax.set_title(title, color='white', fontsize=11, fontweight='bold', pad=8)
            ax.set_xlabel('Lần chạy (Run ID)', color='#AAAAAA', fontsize=9)
            ax.set_ylabel(unit, color='#AAAAAA', fontsize=9)
            ax.set_xticks(x)
            ax.set_xticklabels([f'R{r}' for r in run_ids],
                               color='#CCCCCC', fontsize=8, rotation=45)
            ax.tick_params(colors='#CCCCCC')
            ax.spines[:].set_color('#333344')
            ax.grid(axis='y', color='#333344', linestyle='--', alpha=0.5, zorder=1)
            ax.legend(fontsize=8, labelcolor='white',
                      facecolor='#1A1D27', edgecolor='#333344')

            # Annotate min/max
            min_idx = np.argmin(values)
            max_idx = np.argmax(values)
            ax.annotate(f'min\n{values[min_idx]:.1f}',
                        xy=(x[min_idx], values[min_idx]),
                        xytext=(0, -18), textcoords='offset points',
                        color='#88DDFF', fontsize=7, ha='center')
            ax.annotate(f'max\n{values[max_idx]:.1f}',
                        xy=(x[max_idx], values[max_idx]),
                        xytext=(0, 5), textcoords='offset points',
                        color='#FF6B6B', fontsize=7, ha='center')

        # Colorbar chú thích occupancy
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar_ax = fig.add_axes([0.92, 0.25, 0.015, 0.5])
        cbar = fig.colorbar(sm, cax=cbar_ax)
        cbar.set_label('Số người TB/giờ', color='white', fontsize=9)
        cbar.ax.yaxis.set_tick_params(color='white')
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white', fontsize=8)

        # Lưu
        plot_path = self.study_dir / 'comparison_chart.png'
        fig.savefig(str(plot_path), dpi=150, bbox_inches='tight',
                    facecolor='#0F1117')
        plt.close(fig)

        # Vẽ thêm biểu đồ scatter: occupancy vs CO2/Temp
        self._plot_scatter(df)

        return str(plot_path)

    def _plot_scatter(self, df: pd.DataFrame):
        """Vẽ scatter plot: số người trung bình vs các chỉ số."""
        if 'avg_occupants' not in df.columns:
            return

        targets = []
        if 'avg_co2_ppm' in df.columns:
            targets.append(('avg_co2_ppm', 'CO2 TB (ppm)', '#FFE66D', False))
        if 'avg_temp_C' in df.columns:
            targets.append(('avg_temp_C', 'Nhiệt độ TB (°C)', '#FF6B6B', True))  # True = is_temp
        if 'total_cooling_kWh' in df.columns:
            targets.append(('total_cooling_kWh', 'Năng lượng làm lạnh (kWh)', '#55EFC4', False))

        if not targets:
            return

        fig, axes = plt.subplots(1, len(targets), figsize=(6 * len(targets), 5),
                                 facecolor='#0F1117')
        if len(targets) == 1:
            axes = [axes]

        fig.suptitle('Tương quan: Số người → Chỉ số môi trường',
                     color='white', fontsize=13, fontweight='bold')

        x = df['avg_occupants'].values

        for ax, (col, ylabel, color, is_temp) in zip(axes, targets):
            y = df[col].values
            ax.set_facecolor('#1A1D27')

            ax.scatter(x, y, color=color, s=80, alpha=0.85, zorder=3,
                       edgecolors='white', linewidths=0.5)

            # Trend line
            if len(x) > 1:
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                x_line = np.linspace(x.min(), x.max(), 100)
                ax.plot(x_line, p(x_line), '--', color=color,
                        alpha=0.6, linewidth=1.5, zorder=4,
                        label=f'Trend: y={z[0]:.4f}x+{z[1]:.3f}')

            # Annotate points
            for i, (xi, yi, rid) in enumerate(zip(x, y, df['run_id'])):
                ax.annotate(f'R{rid}', (xi, yi),
                            textcoords='offset points', xytext=(4, 4),
                            color='#CCCCCC', fontsize=7)

            ax.set_xlabel('Số người TB / giờ làm việc', color='#AAAAAA', fontsize=10)
            ax.set_ylabel(ylabel, color='#AAAAAA', fontsize=10)
            ax.set_title(f'Occupancy → {ylabel}', color='white',
                         fontsize=11, fontweight='bold')
            ax.tick_params(colors='#CCCCCC')
            ax.spines[:].set_color('#333344')
            ax.grid(color='#333344', linestyle='--', alpha=0.5)

            # ---- Xử lý đặc biệt cho biểu đồ NHIỆT ĐỘ ----
            if is_temp:
                mean_y = y.mean()
                spread = max(y.max() - y.min(), 0.01)  # tối thiểu 0.01°C để thấy rõ

                # Mở rộng trục Y để thấy dao động nhỏ
                ax.set_ylim(mean_y - spread * 5, mean_y + spread * 5)

                # Hiển thị số thực, không dùng offset (+2.163e1)
                ax.yaxis.set_major_formatter(
                    plt.matplotlib.ticker.FormatStrFormatter('%.3f')
                )

                # Chú thích giải thích tại sao phẳng
                ax.text(0.5, 0.06,
                        '⚠ HVAC giữ nhiệt độ cố định\n'
                        'Số người ảnh hưởng đến tải lạnh,\n'
                        'không phải nhiệt độ phòng.',
                        transform=ax.transAxes,
                        color='#FFCC00', fontsize=7.5,
                        ha='center', va='bottom',
                        bbox=dict(boxstyle='round,pad=0.4',
                                  facecolor='#252535',
                                  edgecolor='#FFCC00',
                                  alpha=0.85))

            ax.legend(fontsize=8, facecolor='#1A1D27',
                      edgecolor='#333344', labelcolor='white')

        plt.tight_layout()
        scatter_path = self.study_dir / 'scatter_occupancy_vs_metrics.png'
        fig.savefig(str(scatter_path), dpi=150, bbox_inches='tight',
                    facecolor='#0F1117')
        plt.close(fig)
        print(f"✓ Đã lưu scatter plot: {scatter_path}")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
if __name__ == '__main__':
    import argparse

    ap = argparse.ArgumentParser(
        description='Chạy nhiều lần mô phỏng với occupancy ngẫu nhiên'
    )
    ap.add_argument('--scenario',
                    default='config/scenarios/generic_scenario.json',
                    help='Đường dẫn file scenario JSON')
    ap.add_argument('--runs', type=int, default=5,
                    help='Số lần chạy mô phỏng (mặc định: 5)')
    ap.add_argument('--energyplus-path', default=None,
                    help='Đường dẫn EnergyPlus executable')
    ap.add_argument('--seed', type=int, default=None,
                    help='Random seed (optional)')
    args = ap.parse_args()

    project_root = Path(__file__).parent.parent.parent
    scenario_path = project_root / args.scenario
    if not scenario_path.exists():
        print(f"Không tìm thấy scenario: {scenario_path}")
        sys.exit(1)

    study = MultiRunStudy(
        scenario_path=str(scenario_path),
        n_runs=args.runs,
        energyplus_path=args.energyplus_path,
        seed=args.seed
    )

    results_df = study.run()

    if not results_df.empty:
        print("\n📊 KẾT QUẢ TỔNG HỢP:")
        print(results_df[['run_id', 'avg_occupants', 'avg_temp_C',
                           'avg_humidity_pct', 'avg_co2_ppm',
                           'total_cooling_kWh']].to_string(index=False))
