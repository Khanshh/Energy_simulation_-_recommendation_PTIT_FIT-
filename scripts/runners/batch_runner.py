"""
Batch runner to run multiple scenarios in parallel
"""

import os
import sys
from pathlib import Path
import concurrent.futures
from typing import List, Dict
import time

sys.path.append(str(Path(__file__).parent.parent))

from generators.idf_generator import IDFGenerator
from runners.run_simulation import EnergyPlusRunner
from utils.helpers import setup_logging, get_project_root, load_json


class BatchRunner:
    """Run multiple EnergyPlus scenarios in parallel"""
    
    def __init__(self, energyplus_path: str = None, max_workers: int = 4):
        """
        Initialize Batch Runner
        
        Args:
            energyplus_path: Path to EnergyPlus executable (optional)
            max_workers: Maximum number of parallel simulations
        """
        self.logger = setup_logging()
        self.project_root = get_project_root()
        self.runner = EnergyPlusRunner(energyplus_path=energyplus_path)
        self.max_workers = max_workers
        
        self.logger.info(f"Batch Runner initialized with {max_workers} workers")
    
    def find_scenarios(self, scenarios_dir: str = None) -> List[str]:
        """
        Find all scenario JSON files
        
        Args:
            scenarios_dir: Directory containing scenario files
            
        Returns:
            List of scenario file paths
        """
        if scenarios_dir is None:
            scenarios_dir = self.project_root / "config" / "scenarios"
        
        scenario_files = []
        for file in os.listdir(scenarios_dir):
            if file.endswith('.json'):
                scenario_files.append(os.path.join(scenarios_dir, file))
        
        self.logger.info(f"Found {len(scenario_files)} scenarios: {scenario_files}")
        return scenario_files
    
    def run_single_scenario(self, scenario_path: str) -> Dict:
        """
        Run a single scenario (generate IDF + run simulation)
        
        Args:
            scenario_path: Path to scenario JSON file
            
        Returns:
            Dictionary with results
        """
        start_time = time.time()
        
        try:
            # Load scenario to get weather file
            scenario = load_json(scenario_path)
            scenario_name = scenario['scenario_name']
            
            self.logger.info(f"Processing scenario: {scenario_name}")
            
            # Generate IDF
            self.logger.info(f"Generating IDF for {scenario_name}...")
            generator = IDFGenerator(scenario_path)
            idf_path = generator.generate_idf()
            
            # Get weather file path
            weather_file_name = scenario.get('weather_file', 'VNM_Ho.Chi.Minh.488500_IWEC.epw')
            weather_file = self.project_root / "data" / "weather" / weather_file_name
            
            if not os.path.exists(weather_file):
                self.logger.warning(f"Weather file not found: {weather_file}")
                self.logger.warning("Skipping simulation. Please download weather file.")
                return {
                    'scenario': scenario_name,
                    'status': 'skipped',
                    'reason': 'Weather file not found',
                    'idf_path': idf_path
                }
            
            # Run simulation
            self.logger.info(f"Running simulation for {scenario_name}...")
            result = self.runner.run_simulation(
                idf_path=idf_path,
                weather_file=str(weather_file),
                scenario_name=scenario_name
            )
            
            elapsed_time = time.time() - start_time
            
            return {
                'scenario': scenario_name,
                'status': 'success',
                'idf_path': idf_path,
                'output_dir': result['output_dir'],
                'elapsed_time': elapsed_time
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Error processing scenario {scenario_path}: {str(e)}")
            
            return {
                'scenario': os.path.basename(scenario_path),
                'status': 'failed',
                'error': str(e),
                'elapsed_time': elapsed_time
            }
    
    def run_all_scenarios(self, scenarios_dir: str = None, parallel: bool = True) -> List[Dict]:
        """
        Run all scenarios
        
        Args:
            scenarios_dir: Directory containing scenario files
            parallel: Whether to run in parallel
            
        Returns:
            List of result dictionaries
        """
        scenario_files = self.find_scenarios(scenarios_dir)
        
        if not scenario_files:
            self.logger.warning("No scenario files found")
            return []
        
        self.logger.info(f"Running {len(scenario_files)} scenarios...")
        
        results = []
        
        if parallel and len(scenario_files) > 1:
            # Run in parallel
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.run_single_scenario, scenario): scenario 
                    for scenario in scenario_files
                }
                
                for future in concurrent.futures.as_completed(futures):
                    scenario = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        self.logger.info(f"Completed: {result['scenario']} - {result['status']}")
                    except Exception as e:
                        self.logger.error(f"Exception for {scenario}: {str(e)}")
                        results.append({
                            'scenario': os.path.basename(scenario),
                            'status': 'failed',
                            'error': str(e)
                        })
        else:
            # Run sequentially
            for scenario in scenario_files:
                result = self.run_single_scenario(scenario)
                results.append(result)
                self.logger.info(f"Completed: {result['scenario']} - {result['status']}")
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: List[Dict]):
        """Print summary of all simulations"""
        print("\n" + "="*80)
        print("SIMULATION SUMMARY")
        print("="*80)
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        skipped_count = sum(1 for r in results if r['status'] == 'skipped')
        
        print(f"Total scenarios: {len(results)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failed_count}")
        print(f"Skipped: {skipped_count}")
        print()
        
        for result in results:
            status_symbol = "✓" if result['status'] == 'success' else "✗" if result['status'] == 'failed' else "⊘"
            print(f"{status_symbol} {result['scenario']}: {result['status']}")
            if result['status'] == 'success':
                print(f"  Output: {result['output_dir']}")
                print(f"  Time: {result['elapsed_time']:.2f}s")
            elif result['status'] == 'failed':
                print(f"  Error: {result.get('error', 'Unknown error')}")
            elif result['status'] == 'skipped':
                print(f"  Reason: {result.get('reason', 'Unknown')}")
        
        print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run multiple EnergyPlus scenarios')
    parser.add_argument('--scenarios-dir', help='Directory containing scenario files')
    parser.add_argument('--energyplus-path', help='Path to EnergyPlus executable')
    parser.add_argument('--max-workers', type=int, default=4, 
                       help='Maximum number of parallel simulations')
    parser.add_argument('--sequential', action='store_true',
                       help='Run scenarios sequentially instead of parallel')
    
    args = parser.parse_args()
    
    batch_runner = BatchRunner(
        energyplus_path=args.energyplus_path,
        max_workers=args.max_workers
    )
    
    results = batch_runner.run_all_scenarios(
        scenarios_dir=args.scenarios_dir,
        parallel=not args.sequential
    )
