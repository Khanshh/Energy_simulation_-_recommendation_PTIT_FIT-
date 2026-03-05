"""
IDF Generator - Generate EnergyPlus IDF files from JSON configurations
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.helpers import (
    load_json, merge_configs, validate_geometry, validate_materials,
    setup_logging, get_project_root, ensure_dir
)


class IDFGenerator:
    """Generate EnergyPlus IDF files from JSON configurations"""
    
    def __init__(self, scenario_path: str):
        """
        Initialize IDF Generator
        
        Args:
            scenario_path: Path to scenario JSON file
        """
        self.logger = setup_logging()
        self.project_root = get_project_root()
        self.scenario = load_json(scenario_path)
        self.scenario_name = self.scenario['scenario_name']
        
        # Load all configuration files
        self.geometry = self._load_config('geometry')
        self.materials = self._load_config('materials')
        self.hvac = self._load_config('hvac')
        self.schedules = self._load_config('schedules')
        
        # Apply overrides from scenario
        self._apply_overrides()
        
        # Validate configurations
        validate_geometry(self.geometry)
        validate_materials(self.materials)
        
        self.logger.info(f"Initialized IDF Generator for scenario: {self.scenario_name}")
    
    def _load_config(self, config_type: str) -> dict:
        """Load configuration file"""
        config_path = self.scenario['config_files'][config_type]
        full_path = self.project_root / config_path
        return load_json(str(full_path))
    
    def _apply_overrides(self):
        """Apply scenario overrides to configurations"""
        if 'overrides' not in self.scenario or not self.scenario['overrides']:
            return
        
        overrides = self.scenario['overrides']
        
        if 'geometry' in overrides:
            self.geometry = merge_configs(self.geometry, overrides['geometry'])
        
        if 'materials' in overrides:
            self.materials = merge_configs(self.materials, overrides['materials'])
        
        if 'hvac' in overrides:
            self.hvac = merge_configs(self.hvac, overrides['hvac'])
        
        if 'schedules' in overrides:
            self.schedules = merge_configs(self.schedules, overrides['schedules'])
        
        self.logger.info("Applied scenario overrides")
    
    def generate_idf(self, output_path: str = None) -> str:
        """
        Generate complete IDF file
        
        Args:
            output_path: Path to save IDF file (optional)
            
        Returns:
            Path to generated IDF file
        """
        if output_path is None:
            ensure_dir(str(self.project_root / "outputs" / "idf"))
            output_path = self.project_root / "outputs" / "idf" / f"{self.scenario_name}.idf"
        
        self.logger.info(f"Generating IDF file: {output_path}")
        
        idf_content = []
        
        # Add header
        idf_content.append(self._generate_header())
        
        # Add simulation control
        idf_content.append(self._generate_simulation_control())
        
        # Add building
        idf_content.append(self._generate_building())
        
        # Add global geometry rules
        idf_content.append(self._generate_global_geometry_rules())
        
        # Add location and design days
        idf_content.append(self._generate_location())
        
        # Add materials
        idf_content.extend(self._generate_materials())
        
        # Add constructions
        idf_content.extend(self._generate_constructions())
        
        # Add zone
        idf_content.append(self._generate_zone())
        
        # Add surfaces (walls, floor, ceiling)
        idf_content.extend(self._generate_surfaces())
        
        # Add windows and doors
        idf_content.extend(self._generate_fenestration())
        
        # Add schedule type limits
        idf_content.append(self._generate_schedule_type_limits())
        
        # Add schedules
        idf_content.extend(self._generate_schedules())
        
        # Add internal gains (people, lights, equipment)
        idf_content.extend(self._generate_internal_gains())
        
        # Add HVAC
        idf_content.extend(self._generate_hvac())
        
        # Add output variables
        idf_content.append(self._generate_outputs())
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n\n'.join(idf_content))
        
        self.logger.info(f"IDF file generated successfully: {output_path}")
        return str(output_path)
    
    def _generate_header(self) -> str:
        """Generate IDF header"""
        return f"""!-Generator IDFGenerator
!-Option OriginalOrderTop

!-NOTE: All comments with '!-' are ignored by the IDFEditor and are generated automatically.
!-      Use '!' comments if they need to be retained when using the IDFEditor.

!- Scenario: {self.scenario_name}
!- Description: {self.scenario.get('description', '')}

Version,
  9.6;  !- Version Identifier"""
    
    def _generate_simulation_control(self) -> str:
        """Generate simulation control objects"""
        period = self.scenario['simulation_period']
        
        return f"""SimulationControl,
  No,                      !- Do Zone Sizing Calculation
  No,                      !- Do System Sizing Calculation
  No,                      !- Do Plant Sizing Calculation
  Yes,                     !- Run Simulation for Sizing Periods
  Yes;                     !- Run Simulation for Weather File Run Periods

RunPeriod,
  Annual,                  !- Name
  {period['start_month']}, !- Begin Month
  {period['start_day']},   !- Begin Day of Month
  {period.get('year', 2024)}, !- Begin Year
  {period['end_month']},   !- End Month
  {period['end_day']},     !- End Day of Month
  {period.get('year', 2024)}, !- End Year
  Sunday,                  !- Day of Week for Start Day
  Yes,                     !- Use Weather File Holidays and Special Days
  Yes,                     !- Use Weather File Daylight Saving Period
  No,                      !- Apply Weekend Holiday Rule
  Yes,                     !- Use Weather File Rain Indicators
  Yes;                     !- Use Weather File Snow Indicators

Timestep,
  4;                       !- Number of Timesteps per Hour"""
    
    def _generate_building(self) -> str:
        """Generate building object"""
        return f"""Building,
  {self.geometry['room_name']},  !- Name
  {self.geometry['orientation']['north_axis']},  !- North Axis
  Suburbs,                 !- Terrain
  0.04,                    !- Loads Convergence Tolerance Value
  0.40,                    !- Temperature Convergence Tolerance Value
  FullInteriorAndExterior, !- Solar Distribution
  25,                      !- Maximum Number of Warmup Days
  6;                       !- Minimum Number of Warmup Days"""
    
    def _generate_global_geometry_rules(self) -> str:
        """Generate global geometry rules"""
        return """GlobalGeometryRules,
  UpperLeftCorner,         !- Starting Vertex Position
  Counterclockwise,        !- Vertex Entry Direction
  Relative;                !- Coordinate System"""
    
    def _generate_location(self) -> str:
        """Generate site location"""
        loc = self.geometry['location']
        
        return f"""Site:Location,
  {loc['city']},           !- Name
  {loc['latitude']},       !- Latitude
  {loc['longitude']},      !- Longitude
  {loc['timezone']},       !- Time Zone
  {loc['elevation']};      !- Elevation"""
    
    def _generate_materials(self) -> list:
        """Generate material objects"""
        materials = []
        
        for mat_name, mat_data in self.materials['materials'].items():
            material = f"""Material,
  {mat_name},              !- Name
  {mat_data['roughness']}, !- Roughness
  {mat_data['thickness']}, !- Thickness
  {mat_data['conductivity']},  !- Conductivity
  {mat_data['density']},   !- Density
  {mat_data['specific_heat']},  !- Specific Heat
  {mat_data.get('thermal_absorptance', 0.9)},  !- Thermal Absorptance
  {mat_data.get('solar_absorptance', 0.7)},    !- Solar Absorptance
  {mat_data.get('visible_absorptance', 0.7)};  !- Visible Absorptance"""
            materials.append(material)
        
        # Add glazing materials
        for glaz_name, glaz_data in self.materials['glazing'].items():
            glazing = f"""WindowMaterial:SimpleGlazingSystem,
  {glaz_name},             !- Name
  {glaz_data['u_factor']}, !- U-Factor
  {glaz_data['solar_heat_gain_coefficient']},  !- Solar Heat Gain Coefficient
  {glaz_data.get('visible_transmittance', 0.8)};  !- Visible Transmittance"""
            materials.append(glazing)
        
        return materials
    
    def _generate_constructions(self) -> list:
        """Generate construction objects"""
        constructions = []
        
        for const_name, const_data in self.materials['constructions'].items():
            if 'glazing' in const_data:
                # Window construction
                construction = f"""Construction,
  {const_name},            !- Name
  {const_data['glazing']};  !- Layer 1"""
            else:
                # Opaque construction
                layers = ',\n  '.join([f"{layer};" if i == len(const_data['layers'])-1 else f"{layer}" 
                                       for i, layer in enumerate(const_data['layers'])])
                construction = f"""Construction,
  {const_name},            !- Name
  {layers}"""
            
            constructions.append(construction)
        
        return constructions
    
    def _generate_zone(self) -> str:
        """Generate zone object"""
        dims = self.geometry['dimensions']
        
        return f"""Zone,
  {self.geometry['room_name']},  !- Name
  0,                       !- Direction of Relative North
  0, 0, 0,                 !- X, Y, Z Origin
  1,                       !- Type
  1,                       !- Multiplier
  autocalculate,           !- Ceiling Height
  autocalculate;           !- Volume"""
    
    def _generate_surfaces(self) -> list:
        """Generate surface objects (walls, floor, ceiling)"""
        surfaces = []
        dims = self.geometry['dimensions']
        zone_name = self.geometry['room_name']
        
        # Floor
        floor = f"""BuildingSurface:Detailed,
  Floor,                   !- Name
  Floor,                   !- Surface Type
  Floor,                   !- Construction Name
  {zone_name},             !- Zone Name
  Ground,                  !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  NoSun,                   !- Sun Exposure
  NoWind,                  !- Wind Exposure
  0,                       !- View Factor to Ground
  4,                       !- Number of Vertices
  0, 0, 0,                 !- Vertex 1
  0, {dims['width']}, 0,   !- Vertex 2
  {dims['length']}, {dims['width']}, 0,  !- Vertex 3
  {dims['length']}, 0, 0;  !- Vertex 4"""
        surfaces.append(floor)
        
        # Ceiling
        ceiling = f"""BuildingSurface:Detailed,
  Ceiling,                 !- Name
  Roof,                    !- Surface Type
  Ceiling,                 !- Construction Name
  {zone_name},             !- Zone Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  0,                       !- View Factor to Ground
  4,                       !- Number of Vertices
  0, {dims['width']}, {dims['height']},  !- Vertex 1
  0, 0, {dims['height']},  !- Vertex 2
  {dims['length']}, 0, {dims['height']},  !- Vertex 3
  {dims['length']}, {dims['width']}, {dims['height']};  !- Vertex 4"""
        surfaces.append(ceiling)
        
        # South Wall
        south_wall = f"""BuildingSurface:Detailed,
  Wall_South,              !- Name
  Wall,                    !- Surface Type
  External_Wall,           !- Construction Name
  {zone_name},             !- Zone Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  0.5,                     !- View Factor to Ground
  4,                       !- Number of Vertices
  0, 0, {dims['height']},  !- Vertex 1
  0, 0, 0,                 !- Vertex 2
  {dims['length']}, 0, 0,  !- Vertex 3
  {dims['length']}, 0, {dims['height']};  !- Vertex 4"""
        surfaces.append(south_wall)
        
        # North Wall
        north_wall = f"""BuildingSurface:Detailed,
  Wall_North,              !- Name
  Wall,                    !- Surface Type
  External_Wall,           !- Construction Name
  {zone_name},             !- Zone Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  0.5,                     !- View Factor to Ground
  4,                       !- Number of Vertices
  {dims['length']}, {dims['width']}, {dims['height']},  !- Vertex 1
  {dims['length']}, {dims['width']}, 0,  !- Vertex 2
  0, {dims['width']}, 0,   !- Vertex 3
  0, {dims['width']}, {dims['height']};  !- Vertex 4"""
        surfaces.append(north_wall)
        
        # East Wall
        east_wall = f"""BuildingSurface:Detailed,
  Wall_East,               !- Name
  Wall,                    !- Surface Type
  External_Wall,           !- Construction Name
  {zone_name},             !- Zone Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  0.5,                     !- View Factor to Ground
  4,                       !- Number of Vertices
  {dims['length']}, 0, {dims['height']},  !- Vertex 1
  {dims['length']}, 0, 0,  !- Vertex 2
  {dims['length']}, {dims['width']}, 0,  !- Vertex 3
  {dims['length']}, {dims['width']}, {dims['height']};  !- Vertex 4"""
        surfaces.append(east_wall)
        
        # West Wall
        west_wall = f"""BuildingSurface:Detailed,
  Wall_West,               !- Name
  Wall,                    !- Surface Type
  External_Wall,           !- Construction Name
  {zone_name},             !- Zone Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  0.5,                     !- View Factor to Ground
  4,                       !- Number of Vertices
  0, {dims['width']}, {dims['height']},  !- Vertex 1
  0, {dims['width']}, 0,   !- Vertex 2
  0, 0, 0,                 !- Vertex 3
  0, 0, {dims['height']};  !- Vertex 4"""
        surfaces.append(west_wall)
        
        return surfaces
    
    def _generate_fenestration(self) -> list:
        """Generate windows and doors"""
        fenestration = []
        dims = self.geometry['dimensions']
        
        # Windows
        if 'windows' in self.geometry:
            for window in self.geometry['windows']:
                wall_name = f"Wall_{window['wall']}"
                # Calculate vertices based on wall
                v1, v2, v3, v4 = "", "", "", ""
                if window['wall'] == 'South':
                    v1 = f"{window['offset_from_left']}, 0, {window['sill_height'] + window['height']}"
                    v2 = f"{window['offset_from_left']}, 0, {window['sill_height']}"
                    v3 = f"{window['offset_from_left'] + window['width']}, 0, {window['sill_height']}"
                    v4 = f"{window['offset_from_left'] + window['width']}, 0, {window['sill_height'] + window['height']}"
                elif window['wall'] == 'North':
                    v1 = f"{dims['length'] - window['offset_from_left']}, {dims['width']}, {window['sill_height'] + window['height']}"
                    v2 = f"{dims['length'] - window['offset_from_left']}, {dims['width']}, {window['sill_height']}"
                    v3 = f"{dims['length'] - (window['offset_from_left'] + window['width'])}, {dims['width']}, {window['sill_height']}"
                    v4 = f"{dims['length'] - (window['offset_from_left'] + window['width'])}, {dims['width']}, {window['sill_height'] + window['height']}"
                elif window['wall'] == 'East':
                    v1 = f"{dims['length']}, {window['offset_from_left']}, {window['sill_height'] + window['height']}"
                    v2 = f"{dims['length']}, {window['offset_from_left']}, {window['sill_height']}"
                    v3 = f"{dims['length']}, {window['offset_from_left'] + window['width']}, {window['sill_height']}"
                    v4 = f"{dims['length']}, {window['offset_from_left'] + window['width']}, {window['sill_height'] + window['height']}"
                elif window['wall'] == 'West':
                    v1 = f"0, {dims['width'] - window['offset_from_left']}, {window['sill_height'] + window['height']}"
                    v2 = f"0, {dims['width'] - window['offset_from_left']}, {window['sill_height']}"
                    v3 = f"0, {dims['width'] - (window['offset_from_left'] + window['width'])}, {window['sill_height']}"
                    v4 = f"0, {dims['width'] - (window['offset_from_left'] + window['width'])}, {window['sill_height'] + window['height']}"
                
                win_obj = f"""FenestrationSurface:Detailed,
  {window['name']},        !- Name
  Window,                  !- Surface Type
  Window_Construction,     !- Construction Name
  {wall_name},             !- Building Surface Name
  ,                        !- Outside Boundary Condition Object
  autocalculate,           !- View Factor to Ground
  ,                        !- Frame and Divider Name
  1,                       !- Multiplier
  4,                       !- Number of Vertices
  {v1},  !- Vertex 1
  {v2},  !- Vertex 2
  {v3},  !- Vertex 3
  {v4};  !- Vertex 4"""
                fenestration.append(win_obj)
        
        # Doors
        if 'doors' in self.geometry:
            for door in self.geometry['doors']:
                wall_name = f"Wall_{door['wall']}"
                v1, v2, v3, v4 = "", "", "", ""
                if door['wall'] == 'South':
                    v1 = f"{door['offset_from_left']}, 0, {door['height']}"
                    v2 = f"{door['offset_from_left']}, 0, 0"
                    v3 = f"{door['offset_from_left'] + door['width']}, 0, 0"
                    v4 = f"{door['offset_from_left'] + door['width']}, 0, {door['height']}"
                elif door['wall'] == 'North':
                    v1 = f"{dims['length'] - door['offset_from_left']}, {dims['width']}, {door['height']}"
                    v2 = f"{dims['length'] - door['offset_from_left']}, {dims['width']}, 0"
                    v3 = f"{dims['length'] - (door['offset_from_left'] + door['width'])}, {dims['width']}, 0"
                    v4 = f"{dims['length'] - (door['offset_from_left'] + door['width'])}, {dims['width']}, {door['height']}"
                elif door['wall'] == 'East':
                    v1 = f"{dims['length']}, {door['offset_from_left']}, {door['height']}"
                    v2 = f"{dims['length']}, {door['offset_from_left']}, 0"
                    v3 = f"{dims['length']}, {door['offset_from_left'] + door['width']}, 0"
                    v4 = f"{dims['length']}, {door['offset_from_left'] + door['width']}, {door['height']}"
                elif door['wall'] == 'West':
                    v1 = f"0, {dims['width'] - door['offset_from_left']}, {door['height']}"
                    v2 = f"0, {dims['width'] - door['offset_from_left']}, 0"
                    v3 = f"0, {dims['width'] - (door['offset_from_left'] + door['width'])}, 0"
                    v4 = f"0, {dims['width'] - (door['offset_from_left'] + door['width'])}, {door['height']}"

                door_obj = f"""FenestrationSurface:Detailed,
  {door['name']},          !- Name
  Door,                    !- Surface Type
  Door_Construction,       !- Construction Name
  {wall_name},             !- Building Surface Name
  ,                        !- Outside Boundary Condition Object
  autocalculate,           !- View Factor to Ground
  ,                        !- Frame and Divider Name
  1,                       !- Multiplier
  4,                       !- Number of Vertices
  {v1},  !- Vertex 1
  {v2},  !- Vertex 2
  {v3},  !- Vertex 3
  {v4};  !- Vertex 4"""
                fenestration.append(door_obj)
        
        return fenestration
    
    def _generate_schedule_type_limits(self) -> str:
        """Generate schedule type limits"""
        return """ScheduleTypeLimits,
  Fraction,                !- Name
  0.0,                     !- Lower Limit Value
  1.0,                     !- Upper Limit Value
  Continuous;              !- Numeric Type

ScheduleTypeLimits,
  OnOff,                   !- Name
  0,                       !- Lower Limit Value
  1,                       !- Upper Limit Value
  Discrete;                !- Numeric Type

ScheduleTypeLimits,
  Temperature,             !- Name
  -60,                     !- Lower Limit Value
  200,                     !- Upper Limit Value
  Continuous;              !- Numeric Type

ScheduleTypeLimits,
  Control Type,            !- Name
  0,                       !- Lower Limit Value
  4,                       !- Upper Limit Value
  Discrete;                !- Numeric Type

ScheduleTypeLimits,
  Any Number;              !- Name"""
    
    def _generate_schedules(self) -> list:
        """Generate schedule objects"""
        schedules = []
        
        # For simplicity, using compact schedules
        # In production, you'd want to generate full schedule objects
        
        schedules.append("""Schedule:Compact,
  Occupancy_Schedule,      !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: Weekdays,           !- Field 2
  Until: 08:00, 0.0,       !- Field 3
  Until: 09:00, 0.2,       !- Field 5
  Until: 12:00, 1.0,       !- Field 7
  Until: 13:00, 0.5,       !- Field 9
  Until: 17:00, 1.0,       !- Field 11
  Until: 18:00, 0.3,       !- Field 13
  Until: 24:00, 0.0,       !- Field 15
  For: Weekend,            !- Field 17
  Until: 24:00, 0.0,       !- Field 18
  For: AllOtherDays,       !- Field 19
  Until: 24:00, 0.0;       !- Field 20""")
        
        schedules.append("""Schedule:Compact,
  Lighting_Schedule,       !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: Weekdays,           !- Field 2
  Until: 08:00, 0.0,       !- Field 3
  Until: 12:00, 0.9,       !- Field 5
  Until: 13:00, 0.5,       !- Field 7
  Until: 17:00, 0.9,       !- Field 9
  Until: 19:00, 0.3,       !- Field 11
  Until: 24:00, 0.0,       !- Field 13
  For: Weekend,            !- Field 15
  Until: 24:00, 0.0,       !- Field 16
  For: AllOtherDays,       !- Field 17
  Until: 24:00, 0.0;       !- Field 18""")
        
        schedules.append("""Schedule:Compact,
  Equipment_Schedule,      !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: Weekdays,           !- Field 2
  Until: 08:00, 0.1,       !- Field 3
  Until: 09:00, 0.3,       !- Field 5
  Until: 12:00, 0.9,       !- Field 7
  Until: 13:00, 0.5,       !- Field 9
  Until: 17:00, 0.9,       !- Field 11
  Until: 18:00, 0.3,       !- Field 13
  Until: 24:00, 0.1,       !- Field 15
  For: Weekend,            !- Field 17
  Until: 24:00, 0.1,       !- Field 18
  For: AllOtherDays,       !- Field 19
  Until: 24:00, 0.1;       !- Field 20""")
        
        schedules.append("""Schedule:Compact,
  HVAC_Schedule,           !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: Weekdays,           !- Field 2
  Until: 07:00, 0,         !- Field 3
  Until: 18:00, 1,         !- Field 5
  Until: 24:00, 0,         !- Field 7
  For: Weekend,            !- Field 9
  Until: 24:00, 0,         !- Field 10
  For: AllOtherDays,       !- Field 11
  Until: 24:00, 0;         !- Field 12""")
        
        schedules.append("""Schedule:Compact,
  Always_On,               !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: AllDays,            !- Field 2
  Until: 24:00, 1.0;       !- Field 3""")
        
        # Add Outdoor CO2 Schedule (constant 400.0 ppm)
        schedules.append("""Schedule:Compact,
  Outdoor_CO2_Schedule,    !- Name
  Any Number,              !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: AllDays,            !- Field 2
  Until: 24:00, 400.0;     !- Field 3""")
        
        return schedules
    
    def _generate_internal_gains(self) -> list:
        """Generate internal gains (people, lights, equipment)"""
        gains = []
        zone_name = self.geometry['room_name']
        dims = self.geometry['dimensions']
        floor_area = dims['length'] * dims['width']
        
        # People
        occ_data = self.schedules['occupancy_data']
        people = f"""People,
  {zone_name}_People,      !- Name
  {zone_name},             !- Zone or ZoneList Name
  Occupancy_Schedule,      !- Number of People Schedule Name
  People,                  !- Number of People Calculation Method
  {occ_data['max_occupants']},  !- Number of People
  ,                        !- People per Zone Floor Area
  ,                        !- Zone Floor Area per Person
  0.3,                     !- Fraction Radiant
  autocalculate,           !- Sensible Heat Fraction
  Activity_Schedule,       !- Activity Level Schedule Name
  3.82e-8;                 !- Carbon Dioxide Generation Rate {{m3/s-W}}"""
        gains.append(people)

        # Infiltration (0.5 ACH roughly corresponds to 0.0003 m3/s-m2)
        infiltration = f"""ZoneInfiltration:DesignFlowRate,
  {zone_name}_Infiltration, !- Name
  {zone_name},             !- Zone or ZoneList Name
  Always_On,               !- Schedule Name
  Flow/Area,               !- Design Flow Rate Calculation Method
  ,                        !- Design Flow Rate {{m3/s}}
  0.0003,                  !- Flow per Zone Floor Area {{m3/s-m2}}
  ,                        !- Flow per Exterior Surface Area {{m3/s-m2}}
  ,                        !- Air Changes per Hour {{1/hr}}
  1.0,                     !- Constant Term Coefficient
  0.0,                     !- Temperature Term Coefficient
  0.0,                     !- Velocity Term Coefficient
  0.0;                     !- Velocity Squared Term Coefficient"""
        gains.append(infiltration)
        
        # Activity schedule
        activity = f"""Schedule:Compact,
  Activity_Schedule,       !- Name
  Any Number,              !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: AllDays,            !- Field 2
  Until: 24:00, {occ_data['activity_level']};  !- Field 3"""
        gains.append(activity)
        
        # Lights
        light_data = self.schedules['lighting_data']
        total_light_power = light_data['power_density'] * floor_area
        lights = f"""Lights,
  {zone_name}_Lights,      !- Name
  {zone_name},             !- Zone or ZoneList Name
  Lighting_Schedule,       !- Schedule Name
  Watts/Area,              !- Design Level Calculation Method
  ,                        !- Lighting Level
  {light_data['power_density']},  !- Watts per Zone Floor Area
  ,                        !- Watts per Person
  {light_data.get('return_air_fraction', 0.0)},  !- Return Air Fraction
  {light_data.get('radiant_fraction', 0.42)},    !- Fraction Radiant
  {light_data.get('visible_fraction', 0.18)};    !- Fraction Visible"""
        gains.append(lights)
        
        # Equipment
        equip_data = self.schedules['equipment_data']
        equipment = f"""ElectricEquipment,
  {zone_name}_Equipment,   !- Name
  {zone_name},             !- Zone or ZoneList Name
  Equipment_Schedule,      !- Schedule Name
  Watts/Area,              !- Design Level Calculation Method
  ,                        !- Design Level
  {equip_data['power_density']},  !- Watts per Zone Floor Area
  ,                        !- Watts per Person
  {equip_data.get('latent_fraction', 0.0)},  !- Fraction Latent
  {equip_data.get('radiant_fraction', 0.3)},  !- Fraction Radiant
  {equip_data.get('lost_fraction', 0.0)};     !- Fraction Lost"""
        gains.append(equipment)
        
        return gains
    
    def _generate_hvac(self) -> list:
        """Generate HVAC system"""
        hvac_objects = []
        zone_name = self.geometry['room_name']
        
        # Using Ideal Loads Air System for simplicity
        thermostat = f"""ZoneControl:Thermostat,
  {zone_name}_Thermostat,  !- Name
  {zone_name},             !- Zone or ZoneList Name
  Zone_Control_Type_Sched, !- Control Type Schedule Name
  ThermostatSetpoint:DualSetpoint,  !- Control 1 Object Type
  {zone_name}_DualSetpoint;  !- Control 1 Name"""
        hvac_objects.append(thermostat)
        
        control_sched = """Schedule:Compact,
  Zone_Control_Type_Sched, !- Name
  Control Type,            !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: AllDays,            !- Field 2
  Until: 24:00, 4;         !- Field 3"""
        hvac_objects.append(control_sched)
        
        heating_setpoint = self.hvac['thermostat']['heating_setpoint']
        cooling_setpoint = self.hvac['thermostat']['cooling_setpoint']
        
        dual_setpoint = f"""ThermostatSetpoint:DualSetpoint,
  {zone_name}_DualSetpoint,  !- Name
  Heating_Setpoint_Sched,  !- Heating Setpoint Temperature Schedule Name
  Cooling_Setpoint_Sched;  !- Cooling Setpoint Temperature Schedule Name"""
        hvac_objects.append(dual_setpoint)
        
        heating_sched = f"""Schedule:Compact,
  Heating_Setpoint_Sched,  !- Name
  Temperature,             !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: AllDays,            !- Field 2
  Until: 24:00, {heating_setpoint};  !- Field 3"""
        hvac_objects.append(heating_sched)
        
        cooling_sched = f"""Schedule:Compact,
  Cooling_Setpoint_Sched,  !- Name
  Temperature,             !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: AllDays,            !- Field 2
  Until: 24:00, {cooling_setpoint};  !- Field 3"""
        hvac_objects.append(cooling_sched)
        
        # Ideal Loads Air System
        ideal_loads = f"""HVACTemplate:Zone:IdealLoadsAirSystem,
  {zone_name},             !- Zone Name
  ,                        !- Template Thermostat Name
  ,                        !- System Availability Schedule Name
  50,                      !- Maximum Heating Supply Air Temperature
  13,                      !- Minimum Cooling Supply Air Temperature
  0.015,                   !- Maximum Heating Supply Air Humidity Ratio
  0.009,                   !- Minimum Cooling Supply Air Humidity Ratio
  NoLimit,                 !- Heating Limit
  autosize,                !- Maximum Heating Air Flow Rate
  ,                        !- Maximum Sensible Heating Capacity
  NoLimit,                 !- Cooling Limit
  autosize,                !- Maximum Cooling Air Flow Rate
  ,                        !- Maximum Total Cooling Capacity
  ,                        !- Heating Availability Schedule Name
  ,                        !- Cooling Availability Schedule Name
  ConstantSensibleHeatRatio,  !- Dehumidification Control Type
  0.7,                     !- Cooling Sensible Heat Ratio
  60.0,                    !- Dehumidification Setpoint
  None,                    !- Humidification Control Type
  30.0,                    !- Humidification Setpoint
  Flow/Person,             !- Outdoor Air Method
  0.00944,                 !- Outdoor Air Flow Rate per Person
  ,                        !- Outdoor Air Flow Rate per Zone Floor Area
  ,                        !- Outdoor Air Flow Rate per Zone
  ,                        !- Design Specification Outdoor Air Object Name
  None,                    !- Demand Controlled Ventilation Type
  NoEconomizer,            !- Outdoor Air Economizer Type
  None,                    !- Heat Recovery Type
  0.70,                    !- Sensible Heat Recovery Effectiveness
  0.65;                    !- Latent Heat Recovery Effectiveness"""
        hvac_objects.append(ideal_loads)
        
        return hvac_objects
    
    def _generate_outputs(self) -> str:
        """Generate output variables and reports"""
        outputs = []
        
        # Output controls
        outputs.append("""OutputControl:Table:Style,
  HTML;                    !- Column Separator""")
        
        outputs.append("""Output:VariableDictionary,
  Regular;                 !- Key Field""")

        # Enable CO2 concentration tracking
        outputs.append("""ZoneAirContaminantBalance,
  Yes,                     !- Carbon Dioxide Concentration
  Outdoor_CO2_Schedule;    !- Outdoor Carbon Dioxide Schedule Name""")
        
        # Output variables from scenario
        for var in self.scenario.get('output_variables', []):
            outputs.append(f"""Output:Variable,
  *,                       !- Key Value
  {var},                   !- Variable Name
  {self.scenario.get('output_frequency', 'Hourly')};  !- Reporting Frequency""")
        
        # Summary reports
        outputs.append("""Output:Table:SummaryReports,
  AllSummary;              !- Report 1 Name""")
        
        return '\n\n'.join(outputs)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python idf_generator.py <scenario_json_path>")
        sys.exit(1)
    
    scenario_path = sys.argv[1]
    generator = IDFGenerator(scenario_path)
    idf_path = generator.generate_idf()
    print(f"IDF file generated: {idf_path}")
