"""
Main script to orchestrate the entire EnergyPlus simulation workflow
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from generators.idf_generator import IDFGenerator
from runners.run_simulation import EnergyPlusRunner
from runners.batch_runner import BatchRunner
from parsers.result_parser import ResultParser
from utils.helpers import setup_logging, get_project_root


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='EnergyPlus Modular JSON-Python Simulation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate IDF for a single scenario
  python main.py generate --scenario config/scenarios/baseline.json
  
  # Run simulation for a single scenario
  python main.py run --scenario config/scenarios/baseline.json
  
  # Run all scenarios
  python main.py run-all
  
  # Run all scenarios in parallel
  python main.py run-all --parallel
  
  # Generate comparison report
  python main.py compare
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Generate IDF command
    generate_parser = subparsers.add_parser('generate', help='Generate IDF file from scenario')
    generate_parser.add_argument('--scenario', required=True, help='Path to scenario JSON file')
    generate_parser.add_argument('--output', help='Output IDF file path')
    
    # Run single scenario command
    run_parser = subparsers.add_parser('run', help='Run simulation for a single scenario')
    run_parser.add_argument('--scenario', required=True, help='Path to scenario JSON file')
    run_parser.add_argument('--energyplus-path', help='Path to EnergyPlus executable')
    run_parser.add_argument('--no-report', action='store_true', help='Skip generating report')
    
    # Run all scenarios command
    run_all_parser = subparsers.add_parser('run-all', help='Run all scenarios')
    run_all_parser.add_argument('--scenarios-dir', help='Directory containing scenario files')
    run_all_parser.add_argument('--energyplus-path', help='Path to EnergyPlus executable')
    run_all_parser.add_argument('--parallel', action='store_true', help='Run scenarios in parallel')
    run_all_parser.add_argument('--max-workers', type=int, default=4, 
                               help='Maximum number of parallel workers')
    run_all_parser.add_argument('--compare', action='store_true', 
                               help='Generate comparison report after running')
    
    # Compare scenarios command
    compare_parser = subparsers.add_parser('compare', help='Generate comparison report')
    compare_parser.add_argument('--scenarios-dir', help='Directory containing scenario results')
    
    # Parse report command
    report_parser = subparsers.add_parser('report', help='Generate report for a scenario')
    report_parser.add_argument('--scenario-name', required=True, help='Scenario name')
    report_parser.add_argument('--result-dir', required=True, help='Result directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    logger = setup_logging()
    project_root = get_project_root()
    
    try:
        if args.command == 'generate':
            # Generate IDF
            logger.info(f"Generating IDF for scenario: {args.scenario}")
            generator = IDFGenerator(args.scenario)
            idf_path = generator.generate_idf(output_path=args.output)
            print(f"\n✓ IDF file generated successfully: {idf_path}")
        
        elif args.command == 'run':
            # Run single scenario
            logger.info(f"Running scenario: {args.scenario}")
            
            # Generate IDF
            generator = IDFGenerator(args.scenario)
            idf_path = generator.generate_idf()
            
            # Get scenario info
            from utils.helpers import load_json
            scenario = load_json(args.scenario)
            scenario_name = scenario['scenario_name']
            weather_file_name = scenario.get('weather_file', 'VNM_Ho.Chi.Minh.488500_IWEC.epw')
            weather_file = project_root / "data" / "weather" / weather_file_name
            
            # Run simulation
            runner = EnergyPlusRunner(energyplus_path=args.energyplus_path)
            result = runner.run_simulation(
                idf_path=idf_path,
                weather_file=str(weather_file),
                scenario_name=scenario_name
            )
            
            print(f"\n✓ Simulation completed successfully!")
            print(f"  Output directory: {result['output_dir']}")
            
            # Generate report
            if not args.no_report:
                logger.info("Generating report...")
                parser_obj = ResultParser()
                report = parser_obj.generate_report(scenario_name, result['output_dir'])
                print(f"  Report generated: {result['output_dir']}/report.json")
        
        elif args.command == 'run-all':
            # Run all scenarios
            logger.info("Running all scenarios...")
            
            batch_runner = BatchRunner(
                energyplus_path=args.energyplus_path,
                max_workers=args.max_workers
            )
            
            results = batch_runner.run_all_scenarios(
                scenarios_dir=args.scenarios_dir,
                parallel=args.parallel
            )
            
            # Generate comparison report if requested
            if args.compare:
                logger.info("Generating comparison report...")
                parser_obj = ResultParser()
                scenarios_dir = args.scenarios_dir or str(project_root / "outputs" / "results")
                parser_obj.generate_comparison_report(scenarios_dir)
                print(f"\n✓ Comparison report generated: {scenarios_dir}/comparison_report.xlsx")
        
        elif args.command == 'compare':
            # Generate comparison report
            logger.info("Generating comparison report...")
            parser_obj = ResultParser()
            scenarios_dir = args.scenarios_dir or str(project_root / "outputs" / "results")
            parser_obj.generate_comparison_report(scenarios_dir)
            print(f"\n✓ Comparison report generated: {scenarios_dir}/comparison_report.xlsx")
        
        elif args.command == 'report':
            # Generate report for specific scenario
            logger.info(f"Generating report for {args.scenario_name}...")
            parser_obj = ResultParser()
            report = parser_obj.generate_report(args.scenario_name, args.result_dir)
            print(f"\n✓ Report generated: {args.result_dir}/report.json")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
