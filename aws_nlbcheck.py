import csv
import subprocess
import json
import time
from concurrent.futures import ThreadPoolExecutor

def describe_load_balancer(args):
    profile, region, dns_value, record_type = args
    command = [
        "aws",
        "elbv2",
        "describe-load-balancers",
        "--region",
        region,
        "--profile",
        profile,
        "--query",
        f"LoadBalancers[?DNSName=='{dns_value}'].{{ARN:LoadBalancerArn,Type:Type,AccountId:LoadBalancerAttributes[?Key=='owner_account_id'].Value | [0], DNSName: DNSName}}",
        "--output",
        "json",
    ]

    retries = 0
    while retries < 3:  # You can adjust the maximum number of retries
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error executing AWS CLI command: {result.stderr}")

            # Exponential backoff
            sleep_duration = 2 ** retries
            print(f"Retrying in {sleep_duration} seconds...")
            time.sleep(sleep_duration)
            retries += 1
        else:
            try:
                # Attempt to parse JSON output
                return json.loads(result.stdout), profile, record_type, dns_value
            except json.JSONDecodeError:
                print("Failed to decode JSON response.")
                return None

    print("Max retries reached. Exiting.")
    return None

# Specify the path to your CSV file
csv_file = "route53zones.csv"

# Specify the AWS region
aws_region = "us-west-2"

# Specify the output CSV file
output_csv_file = "nlb-waf-candidates.csv"

# Counters for skipped and matched records
skipped_records = 0
matched_records = 0

# List to store results
results = []

# Open the CSV file and read each line
with open(csv_file, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    tasks = [(row["Profile"], aws_region, row["Record Value"], row["Record Type"]) for row in reader]

    with ThreadPoolExecutor() as executor:
        with open(output_csv_file, 'a', newline='') as output_csv:
            fieldnames = ["Profile", "Record Type", "DNS Value (CSV)", "AWS Load Balancer ARN", "AWS Load Balancer Type", "AWS Owner Account ID", "AWS DNSName"]
            writer = csv.DictWriter(output_csv, fieldnames=fieldnames)

            # Write header if the file is newly created
            if output_csv.tell() == 0:
                writer.writeheader()

            for i, result in enumerate(executor.map(describe_load_balancer, tasks), start=1):
                if result:
                    if result[0] and result[0][0] and result[0][0]["Type"] == "network":
                        # ... (print and process the matched record)
                        print(f"Processing record {i}/{len(tasks)}: Profile: {result[1]}, Record Type: {result[2]}, DNS Value (CSV): {result[3]}")

                    # Print the results for matching records
                        print(f"AWS Load Balancer ARN: {result[0][0]['ARN']}")
                        print(f"AWS Load Balancer Type: {result[0][0]['Type']}")
                        print(f"AWS Owner Account ID: {result[0][0]['AccountId']}")
                        print(f"AWS DNSName: {result[0][0]['DNSName']}")
                        print("Match verified.\n")
                        
                        # Write to CSV
                        writer.writerow({
                            "Profile": result[1],
                            "Record Type": result[2],
                            "DNS Value (CSV)": result[3],
                            "AWS Load Balancer ARN": result[0][0]['ARN'],
                            "AWS Load Balancer Type": result[0][0]['Type'],
                            "AWS Owner Account ID": result[0][0]['AccountId'],
                            "AWS DNSName": result[0][0]['DNSName']
                        })

                        matched_records += 1
                    else:
                        # Skip records where load balancer type is not "network"
                        print(f"Skipping record {i}/{len(tasks)} with 'Application' Type: Profile: {result[1]}, Record Type: {result[2]}, DNS Value: {result[3]}\n")
                        skipped_records += 1


# Print the totals
print(f"Total of Skipped Records: {skipped_records}")
print(f"Total of Matched Records: {matched_records}")
