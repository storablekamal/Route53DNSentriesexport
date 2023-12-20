import csv
import boto3
import json

def get_account_ids_from_json(json_filename):
    with open(json_filename, 'r') as json_file:
        data = json.load(json_file)
    return data

def get_vpc_id_from_acl(acl_id, region, account_name):
    session = boto3.Session(profile_name=account_name)
    ec2_client = session.client('ec2', region_name=region)

    acl_info = ec2_client.describe_network_acls(NetworkAclIds=[acl_id])
    if 'NetworkAcls' in acl_info and acl_info['NetworkAcls']:
        vpc_id = acl_info['NetworkAcls'][0]['VpcId']
        return vpc_id
    else:
        return None
    
def check_vpc_usage(vpc_id, region, account_name):
    session = boto3.Session(profile_name=account_name)
    ec2_client = session.client('ec2', region_name=region)

    Instances = ec2_client.describe_instances(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Reservations']
    return bool(Instances)

def export_vpcs_to_csv(account_name, acl_id, used_vpcs, region, output_file):

    fieldnames = ['Account Name', 'ACL ID', 'Used VPC', 'Region']
    with open(output_file, 'a', newline='') as csv_file:    
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        for vpc in used_vpcs:
            writer.writerow({'Account Name': account_name, 'ACL ID': acl_id, 'Used VPC': vpc, 'Region': region})

if __name__ == "__main__":

    input_csv_file_path = 'input.csv'
    output_csv_file_path = 'output.csv'
    json_filename = 'aws_accounts.json'

    account_ids = get_account_ids_from_json(json_filename)

    for account in account_ids:
        account_name = (account[0])
        account_ID = (account[1])

        with open(input_csv_file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                acl_id = row['Resource ID']
                account_id = row['Account ID']
                region = row['Region']

                if account_id == account_ID:

                    vpc_id = get_vpc_id_from_acl(acl_id, region, account_name)

                    if vpc_id:
                        if check_vpc_usage(vpc_id, region, account_name):

                            export_vpcs_to_csv(account_name, acl_id, [vpc_id], region, output_csv_file_path)

                            print(f"ACL {acl_id} in account {account_name} in region {region} is assocaited with used VPC {vpc_id}.")

                        else:
                            print(f"ACL {acl_id} in account {account_name} in region {region} is assocaited with unused VPC {vpc_id}.")

                    else:
                        print(f"Could not find VPC associated with ACL {acl_id} in account {account_name} in region {region}.")

    print("Exported Used VPCs to:", output_csv_file_path)





    