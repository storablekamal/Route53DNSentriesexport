import subprocess
import json
import os
import csv
from configparser import ConfigParser
import signal
import sys

def cleanup():
    print("\nScript terminated. Cleaning up...")
    # Add any cleanup operations here if needed
    sys.exit(0)

def handle_interrupt(signum, frame):
    cleanup()

def get_aws_profiles():
    # Parse the AWS CLI config file to get a list of profiles
    config = ConfigParser()
    config_file_path = os.path.expanduser("~/.aws/config")

    try:
        config.read(config_file_path)
        profiles = [section.replace('profile ', '') for section in config.sections() if section.startswith('profile ')]
        return profiles
    except Exception as e:
        print(f"Error reading AWS profiles from {config_file_path}: {e}")
        return []

def get_all_hosted_zones(profile):
    try:
        # Get all hosted zones for the specified profile
        result = subprocess.run(['aws', 'route53', 'list-hosted-zones', '--profile', profile], capture_output=True, text=True)
        hosted_zones = json.loads(result.stdout)['HostedZones']
        return [zone['Id'].split('/')[-1] for zone in hosted_zones]
    except Exception as e:
        print(f"Error getting all hosted zones for profile {profile}: {e}")
        return []

def get_records_for_hosted_zone(profile, hosted_zone_id):
    try:
        # Get records for the specified hosted zone
        result = subprocess.run(['aws', 'route53', 'list-resource-record-sets', '--hosted-zone-id', hosted_zone_id, '--profile', profile], capture_output=True, text=True)
        records = json.loads(result.stdout)['ResourceRecordSets']
        return records
    except Exception as e:
        print(f"Error getting records for hosted zone {hosted_zone_id} in profile {profile}: {e}")
        return None

def filter_records(records):
    # Filter Type A records with alias settings or CNAME values
    filtered_records = [record for record in records if
                        (record['Type'] == 'A' and 'AliasTarget' in record) or record['Type'] == 'CNAME']
    return filtered_records

def print_record(profile, record, show_stdout=False):
    record_type = record['Type']
    record_name = record['Name']
    
    if record_type == 'A' and 'AliasTarget' in record:
        # If it's an A record with AliasTarget, use DNSName as the value
        record_value = record['AliasTarget']['DNSName']
    else:
        record_value = record.get('ResourceRecords', [{}])[0].get('Value', 'N/A')

    if show_stdout:
        # Print record to stdout with a new line character
        print(f"Profile: {profile}, Type: {record_type}, Name: {record_name}, Value: {record_value}\n")

    return profile, record_type, record_name, record_value

def write_to_csv(data):
    with open('route53zones.csv', 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(data)

def main(profile=None, show_stdout=False):
    # Set up signal handlers for graceful termination
    signal.signal(signal.SIGINT, handle_interrupt)
    signal.signal(signal.SIGTERM, handle_interrupt)

    # Clear the existing CSV file or create a new one
    with open('route53zones.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Profile', 'Record Type', 'Record Name', 'Record Value'])

    profiles = [profile] if profile else get_aws_profiles()

    for profile in profiles:
        print(f"Profile: {profile}")
        print("Processing Records...")

        hosted_zone_ids = get_all_hosted_zones(profile)
        if hosted_zone_ids:
            for hosted_zone_id in hosted_zone_ids:
                records = get_records_for_hosted_zone(profile, hosted_zone_id)
                if records:
                    filtered_records = filter_records(records)
                    if filtered_records:
                        for record in filtered_records:
                            data = print_record(profile, record, show_stdout)
                            write_to_csv(data)

        print("Completed\n")

    print("Processing complete.")

if __name__ == "__main__":
    profile = None
    show_stdout = False

    # Parse command-line arguments
    args = iter(sys.argv[1:])
    for arg in args:
        if arg == '-p':
            profile = next(args, None)
        elif arg == '-stdout':
            show_stdout = True

    main(profile=profile, show_stdout=show_stdout)

