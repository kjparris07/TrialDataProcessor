"""
Trial Data Processing Script
Processes all trial data files and organizes them according to TRIAL_MAP and GROUPS
"""

import os
import csv
import math
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================
# CONFIGURATION
# ============================================

# Trial to eHMI Type mapping
TRIAL_MAP = {
    4: "A", 5: "A", 6: "A",
    10: "A", 11: "A", 12: "A",
    16: "A", 17: "A", 18: "A",
    22: "B", 23: "B", 24: "B",
    28: "B", 29: "B", 30: "B",
    34: "B", 35: "B", 36: "B",
}

# Grouping rules: (Lane, Traffic Type, Yield Type, [Trial Numbers])
GROUPS = [
    ("Two", "Single Car", "No Yield", [1, 19]),
    ("Two", "Single Car", "Yield", [4, 22]),
    ("Two", "Two Car Different", "No Yield", [7, 25]),
    ("Two", "Two Car Different", "Yield", [10, 28]),
    ("Two", "Two Car Same", "No Yield", [13, 31]),
    ("Two", "Two Car Same", "Yield", [16, 34]),

    ("Three", "Single Car", "No Yield", [2, 20]),
    ("Three", "Single Car", "Yield", [5, 23]),
    ("Three", "Two Car Different", "No Yield Failure", [8, 26]),
    ("Three", "Two Car Different", "Yield", [11, 29]),
    ("Three", "Two Car Same", "No Yield", [14, 32]),
    ("Three", "Two Car Same", "Yield", [17, 35]),

    ("Four", "Single Car", "No Yield Failure", [3, 21]),
    ("Four", "Single Car", "Yield", [6, 24]),
    ("Four", "Two Car Different", "No Yield Failure", [9, 27]),
    ("Four", "Two Car Different", "Yield", [12, 30]),
    ("Four", "Two Car Same", "No Yield Failure", [15, 33]),
    ("Four", "Two Car Same", "Yield", [18, 36]),
]

class TrialDataProcessor:
    """Processes trial data files and organizes them according to mappings"""
    
    def __init__(self, data_dir: str, gender_file: str):
        self.data_dir = Path(data_dir)
        self.gender_file = Path(gender_file) if gender_file != None else None
        self.gender_data = self._load_gender_data()
        self.trial_to_group = self._build_trial_to_group_map()
        
    def _load_gender_data(self) -> Dict[str, str]:
        """Load gender information for participants"""
        gender_dict = {}
        if self.gender_file and str(self.gender_file) != 'None' and self.gender_file.exists():
            with open(self.gender_file, 'r', encoding='utf-8-sig', errors='replace') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Participant ID' in row and 'Gender' in row:
                        participant_id = row['Participant ID'].strip()
                        gender = row['Gender'].strip()
                        gender_dict[participant_id] = gender
        return gender_dict
    
    def _build_trial_to_group_map(self) -> Dict[int, Tuple[str, str, str]]:
        """Build a mapping from trial number to group information"""
        trial_map = {}
        for lane, traffic_type, yield_type, trials in GROUPS:
            for trial_num in trials:
                trial_map[trial_num] = (lane, traffic_type, yield_type)
        return trial_map
    
    def process_all_files(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Process all trial data files in the directory"""
        all_data = []
        NO_COLLISIONS = []
        ONE_COLLISION = []
        MULTIPLE_COLLISIONS = []
        
        # Get all trial data files
        trial_files = sorted(self.data_dir.glob("*-AllTrials-data-*.txt"))
        
        print(f"Found {len(trial_files)} trial data files")
        
        for file_path in trial_files:
            # Extract participant ID from filename
            participant_id = file_path.name.split('-')[0]
            
            # Get gender
            gender = self.gender_data.get(participant_id, "Unknown")
            
            total_collisions = 0
            # Read the trial data
            # Note: The CSV files have trailing commas that need to be removed
            # Header: 23 columns ["Trial", "Lane", "Traffic", ...]
            # Data: 23 values + trailing comma
            # After removing trailing comma, data matches headers exactly
            try:
                # Read all lines and clean them
                try:
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        lines = f.readlines()
                except UnicodeDecodeError:
                    # Fallback for Windows generated files or invalid characters
                    with open(file_path, 'r', encoding='cp1252', errors='replace') as f:
                        lines = f.readlines()
                
                if not lines:
                    continue

                # First line is headers
                header_line = lines[0].strip()
                
                # Clean data lines - remove trailing commas
                cleaned_lines = [header_line]  # Keep original header
                for line in lines[1:]:
                    line = line.strip()
                    if line:
                        # Remove trailing comma if present
                        if line.endswith(','):
                            line = line[:-1]
                        cleaned_lines.append(line)
                
                # Write to temporary cleaned file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as tmp:
                    tmp.write('\n'.join(cleaned_lines))
                    tmp_path = tmp.name
                
                # Now read the cleaned CSV
                df = pd.read_csv(tmp_path, encoding='utf-8')
                
                # Clean up temp file
                import os
                os.unlink(tmp_path)
                
                # Rename 'Trial' column to 'TrialNumber' for clarity
                df = df.rename(columns={'Trial': 'TrialNumber'})
                
                rows_processed = 0
    
                # Process each trial row
                for idx, row in df.iterrows():
                    # Skip empty rows - check if TrialNumber value is null or empty
                    if 'TrialNumber' not in df.columns:
                        continue
                        
                    trial_value = row['TrialNumber']
                    
                    # Convert to string and check if empty
                    trial_str = str(trial_value).strip()
                    if trial_str == '' or trial_str == 'nan':
                        continue
                    
                    try:
                        trial_num = int(float(trial_value))
                    except (ValueError, TypeError):
                        # Skip rows with invalid trial numbers
                        continue
                    
                    # Get group information
                    if trial_num in self.trial_to_group:
                        lane, traffic_type, yield_type = self.trial_to_group[trial_num]
                    else:
                        lane = "Unknown"
                        traffic_type = "Unknown"
                        yield_type = "Unknown"
                    
                    # Get eHMI type from TRIAL_MAP
                    ehmi_type = TRIAL_MAP.get(trial_num, "N/A")
                    
                    # Build processed row
                    processed_row = {
                        'Participant_ID': participant_id,
                        'Gender': gender,
                        'Lane': lane,
                        'Traffic_Type': traffic_type,
                        'TrialNumber': trial_num,
                        'eHMI_Type': ehmi_type,
                        'Yield_Type': yield_type,
                        
                        # Timing columns
                        'Waiting_Time': self._calculate_waiting_time(row) or 'Invalid Trial Value',
                        'Crossing_Time': self._calculate_crossing_time(row) or 'Invalid Trial Value',
                        'Total_Trial_Time': self._calculate_total_time(row) or 'Invalid Trial Value',
                        'Timing_of_Entry': self._calculate_entry_time(row) or 'N/A',
                        
                        # Collision information
                        'Collision_Count': total_collisions,
                        'First_Car_Collision': self._check_collision(row, 'First'),
                        'Second_Car_Collision': self._check_collision(row, 'Second'),
                        
                        # Raw timing data
                        'Pedestrian_Enter_Time': self._safe_float(row.get('Pedestrian_Enter_time', 'N/A')),
                        'Pedestrian_Exit_Time': self._safe_float(row.get('Pedestrian_Exit_Time', 'N/A')),
                        'First_Car_Creation_Time': self._safe_float(row.get('First_Car_Creation_Time', 'N/A')),
                        'First_Car_Stop_Time': self._safe_float(row.get('First_Car_Stop_Time', 'N/A')),
                        'First_Car_eHMI_ON_Time': self._safe_float(row.get('First_Car_eHMI_ON_Time', 'N/A')),
                        'First_Car_eHMI_OFF_Time': self._safe_float(row.get('First_Car_eHMI_OFF_Time', 'N/A')),
                        'Second_Car_Creation_Time': self._safe_float(row.get('Second_Car_Creation_Time', 'N/A')),
                        'Second_Car_Stop_Time': self._safe_float(row.get('Second_Car_Stop_Time', 'N/A')),
                    }
                    has_collision = self._get_collision(row)
                    total_collisions += 1 if has_collision == 1 else 0
                    
                    
                    # Only include collision time if there was actually a collision
                    collision_time = self._safe_float(row.get('Collision_Time', 'N/A'))
                    if collision_time is not None and has_collision != 0:
                        processed_row['Collision_Time'] = collision_time
                    
                    all_data.append(processed_row)
                    rows_processed += 1
                
                print(f"  Processed {rows_processed} trials from {file_path.name}")
                
                # Create dataframe for each participant
                current_participant = pd.DataFrame(all_data[-36:len(all_data)])

                # Add Dataframe to appropriate list (No Collisions, One Collision, Multiple Collisions)
                if total_collisions == 0 :
                    NO_COLLISIONS.append(current_participant)
                elif total_collisions == 1:
                    ONE_COLLISION.append(current_participant)
                else:
                    MULTIPLE_COLLISIONS.append(current_participant)
                    
            except Exception as e:
                print(f"Error processing {file_path.name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return NO_COLLISIONS, ONE_COLLISION, MULTIPLE_COLLISIONS
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float, return None if N/A or invalid"""
        if pd.isna(value) or value == 'N/A' or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _calculate_waiting_time(self, row) -> float:
        """Calculate waiting time: Pedestrian Road Enter Time - First Car Creation Time"""
        enter_time = self._safe_float(row.get('Pedestrian_Enter_time', 'N/A'))
        first_car_time = self._safe_float(row.get('First_Car_Creation_Time', 'N/A'))
        
        if enter_time is not None and enter_time != -1 and first_car_time is not None:
            return round(enter_time - first_car_time, 2)
        return None
    
    def _calculate_crossing_time(self, row) -> float:
        """Calculate crossing time: Exit Time - Enter Time"""
        exit_time = self._safe_float(row.get('Pedestrian_Exit_Time', 'N/A'))
        enter_time = self._safe_float(row.get('Pedestrian_Enter_time', 'N/A'))
        
        if exit_time is not None and enter_time is not None and enter_time != exit_time:
            return round(exit_time - enter_time, 2)
        return None
    
    def _calculate_total_time(self, row) -> float:
        """Calculate total trial time: Exit Time - First Car Creation Time"""
        exit_time = self._safe_float(row.get('Pedestrian_Exit_Time', 'N/A'))
        first_car_time = self._safe_float(row.get('First_Car_Creation_Time', 'N/A'))
        
        if exit_time is not None and exit_time != -1 and first_car_time is not None:
            return round(exit_time - first_car_time, 2)
        return None

    def _calculate_entry_time(self, row) -> float:
        """Calculate entry time: Pedestrian Road Enter Time - First eHMI On Time"""
        enter_time = self._safe_float(row.get('Pedestrian_Enter_time', 'N/A'))
        first_car_time = self._safe_float(row.get('First_Car_eHMI_ON_Time', 'N/A'))
        
        if enter_time is not None and first_car_time is not None:
            return round(enter_time - first_car_time, 2)
        return None
    
    def _check_collision(self, row, car_type: str) -> str:
        """Check if there was a collision with specified car (First or Second)"""
        collision_car = str(row.get('Collision_Car', 'N/A')).strip()

        if car_type in collision_car:
            return '1/1'
        
        return '0/1'
    
    def _get_collision(self, row) -> int:
        """Check if any collision occurred"""
        collision_car = str(row.get('Collision_Car', 'N/A')).strip()
        if collision_car == 'nan':
            return 0 # no collision

        return 1 # collision found
    
    def _get_combined_means(self, list):
        combined = []
        for df in list:
            pre_collision_yield_sum = 0.0
            total_pre_coll_yield_trials = 0

            post_collision_yield_sum = 0.0
            total_post_coll_yield_trials = 0

            pre_collision_no_yield_sum = 0.0
            total_pre_coll_no_yield_trials = 0

            post_collision_no_yield_sum = 0.0
            total_post_coll_no_yield_trials = 0

            pre_collision_fail_sum = 0.0
            total_pre_coll_fail_trials = 0

            post_collision_fail_sum = 0.0
            total_post_coll_fail_trials = 0

            collision_passed = False
            for _, row in df.iterrows():
                if row['Waiting_Time'] != 'Invalid Trial Value':
                    if collision_passed:
                        if row['Yield_Type'] == 'Yield':
                            post_collision_yield_sum += row['Waiting_Time']
                            total_post_coll_yield_trials += 1
                        elif row['Yield_Type'] == 'No Yield':
                            post_collision_no_yield_sum += row['Waiting_Time']
                            total_post_coll_no_yield_trials += 1
                        else:
                            post_collision_fail_sum += row['Waiting_Time']
                            total_post_coll_fail_trials += 1
                    else:
                        if row['Yield_Type'] == 'Yield':
                            pre_collision_yield_sum += row['Waiting_Time']
                            total_pre_coll_yield_trials += 1
                        elif row['Yield_Type'] == 'No Yield':
                            pre_collision_no_yield_sum += row['Waiting_Time']
                            total_pre_coll_no_yield_trials += 1
                        else:
                            pre_collision_fail_sum += row['Waiting_Time']
                            total_pre_coll_fail_trials += 1
                
                if row['Collision_Count'] > 0:
                    collision_passed = True
            
            pre_collision_yield_avg = round(pre_collision_yield_sum / float(total_pre_coll_yield_trials), 2) if total_pre_coll_yield_trials != 0 else 'N/A'
            post_collision_yield_avg = round(post_collision_yield_sum / float(total_post_coll_yield_trials), 2) if total_post_coll_yield_trials != 0 else 'N/A'
            yield_waiting_diff = round(post_collision_yield_avg - pre_collision_yield_avg, 2) if pre_collision_yield_avg != 'N/A' and post_collision_yield_avg != 'N/A' else 'N/A'

            pre_collision_no_yield_avg = round(pre_collision_no_yield_sum / float(total_pre_coll_no_yield_trials), 2) if total_pre_coll_no_yield_trials != 0 else 'N/A'
            post_collision_no_yield_avg = round(post_collision_no_yield_sum / float(total_post_coll_no_yield_trials), 2) if total_post_coll_no_yield_trials != 0 else 'N/A'
            no_yield_waiting_diff = round(post_collision_no_yield_avg - pre_collision_no_yield_avg, 2)  if pre_collision_no_yield_avg != 'N/A' and post_collision_no_yield_avg != 'N/A' else 'N/A'

            pre_collision_fail_avg = round(pre_collision_fail_sum / float(total_pre_coll_fail_trials), 2) if total_pre_coll_fail_trials != 0 else 'N/A'
            post_collision_fail_avg = round(post_collision_fail_sum / float(total_post_coll_fail_trials), 2) if total_post_coll_fail_trials != 0 else 'N/A'
            fail_waiting_diff = round(post_collision_fail_avg - pre_collision_fail_avg, 2) if pre_collision_fail_avg != 'N/A' and post_collision_fail_avg != 'N/A' else 'N/A'


            data = {
                'Participant_ID': df.iloc[0]['Participant_ID'],
                'Gender': df.iloc[0]['Gender'],
                'Mean Waiting time Pre Collision (Yield)': pre_collision_yield_avg,
                'Mean Waiting time Post Collision (Yield)': post_collision_yield_avg,
                'Difference Pre and Post Collision (Yield)': yield_waiting_diff,
                'Mean Waiting time Pre Collision (No Yield)': pre_collision_no_yield_avg,
                'Mean Waiting time Post Collision (No Yield)': post_collision_no_yield_avg,
                'Difference Pre and Post Collision (No Yield)': no_yield_waiting_diff,
                'Mean Waiting time Pre Collision (No Yield Failure)': pre_collision_fail_avg,
                'Mean Waiting time Post Collision (No Yield Failure)': post_collision_fail_avg,
                'Difference Pre and Post Collision (No Yield Failure)': fail_waiting_diff
            }
            combined.append(data)
        return combined
    
    def save_results(self, NO_COLLISIONS: pd.DataFrame,ONE_COLLISION: pd.DataFrame, MULTIPLE_COLLISIONS: pd.DataFrame, output_file: str):
        """Save processed results to CSV - creates two versions: one with eHMI_Type, one with Yield_Type"""
        output_path = Path(output_file)
        
        # File 1: No Collision CSV
        # File 5: Mean - No Collision Group CSV
        if len(NO_COLLISIONS) > 0:
            print(f"\nTotal zero collision participants: {len(NO_COLLISIONS)}")
            no_collision_path = output_path.parent / f"{output_path.stem}_no_coll{output_path.suffix}"
            self._generate_collision_csv(NO_COLLISIONS, no_collision_path)

            mean_no_collision_path = output_path.parent / f"{output_path.stem}_mean_no_coll{output_path.suffix}"
            self._generate_mean_wait_no_coll_csv(NO_COLLISIONS, mean_no_collision_path)
        else:
            print("WARNING: No data was processed for zero collisions!")

        # File 2: One Collision CSV
        if len(
            
            ONE_COLLISION) > 0:
            print(f"\nTotal one collision participants: {len(ONE_COLLISION)}")
            one_collision_path = output_path.parent / f"{output_path.stem}_one_coll{output_path.suffix}"
            self._generate_collision_csv(ONE_COLLISION, one_collision_path)
        else:
            print("WARNING: No data was processed for zero collisions!")
        
        # File 3: Two (or more) Collision CSV
        if len(MULTIPLE_COLLISIONS) > 0:
            print(f"\nTotal multiple collision participants: {len(MULTIPLE_COLLISIONS)}")
            multi_collision_path = output_path.parent / f"{output_path.stem}_multi_coll{output_path.suffix}"
            self._generate_collision_csv(MULTIPLE_COLLISIONS, multi_collision_path)
        else:
            print("WARNING: No data was processed for multiple collisions!")

        # File 4: Mean - Collision Group CSV
        if (len(ONE_COLLISION) + len(MULTIPLE_COLLISIONS)) > 0:
            print(f'\nTotal Collision Participants: {len(ONE_COLLISION) + len(MULTIPLE_COLLISIONS)}')
            mean_collision_path = output_path.parent / f"{output_path.stem}_mean_coll{output_path.suffix}"
            self._generate_mean_collision_csv(ONE_COLLISION, MULTIPLE_COLLISIONS, mean_collision_path)

    def _generate_collision_csv(self, list, output_path: Path):
        """Generate Collision CSV, all 36 trials per participant"""
        combined = []
        for df in list:
            for _, row in df.iterrows():
                ehmi_label = f'eHMI {row['eHMI_Type']}' if row['eHMI_Type'] != 'N/A' else 'N/A'
                row['eHMI_Type'] = ehmi_label
                combined.append(row)
        
        combined_df = pd.DataFrame(combined)
        part_df = combined_df[[
            'Participant_ID', 
            'Gender', 
            'Lane', 
            'Traffic_Type', 
            'TrialNumber', 
            'Yield_Type',
            'eHMI_Type', 
            'Waiting_Time', 
            'Timing_of_Entry',
            'Crossing_Time',
            'Total_Trial_Time',
            'Collision_Count'
        ]]
        part_df.to_csv(output_path, index=False)
        print(f"Detailed results saved to: {output_path}")

    def _generate_mean_collision_csv(self, one_coll, multi_coll, output_path: Path):
        """Generate the Mean Pre- and Post- Collision Waiting Times, one row per participant"""
        one_collision_combined = self._get_combined_means(one_coll)
        multi_collision_combined = self._get_combined_means(multi_coll)

        all_means = one_collision_combined + multi_collision_combined

        combined_df = pd.DataFrame(all_means)
        combined_df.to_csv(output_path, index=False)
        print(f"Detailed results saved to: {output_path}")

    def _generate_mean_wait_no_coll_csv(self, list, output_path: Path):
        """Generate the Mean Waiting Times, one row per participant"""
        means = []
        
        for df in list:
            yield_wait_sum = 0.0
            total_yield_trials = 0

            no_yield_wait_sum = 0.0
            total_no_yield_trials = 0

            fail_wait_sum = 0.0
            total_fail_trials = 0

            for _, row in df.iterrows():
                if row['Waiting_Time'] != 'Invalid Trial Value' and row['Waiting_Time'] >= 0:
                    if row['Yield_Type'] == 'Yield':
                        yield_wait_sum += row['Waiting_Time']
                        total_yield_trials += 1
                    elif row['Yield_Type'] == 'No Yield':
                        no_yield_wait_sum += row['Waiting_Time']
                        total_no_yield_trials += 1
                    else:
                        fail_wait_sum += row['Waiting_Time']
                        total_fail_trials += 1

            yield_avg = round(yield_wait_sum / float(total_yield_trials), 2) if total_yield_trials != 0 else 'N/A'
            no_yield_avg = round(no_yield_wait_sum / float(total_no_yield_trials), 2) if total_no_yield_trials != 0 else 'N/A'
            fail_avg = round(fail_wait_sum / float(total_fail_trials), 2) if total_fail_trials != 0 else 'N/A'

            data = {
                'Participant_ID': df.iloc[0]['Participant_ID'],
                'Gender': df.iloc[0]['Gender'],
                'Mean Waiting Time (Yield)': yield_avg,
                'Mean Waiting Time (No Yield)': no_yield_avg,
                'Mean Waiting Time (No Yield Failure)': fail_avg
            }
            means.append(data)
        
        means_df = pd.DataFrame(means)
        means_df.to_csv(output_path, index=False)
        print(f"Detailed results saved to: {output_path}")

def main():
    """Main execution function"""
    import argparse
    parser = argparse.ArgumentParser(description="Process Trial Data")
    parser.add_argument("--base_dir", default=r"C:\\Users\\kypar\\Desktop\\school\\sp26\\senior-research\\research-project_2\\Post_Processing_Files", help="Base directory path")
    args = parser.parse_args()
    
    # Set up paths
    base_dir = Path(args.base_dir)
    # data_dir = base_dir / "AllTrials_Allparticipants"
    data_dir = base_dir / "SP26_AllTrials_data"
    # gender_file = base_dir / "Gender_Details.csv"
    gender_file = base_dir / "Gender_Details_sp26.csv"
    
    # Output files
    output_detailed = base_dir / "Test_SP26_Output" / "processed_data.csv"
    # output_detailed = base_dir / "Output" / "processed_data.csv"
    
    print("=" * 60)
    print("TRIAL DATA PROCESSING SCRIPT")
    print("=" * 60)
    
    # Initialize processor
    processor = TrialDataProcessor(data_dir, gender_file)
    
    # Process all files
    print("\nProcessing trial data files...")
    NO_COLLISIONS, ONE_COLLISION, MULTIPLE_COLLISIONS = processor.process_all_files()
    
    # Save detailed results
    processor.save_results(NO_COLLISIONS, ONE_COLLISION, MULTIPLE_COLLISIONS, output_detailed)
    
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
