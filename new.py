import boto3
import csv
import json

def get_account_ids_from_json(json_filename):
    with open(json_filename, 'r') as json_file:
        data = json.load(json_file)
    return data
    
def import_aws_zones_from_json(json_file_path):
    try: 
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)

            if 'zones' in data and isinstance(data['zones'], list):
                aws_zones = data['zones']

                regions = list(set(zone['region'] for zone in aws_zones))
                return regions
            else:
                print("invalid JSON format")
                return None
        
    except FileNotFoundError:
        print(f"File not found: {json_file_path}")
        return None
    
    except json.JSONDecodeError:
        print(f"Error Decoding Json file: {json_file_path}")
        return None
    

def list_hosted_zones(account_id):
    session = boto3.session.Session(profile_name=f'st-security-ro-{account_id}')
    route53_client = session.client('route53')

    try:
        response = route53_client.list_hosted_zones()
        return response['HostedZones']
    
    except Exception as e:
        print(f"Error listing the hosted Zone: {e}")
        return None


def list_resource_record_sets(account_id, hosted_zone_id):
    session = boto3.session.Session(profile_name=f'st-security-ro-{account_id}')
    route53_client = session.client('route53')

    try:
        response = route53_client.list_resource_record_sets(HostedZoneId=hosted_zone_id)
        return response

    
    except Exception as e:
        # print(f"Error listing resource record set: {e} {account_id}")
        return None
    
    
def get_load_balancer_arn_for_dns_name(account_id, dns_name):
    json_file_path = 'aws-region-names.json'

    regions = import_aws_zones_from_json(json_file_path)

    for region in regions:
        session = boto3.session.Session(profile_name=f'st-security-ro-{account_id}')
        elbv2_client = session.client('elbv2', region)

        try:
            response = elbv2_client.describe_load_balancers()
            load_balancers = response['LoadBalancers']
            for lb in load_balancers:
                if dns_name==lb['DNSName'] + '.':
                    return lb['LoadBalancerArn']
                elif dns_name=='dualstack.' + lb['DNSName'] + '.':
                    return lb['LoadBalancerArn']

        except Exception as e:
            print(f"Error describing load balancers: {e}")
            return None

def export_to_csv(data, csv_filename):
    if not data:
        print("No data to export.")
        return
    
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)

        print(f"Data exported to {csv_filename}")


    
def main():
    json_filename = 'accounts.json'
    csv_filename = 'output.csv'

    account_ids = get_account_ids_from_json(json_filename)
    all_entries = []

    for account_id in account_ids:
        hosted_zones = list_hosted_zones(account_id)

        if hosted_zones:
            for zone in hosted_zones:
                hosted_zone_id = zone['Id']
                records = list_resource_record_sets(account_id, hosted_zone_id)

                if records: 
                    for record in records['ResourceRecordSets']:
                        # print(record)
                        Name = record['Name']
                        record_type = record['Type']

                        if record_type in ['A', 'CNAME']:
                            value = None

                            if 'ResourceRecords' in record:
                                value = record['ResourceRecords'][0]['Value']

                            elif 'AliasTarget' in record:
                                value = record['AliasTarget']['DNSName']
                            
                            dns_name = value
                            # print(dns_name)
                            lb_arns = get_load_balancer_arn_for_dns_name(account_id, dns_name)
                            

                            entry = {
                                'AccountID': account_id,
                                'HostedZoneName': zone['Name'],
                                'RecordName': dns_name,
                                'RecordType': record['Type'],
                                'LoadBalancerARNs': lb_arns
                            }
                            print(entry)
                            all_entries.append(entry)
        export_to_csv(all_entries, csv_filename)
    
if __name__ == "__main__":
    main()        

