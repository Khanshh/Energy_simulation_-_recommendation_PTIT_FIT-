"""
Parse EnergyPlus simulation results and generate reports
"""

import os
import sys
from pathlib import Path
import pandas as pd
import json
from typing import Dict, List
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

sys.path.append(str(Path(__file__).parent.parent))

from utils.helpers import setup_logging, get_project_root, ensure_dir


class ResultParser:
    """Parse and analyze EnergyPlus simulation results"""
    
    def __init__(self):
        """Initialize Result Parser"""
        self.logger = setup_logging()
        self.project_root = get_project_root()
    
    def parse_csv_output(self, csv_path: str) -> pd.DataFrame:
        """
        Parse EnergyPlus CSV output file
        
        Args:
            csv_path: Path to eplusout.csv file
            
        Returns:
            Pandas DataFrame with results
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self.logger.info(f"Parsing CSV: {csv_path}")
        
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Convert Date/Time to datetime if exists
        if 'Date/Time' in df.columns:
            def parse_ep_datetime(dt_str):
                try:
                    # EnergyPlus format: " 01/01  01:00:00"
                    dt_str = dt_str.strip()
                    parts = dt_str.split(' ')
                    date_part = parts[0]
                    time_part = parts[-1]
                    
                    month, day = map(int, date_part.split('/'))
                    hour, minute, second = map(int, time_part.split(':'))
                    
                    # Handle 24:00:00 as 00:00:00 of next day
                    year = 2024  # Default to 2024 as per scenario
                    if hour == 24:
                        dt = pd.Timestamp(year=year, month=month, day=day, hour=0, minute=minute, second=second)
                        dt = dt + pd.Timedelta(days=1)
                    else:
                        dt = pd.Timestamp(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
                    return dt
                except:
                    return pd.NaT

            df['DateTime'] = df['Date/Time'].apply(parse_ep_datetime)
        
        return df
    
    def export_sensor_csv(self, df: pd.DataFrame, output_dir: str, scenario_name: str) -> str:
        """
        Export a clean CSV with the 4 sensor columns:
        DateTime, Nhiệt độ (°C), Độ ẩm (%), Ánh sáng (W), CO2 (ppm)

        Args:
            df: DataFrame parsed from EnergyPlus CSV output
            output_dir: Directory to save the file
            scenario_name: Name of scenario (used in filename)

        Returns:
            Path to the exported CSV file
        """
        ensure_dir(output_dir)

        # --- Nhiệt độ ---
        temp_cols = [col for col in df.columns if 'Zone Mean Air Temperature' in col]
        # --- Độ ẩm ---
        humidity_cols = [col for col in df.columns if 'Zone Air Relative Humidity' in col]
        # --- Ánh sáng (Electric Power of Lights, Watts) ---
        light_cols = [col for col in df.columns if 'Zone Lights Electric Power' in col]
        # --- CO2 (ppm) ---
        co2_cols = [col for col in df.columns if 'Zone Air CO2 Concentration' in col]

        sensor_df = pd.DataFrame()

        if 'DateTime' in df.columns:
            sensor_df['DateTime'] = df['DateTime']
        elif 'Date/Time' in df.columns:
            sensor_df['DateTime'] = df['Date/Time']

        if temp_cols:
            sensor_df['Nhiet_do_C'] = df[temp_cols[0]]
        else:
            sensor_df['Nhiet_do_C'] = None
            self.logger.warning("Không tìm thấy cột Nhiệt độ trong CSV")

        if humidity_cols:
            sensor_df['Do_am_pct'] = df[humidity_cols[0]]
        else:
            sensor_df['Do_am_pct'] = None
            self.logger.warning("Không tìm thấy cột Độ ẩm trong CSV")

        if light_cols:
            sensor_df['Anh_sang_W'] = df[light_cols[0]]
        else:
            sensor_df['Anh_sang_W'] = None
            self.logger.warning("Không tìm thấy cột Ánh sáng trong CSV")

        if co2_cols:
            sensor_df['CO2_ppm'] = df[co2_cols[0]]
        else:
            sensor_df['CO2_ppm'] = None
            self.logger.warning("Không tìm thấy cột CO2 trong CSV")

        out_path = os.path.join(output_dir, f'{scenario_name}_sensor_data.csv')
        sensor_df.to_csv(out_path, index=False)
        self.logger.info(f"Sensor CSV exported: {out_path}")
        return out_path

    def calculate_summary_metrics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate summary metrics from simulation results
        
        Args:
            df: DataFrame with simulation results
            
        Returns:
            Dictionary with summary metrics
        """
        metrics = {}
        
        # Energy consumption metrics
        cooling_cols = [col for col in df.columns if 'Cooling Energy' in col]
        heating_cols = [col for col in df.columns if 'Heating Energy' in col]
        lighting_cols = [col for col in df.columns if 'Lights' in col and 'Energy' in col]
        equipment_cols = [col for col in df.columns if 'Equipment' in col and 'Energy' in col]
        
        if cooling_cols:
            metrics['total_cooling_energy_kwh'] = df[cooling_cols[0]].sum() / 3600000  # J to kWh
            metrics['peak_cooling_power_kw'] = df[cooling_cols[0]].max() / 3600000 * 4  # Timestep to power
        
        if heating_cols:
            metrics['total_heating_energy_kwh'] = df[heating_cols[0]].sum() / 3600000
            metrics['peak_heating_power_kw'] = df[heating_cols[0]].max() / 3600000 * 4
        
        if lighting_cols:
            metrics['total_lighting_energy_kwh'] = df[lighting_cols[0]].sum() / 3600000
        
        if equipment_cols:
            metrics['total_equipment_energy_kwh'] = df[equipment_cols[0]].sum() / 3600000
        
        # Total energy
        total_energy = 0
        for key in ['total_cooling_energy_kwh', 'total_heating_energy_kwh', 
                   'total_lighting_energy_kwh', 'total_equipment_energy_kwh']:
            if key in metrics:
                total_energy += metrics[key]
        
        metrics['total_energy_kwh'] = total_energy
        
        # Temperature metrics
        temp_cols = [col for col in df.columns if 'Temperature' in col and 'Zone' in col]
        if temp_cols:
            metrics['avg_temperature_c'] = df[temp_cols[0]].mean()
            metrics['min_temperature_c'] = df[temp_cols[0]].min()
            metrics['max_temperature_c'] = df[temp_cols[0]].max()
        
        # Humidity metrics
        humidity_cols = [col for col in df.columns if 'Humidity' in col]
        if humidity_cols:
            metrics['avg_humidity_pct'] = df[humidity_cols[0]].mean()
            metrics['min_humidity_pct'] = df[humidity_cols[0]].min()
            metrics['max_humidity_pct'] = df[humidity_cols[0]].max()
        
        return metrics
    
    def compare_scenarios(self, scenario_results: Dict[str, Dict]) -> pd.DataFrame:
        """
        Compare metrics across multiple scenarios
        
        Args:
            scenario_results: Dictionary mapping scenario names to their metrics
            
        Returns:
            DataFrame with comparison
        """
        comparison_df = pd.DataFrame(scenario_results).T
        
        # Calculate percentage differences from baseline if exists
        if 'Baseline' in comparison_df.index or 'baseline' in comparison_df.index:
            baseline_name = 'Baseline' if 'Baseline' in comparison_df.index else 'baseline'
            baseline = comparison_df.loc[baseline_name]
            
            for col in comparison_df.columns:
                if pd.api.types.is_numeric_dtype(comparison_df[col]):
                    comparison_df[f'{col}_diff_pct'] = (
                        (comparison_df[col] - baseline[col]) / baseline[col] * 100
                    )
        
        return comparison_df
    
    def generate_plots(self, df: pd.DataFrame, output_dir: str, scenario_name: str):
        """
        Generate visualization plots
        
        Args:
            df: DataFrame with simulation results
            output_dir: Directory to save plots
            scenario_name: Name of scenario
        """
        ensure_dir(output_dir)
        
        # Temperature plot
        temp_cols = [col for col in df.columns if 'Temperature' in col and 'Zone' in col]
        if temp_cols and 'DateTime' in df.columns:
            plt.figure(figsize=(12, 6))
            plt.plot(df['DateTime'], df[temp_cols[0]], label='Zone Temperature')
            plt.xlabel('Date/Time')
            plt.ylabel('Temperature (°C)')
            plt.title(f'Zone Temperature - {scenario_name}')
            plt.legend()
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f'{scenario_name}_temperature.png'))
            plt.close()
        
        # Energy consumption plot
        energy_data = {}
        cooling_cols = [col for col in df.columns if 'Cooling Energy' in col]
        heating_cols = [col for col in df.columns if 'Heating Energy' in col]
        lighting_cols = [col for col in df.columns if 'Lights' in col and 'Energy' in col]
        equipment_cols = [col for col in df.columns if 'Equipment' in col and 'Energy' in col]
        
        if cooling_cols:
            energy_data['Cooling'] = df[cooling_cols[0]].sum() / 3600000
        if heating_cols:
            energy_data['Heating'] = df[heating_cols[0]].sum() / 3600000
        if lighting_cols:
            energy_data['Lighting'] = df[lighting_cols[0]].sum() / 3600000
        if equipment_cols:
            energy_data['Equipment'] = df[equipment_cols[0]].sum() / 3600000
        
        if energy_data:
            plt.figure(figsize=(10, 6))
            plt.bar(energy_data.keys(), energy_data.values())
            plt.xlabel('Category')
            plt.ylabel('Energy Consumption (kWh)')
            plt.title(f'Annual Energy Consumption - {scenario_name}')
            plt.grid(True, axis='y')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f'{scenario_name}_energy.png'))
            plt.close()
    
    def generate_report(self, scenario_name: str, result_dir: str, 
                       output_path: str = None) -> Dict:
        """
        Generate comprehensive report for a scenario
        
        Args:
            scenario_name: Name of scenario
            result_dir: Directory containing simulation results
            output_path: Path to save report (optional)
            
        Returns:
            Dictionary with report data
        """
        csv_path = os.path.join(result_dir, 'eplusout.csv')
        
        if not os.path.exists(csv_path):
            self.logger.error(f"Results not found for {scenario_name}")
            return None
        
        # Parse results
        df = self.parse_csv_output(csv_path)
        
        # Calculate metrics
        metrics = self.calculate_summary_metrics(df)
        
        # Export clean sensor CSV (Nhiệt độ, Độ ẩm, Ánh sáng, CO2)
        sensor_csv_path = self.export_sensor_csv(df, result_dir, scenario_name)

        # Generate plots
        plots_dir = os.path.join(result_dir, 'plots')
        self.generate_plots(df, plots_dir, scenario_name)
        
        # Create report
        report = {
            'scenario_name': scenario_name,
            'metrics': metrics,
            'sensor_csv': sensor_csv_path,
            'plots_dir': plots_dir
        }
        
        # Save report as JSON
        if output_path is None:
            output_path = os.path.join(result_dir, 'report.json')
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Report generated: {output_path}")
        
        return report
    
    def generate_comparison_report(self, scenarios_dir: str, output_path: str = None):
        """
        Generate comparison report for all scenarios
        
        Args:
            scenarios_dir: Directory containing all scenario results
            output_path: Path to save comparison report
        """
        scenario_metrics = {}
        
        # Collect metrics from all scenarios
        for scenario_name in os.listdir(scenarios_dir):
            scenario_path = os.path.join(scenarios_dir, scenario_name)
            if os.path.isdir(scenario_path):
                csv_path = os.path.join(scenario_path, 'eplusout.csv')
                if os.path.exists(csv_path):
                    df = self.parse_csv_output(csv_path)
                    metrics = self.calculate_summary_metrics(df)
                    scenario_metrics[scenario_name] = metrics
        
        if not scenario_metrics:
            self.logger.warning("No scenario results found")
            return
        
        # Create comparison DataFrame
        comparison_df = self.compare_scenarios(scenario_metrics)
        
        # Save comparison
        if output_path is None:
            output_path = os.path.join(scenarios_dir, 'comparison_report.xlsx')
        
        comparison_df.to_excel(output_path)
        
        # Also save as CSV
        csv_output = output_path.replace('.xlsx', '.csv')
        comparison_df.to_csv(csv_output)
        
        self.logger.info(f"Comparison report generated: {output_path}")
        
        # Generate comparison plots
        self._generate_comparison_plots(comparison_df, os.path.dirname(output_path))
    
    def _generate_comparison_plots(self, comparison_df: pd.DataFrame, output_dir: str):
        """Generate comparison plots across scenarios"""
        
        # Energy comparison
        energy_cols = [col for col in comparison_df.columns 
                      if 'energy_kwh' in col and 'diff' not in col]
        
        if energy_cols:
            fig, ax = plt.subplots(figsize=(12, 6))
            comparison_df[energy_cols].plot(kind='bar', ax=ax)
            ax.set_xlabel('Scenario')
            ax.set_ylabel('Energy (kWh)')
            ax.set_title('Energy Consumption Comparison')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'energy_comparison.png'))
            plt.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Parse EnergyPlus results')
    parser.add_argument('--scenario-name', help='Scenario name')
    parser.add_argument('--result-dir', help='Result directory')
    parser.add_argument('--compare-all', action='store_true',
                       help='Generate comparison report for all scenarios')
    parser.add_argument('--scenarios-dir', help='Directory containing all scenarios')
    
    args = parser.parse_args()
    
    parser_obj = ResultParser()
    
    if args.compare_all:
        if not args.scenarios_dir:
            project_root = get_project_root()
            args.scenarios_dir = project_root / "outputs" / "results"
        
        parser_obj.generate_comparison_report(args.scenarios_dir)
    elif args.scenario_name and args.result_dir:
        parser_obj.generate_report(args.scenario_name, args.result_dir)
    else:
        print("Please specify either --compare-all or both --scenario-name and --result-dir")
