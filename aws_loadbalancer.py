import csv
import json
import boto3

def get_account_ids_from_json(json_filename):
    with open(json_filename, 'r') as json_file:
        data = json.load(json_file)
    return data
        
def get_load_balancers(account_name, region): 
    session = boto3.Session(profile_name=account_name)
    elbv2_client = session.client('elbv2', region)

    try:
        response = elbv2_client.describe_load_balancers()
        return response['LoadBalancers']
    
    except Exception as e:
        print("Error getting load balancers for account id {account_id}")
        return []
    
def export_to_csv(all_load_balancers, csv_file):
    fieldnames = ['AccountID', 'LoadBalancerArn', 'LoadBalancerName', 'DNSName', 'Type']

    with open(csv_file, mode='w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader() 

        for lb in all_load_balancers:
            writer.writerow({
                'AccountID': lb.get('Account', ''),
                'LoadBalancerName': lb.get('LoadBalancerName', ''),
                'LoadBalancerArn': lb.get('LoadBalancerArn', ''),
                'DNSName': lb.get('DNSName', ''),
                'Type': lb.get('Type', ''),
            })   

if __name__ == "__main__":

    json_filename = 'aws_accounts.json'
    csv_filename = 'output.csv'
   
    account_ids = get_account_ids_from_json(json_filename)

    all_load_balancers = []

    for account in account_ids:
        account_name = (account[0])
        account_id = (account[1])

        regions = ['us-east-2', 'us-east-1', 'us-west-1', 'us-west-2']

        for region in regions:

            print(f"Exporting load balancers for account {account_name} in {region}")
            load_balancers = get_load_balancers(account_name, region)
            all_load_balancers.extend(load_balancers)
        

            print(f"Exported {len(load_balancers)} load balancers for account ID {account_name}")

    csv_file_name = "all_load_balancer.csv"
    export_to_csv(all_load_balancers, csv_file_name)

    print(f"Exported {len(all_load_balancers)} load balancers to {csv_file_name}")



    