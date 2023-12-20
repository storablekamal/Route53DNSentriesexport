import csv
import json
import subprocess
import boto3

def get_account_ids_from_json(json_filename):
    with open(json_filename, 'r') as json_file:
        data = json.load(json_file)
    return data

def sso_login(profile_name):
    try:
        subprocess.run(['aws', 'sso', 'login', '--profile', profile_name], check=True)
        print(f"Successfully logged in with AWS SSO profile: {profile_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error LOgging in with AWS SSO profile: {profile_name}\n{e}")
        
def export_network_acls_to_csv(account_id, region, network_acls, csv_writer):
    for acl in network_acls:
        is_default = acl.get('IsDefault', False)
        acl_id = acl['NetworkAclId']

        entry = {
            'AccountID': account_id,
            'Region': region,
            'NetworkAclID': acl_id,
            'IsDefault': is_default
        }
        print(entry)
        csv_writer.writerow(entry)

def main():

    json_filename = 'aws_accounts.json'
    csv_filename = 'output.csv'
    # sso_profile = 'se-staging-fms'

    account_ids = get_account_ids_from_json(json_filename)
    # accounts = seperate_account_id_name(account_ids)

    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['AccountID', 'Region', 'NetworkAclID', 'IsDefault']
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csv_writer.writeheader() 

        for account in account_ids:
            # sso_login(sso_profile)
            account_name = (account[0])
            account_id = (account[1])

            session = boto3.Session(profile_name=account_name)
            regions = ['us-east-2', 'ap-northeast-3', 'eu-west-1', 'eu-north-1', 'ca-central-1', 'ap-northeast-2', 'ap-south-1', 'us-east-1', 'us-west-1', 'eu-west-3', 'sa-east-1', 'us-west-2', 'ap-southeast-1', 'eu-central-1', 'ap-southeast-2', 'ap-northeast-1', 'eu-west-2']
        
            for region in regions:
                ec2_client = session.client('ec2', region_name=region)

                try:
                    response = ec2_client.describe_network_acls()
                    network_acls = response['NetworkAcls']
                    export_network_acls_to_csv(account_id, region, network_acls, csv_writer)

                except Exception as e:
                    print(f"Error Describing network ACLs in account {account_id}, region {region}: {e}")

    print(f"Data exported to {csv_filename}")

if __name__ == "__main__":
    main()        