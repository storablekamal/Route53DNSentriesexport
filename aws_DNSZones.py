import csv
import json
import boto3
import subprocess

def get_account_ids_from_json(json_filename):
    with open(json_filename, 'r') as json_file:
        data = json.load(json_file)
    return data
        
def get_all_hosted_zones(account_id, profile, json_writer):
    try:
        hosted_zones_data = []
        # Get all hosted zones for the specified profile
        result = subprocess.run(['aws', 'route53', 'list-hosted-zones', '--profile', profile], capture_output=True, text=True)
        hosted_zones = json.loads(result.stdout)['HostedZones']
        for zone in hosted_zones:
            hosted_zone_data = {
                'AccountID': account_id,
                'HostedZoneId': zone['Id'],
                'HostedZoneName': zone['Name'],
                'PrivateZone': zone['Config']['PrivateZone'] if 'Config' in zone else False
            }
            

            hosted_zones_data.append(hosted_zone_data)
        # return [zone['HostedZoneName'].split('/')[-1] for zone in hosted_zones]
        json_writer.extend(hosted_zones_data)

    except Exception as e:
        print(f"Error getting all hosted zones for profile {profile}: {e}")
        return []

def compare_hosted_zone_with_csv(hosted_zones, csv_filename, exclude_domain='gmail.com'):
    dns_names_to_compare = set()
    with open(csv_filename, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            domain_name = row['domain_name'].lower()
            if exclude_domain not in domain_name:
                dns_names_to_compare.add(domain_name)

    matched_zones = []

    for zone in hosted_zones: 
        if zone['HostedZoneName'].lower() in dns_names_to_compare:
            matched_zones.append(zone)
    
    return matched_zones

def export_dkim_cname_records_to_csv(account_id, hosted_zone_id, csv_writer, account_name):
    session = boto3.Session(profile_name=account_name)
    route53_client = session.client('route53')

    try:
        response = route53_client.list_resource_record_sets(HostedZoneId=hosted_zone_id)
        print(response)
        dkim_cname_records = [record['Name'] for record in response['ResourceRecordSets'] if record['Type'] == 'CNAME' and 'dkim' in record['Name'].lower()]

        for record in dkim_cname_records:
            csv_writer.writerow({'AccountID': account_id, 'HostedZoneId': hosted_zone_id, 'DKIM_CNAME_Record': record})
    
    except Exception as e:
        print(f"Error exporting DKIM CNAME records in hosted zone {hosted_zone_id}: {e}")

def main():
    json_filename = 'aws_accounts.json'
    csv_filename = 'dkim.csv'
    csv_filename_dkim = 'dkim_cname_records.csv'

    json_data = []
    account_ids = get_account_ids_from_json(json_filename)

    all_load_balancers = []

    for account in account_ids:
        account_name = (account[0])
        account_id = (account[1])
        get_all_hosted_zones(account_id, account_name, json_data)

    matched_zones = compare_hosted_zone_with_csv(json_data, csv_filename)

    print("Matched Hosted Zones:")

    for zone in matched_zones:
        print(f"AccountID: {zone['AccountID']}, HostedZoneId: {zone['HostedZoneId']}, HostedZoneName: {zone['HostedZoneName']}, PrivateZone: {zone['PrivateZone']}")
        export_dkim_cname_records_to_csv(zone['AccountID'], zone['HostedZoneId'], csv_filename_dkim, account_name)

    print(f"Data Exported to {csv_filename_dkim}")

if __name__ == "__main__":
    main()

