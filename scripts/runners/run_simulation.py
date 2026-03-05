"""
Run EnergyPlus simulation with generated IDF file
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

sys.path.append(str(Path(__file__).parent.parent))

from utils.helpers import setup_logging, ensure_dir, get_project_root


class EnergyPlusRunner:
    """Run EnergyPlus simulations"""
    
    def __init__(self, energyplus_path: str = None):
        """
        Initialize EnergyPlus Runner
        
        Args:
            energyplus_path: Path to EnergyPlus executable (optional)
        """
        self.logger = setup_logging()
        self.project_root = get_project_root()
        
        # Try to find EnergyPlus executable
        if energyplus_path:
            self.energyplus_exe = energyplus_path
        else:
            self.energyplus_exe = self._find_energyplus()
        
        self.logger.info(f"EnergyPlus executable: {self.energyplus_exe}")
    
    def _find_energyplus(self) -> str:
        """
        Try to find EnergyPlus executable in common locations
        
        Returns:
            Path to EnergyPlus executable
        """
        # Common installation paths
        common_paths = [
            "/usr/local/EnergyPlus-9-6-0/energyplus",
            "/usr/local/EnergyPlus-23-2-0/energyplus",
            "C:/EnergyPlusV9-6-0/energyplus.exe",
            "C:/EnergyPlusV23-2-0/energyplus.exe",
        ]
        
        # Check if energyplus is in PATH
        try:
            result = subprocess.run(['which', 'energyplus'], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # Check common paths
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError(
            "EnergyPlus executable not found. Please install EnergyPlus or "
            "specify the path using --energyplus-path argument.\n"
            "Download from: https://energyplus.net/downloads"
        )
    
    def run_simulation(self, idf_path: str, weather_file: str, 
                      output_dir: str = None, scenario_name: str = None) -> dict:
        """
        Run EnergyPlus simulation
        
        Args:
            idf_path: Path to IDF file
            weather_file: Path to weather file (.epw)
            output_dir: Directory to store outputs (optional)
            scenario_name: Name of scenario for organizing outputs
            
        Returns:
            Dictionary with simulation results info
        """
        if not os.path.exists(idf_path):
            raise FileNotFoundError(f"IDF file not found: {idf_path}")
        
        if not os.path.exists(weather_file):
            raise FileNotFoundError(f"Weather file not found: {weather_file}")
        
        # Setup output directory
        if output_dir is None:
            if scenario_name:
                output_dir = self.project_root / "outputs" / "results" / scenario_name
            else:
                output_dir = self.project_root / "outputs" / "results" / "default"
        
        ensure_dir(str(output_dir))
        
        self.logger.info(f"Running simulation for: {idf_path}")
        self.logger.info(f"Weather file: {weather_file}")
        self.logger.info(f"Output directory: {output_dir}")
        
        # Run EnergyPlus
        try:
            # Check if we need to run ExpandObjects
            with open(idf_path, 'r') as f:
                idf_content = f.read()
                if 'HVACTemplate:' in idf_content:
                    self.logger.info("HVACTemplate found. Running ExpandObjects...")
                    
                    # Find real EnergyPlus dir (handle symlinks)
                    real_ep_exe = os.path.realpath(self.energyplus_exe)
                    ep_dir = os.path.dirname(real_ep_exe)
                    expand_exe = os.path.join(ep_dir, 'ExpandObjects')
                    idd_path = os.path.join(ep_dir, 'Energy+.idd')
                    
                    if os.path.exists(expand_exe) and os.path.exists(idd_path):
                        # Use output_dir as working dir for ExpandObjects to avoid conflicts
                        # ExpandObjects always looks for 'in.idf' and 'Energy+.idd' in CWD
                        shutil.copy2(idf_path, os.path.join(output_dir, 'in.idf'))
                        shutil.copy2(idd_path, os.path.join(output_dir, 'Energy+.idd'))
                        
                        # Run ExpandObjects in output_dir
                        subprocess.run([expand_exe], cwd=str(output_dir), capture_output=True, text=True)
                        
                        # If expanded.idf exists, use it
                        expanded_idf = os.path.join(output_dir, 'expanded.idf')
                        if os.path.exists(expanded_idf):
                            self.logger.info("IDF expanded successfully.")
                            idf_path = expanded_idf
                        else:
                            self.logger.warning("ExpandObjects did not produce expanded.idf. Using original IDF.")
                    else:
                        self.logger.warning(f"ExpandObjects or Energy+.idd not found in {ep_dir}. Simulation might fail.")

            cmd = [
                self.energyplus_exe,
                '-w', weather_file,
                '-d', str(output_dir),
                idf_path
            ]
            
            self.logger.info(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode != 0:
                self.logger.error(f"EnergyPlus failed with return code {result.returncode}")
                self.logger.error(f"STDOUT: {result.stdout}")
                self.logger.error(f"STDERR: {result.stderr}")
                raise RuntimeError(f"EnergyPlus simulation failed")
            
            self.logger.info("Simulation completed successfully")
            
            # Run ReadVarsESO to generate CSV from ESO
            self.logger.info("Running ReadVarsESO to generate CSV...")
            real_ep_exe = os.path.realpath(self.energyplus_exe)
            ep_dir = os.path.dirname(real_ep_exe)
            readvars_exe = os.path.join(ep_dir, 'PostProcess', 'ReadVarsESO')
            if not os.path.exists(readvars_exe):
                # Try same dir as energyplus
                readvars_exe = os.path.join(ep_dir, 'ReadVarsESO')
            
            if os.path.exists(readvars_exe):
                # Copy eplusout.eso to in.eso for ReadVarsESO
                eso_path = os.path.join(output_dir, 'eplusout.eso')
                if os.path.exists(eso_path):
                    shutil.copy2(eso_path, os.path.join(output_dir, 'in.eso'))
                    # Run ReadVarsESO in output_dir
                    subprocess.run([readvars_exe], cwd=str(output_dir), capture_output=True, text=True)
                    # Result should be in.csv, rename to eplusout.csv
                    in_csv = os.path.join(output_dir, 'in.csv')
                    if os.path.exists(in_csv):
                        shutil.move(in_csv, os.path.join(output_dir, 'eplusout.csv'))
                        self.logger.info("CSV generated successfully.")
                    else:
                        self.logger.warning("ReadVarsESO did not produce in.csv.")
                else:
                    self.logger.warning("eplusout.eso not found. Cannot run ReadVarsESO.")
            else:
                self.logger.warning("ReadVarsESO executable not found.")
            
            # Check for output files
            output_files = {
                'csv': os.path.join(output_dir, 'eplusout.csv'),
                'html': os.path.join(output_dir, 'eplustbl.htm'),
                'err': os.path.join(output_dir, 'eplusout.err'),
                'eio': os.path.join(output_dir, 'eplusout.eio'),
            }
            
            # Check for errors in .err file
            if os.path.exists(output_files['err']):
                with open(output_files['err'], 'r') as f:
                    err_content = f.read()
                    if 'Fatal' in err_content or 'Severe' in err_content:
                        self.logger.warning("Simulation completed with errors. Check .err file.")
            
            return {
                'status': 'success',
                'output_dir': str(output_dir),
                'output_files': output_files,
                'idf_path': idf_path,
                'weather_file': weather_file
            }
            
        except subprocess.TimeoutExpired:
            self.logger.error("Simulation timed out after 10 minutes")
            raise RuntimeError("Simulation timeout")
        except Exception as e:
            self.logger.error(f"Simulation error: {str(e)}")
            raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run EnergyPlus simulation')
    parser.add_argument('idf_file', help='Path to IDF file')
    parser.add_argument('weather_file', help='Path to weather file (.epw)')
    parser.add_argument('--output-dir', help='Output directory')
    parser.add_argument('--scenario-name', help='Scenario name')
    parser.add_argument('--energyplus-path', help='Path to EnergyPlus executable')
    
    args = parser.parse_args()
    
    runner = EnergyPlusRunner(energyplus_path=args.energyplus_path)
    result = runner.run_simulation(
        args.idf_file,
        args.weather_file,
        output_dir=args.output_dir,
        scenario_name=args.scenario_name
    )
    
    print(f"Simulation completed successfully!")
    print(f"Output directory: {result['output_dir']}")
