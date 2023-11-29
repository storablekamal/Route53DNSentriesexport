import boto3
import csv
import json

input_json = "account_ids.json"
output_csv = 'dns_entries.csv'

def process_records(records, csv_writer, account_id, hosted_zone_name):
    for record in records['ResourceRecordSets']:
        name = record['Name']
        record_type = record['Type']

        if record_type in ['A', 'CNAME']:
            value = None

            if 'ResourceRecords' in record:
                value = record['ResourceRecords'][0]['Value']
            elif 'AliasTarget' in record:
                value = record['AliasTarget']['DNSName']
            
            csv_writer.writerow(["'" + str(account_id), hosted_zone_name, name, record_type, value])
            
# Get a list of account IDs in the organization
with open(input_json, 'r') as json_file:
    account_ids = json.load(json_file)

# Loop through each account and list DNS entries for each hosted zone 
with open(output_csv, mode='w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Account ID', 'Hosted Zone Name', 'Name', 'Type', 'Value'])

    for account_id in account_ids:
        print (f"Processing Account ID: {account_id}")

        # Use AWS Identity Center Profile
        session = boto3.session.Session(profile_name=f'st-security-ro-{account_id}') 
        route53_client = session.client('route53')
        
        #list Hosted Zones
        hosted_zones = route53_client.list_hosted_zones()['HostedZones']
 
        #Loop Through each hosted zone and list DNS Entries
        for hosted_zone in hosted_zones:
            hosted_zone_id = hosted_zone['Id'].split('/')[-1]
            hosted_zone_name = hosted_zone['Name']
            # List DNS entries for each hosted zone
            resource_record_sets = route53_client.list_resource_record_sets(
                HostedZoneId=hosted_zone_id
            )
            
            # Convert DNS entries to CSV
            if (resource_record_sets):
            #  for record_set in resource_record_sets: 
                process_records(resource_record_sets, csv_writer, account_id, hosted_zone_name)
                  
print("CSV file exported to: [output_csv}")
