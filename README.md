# Route53DNSentriesexport

This code is wrritten to export the list of Route53DNSEntries from all of our AWS accounts using AWS IAM Identity Center and then export the Load Balancer ARN associated to the specific A and CNAME record Route53 Entries. 

Before executing the code we should have proper privileges to list Route53 and List EC2 privileges. 

**Step1:-**
1. Clone the directory to your local machine.
2. Update the accounts.json file as all of your account ids in your organization.
3. Update the region names in aws-region-names.json as per resource deployment in storable.
4. Run aws configure sso in the terminal window and login to any accoune using associated role.
5. Run the new.py file using python3 as it has modules which are not available in python. 

Note:- Before executing the file please make sure you have boto, json and csv modules already avalable in your local python directory. 
