import boto3
import sys
from botocore.exceptions import ClientError
import argparse

def paginate(method, **kwargs):
      client = method.__self__
      paginator = client.get_paginator(method.__name__)
      for page in paginator.paginate(**kwargs).result_key_iters():
          for result in page:
              yield result
              
parser = argparse.ArgumentParser(description='Fix Default SG in Security Alerts',
                                     formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--profile', required=True,
                    help='Pass AWS Profile of your SG to fix')
parser.add_argument('--sg-id', required=True,
                    help='Pass default SG id to fix')
args = parser.parse_args()
pr=args.profile
sg_id=args.sg_id
network_ifs=[]
try:    
    session = boto3.session.Session(profile_name=pr,region_name="us-east-1")
except Exception as e:
    sys.stderr.write("assume role got exception/{}/{}/{}\n".format(type(e),
                                                                    repr(e),
                                                                    str(e)))
    print(f'Issue with Profile : {pr}')
ec2_client=session.client('ec2')
sg_data = ec2_client.describe_security_groups(
        GroupIds=[
            sg_id,
        ]
        )
vpc_id = sg_data['SecurityGroups'][0]['VpcId']
replace_sg_id = ec2_client.create_security_group(
    Description='Replacement for Default SG', #hard coded, will add arguments in parser if needed.
    GroupName='default_sg_replacement',
    VpcId=vpc_id,
)['GroupId']
default_ingress_1 = sg_data['SecurityGroups'][0]['IpPermissions']
default_egress_1 =  sg_data['SecurityGroups'][0]['IpPermissionsEgress']
default_ingress=[]
if len(default_ingress_1[0]['UserIdGroupPairs']) > 0 :
    for sgs in default_ingress_1[0]['UserIdGroupPairs']:
        sgs['GroupId'] = replace_sg_id
default_ingress= default_ingress_1
ingress_rules = ec2_client.authorize_security_group_ingress(
        GroupId=replace_sg_id,
        IpPermissions=default_ingress)
for response in paginate(ec2_client.describe_network_interfaces, Filters=[
        {
            'Name': 'group-id',
            'Values': [
                sg_id,
            ]
        },
    ]):
    group_ids=[]
    for groupids in response['Groups']:
        if groupids['GroupId'] != sg_id:
            group_ids.append(groupids['GroupId'])
    group_ids.append(replace_sg_id)
    network_ifs.append({f"{response['NetworkInterfaceId']}":group_ids})
print(f"Updating NIFs with the replaced SG - {replace_sg_id} in place of {sg_id}",network_ifs)
for nif in network_ifs:
    response = ec2_client.modify_network_interface_attribute(
    Groups=nif[list(nif.keys())[0]],
    NetworkInterfaceId=list(nif.keys())[0],
    )
print(f"Inbound rules for {sg_id} are {sg_data['SecurityGroups'][0]['IpPermissions']}")
print(f"Outbound rules for {sg_id} are {sg_data['SecurityGroups'][0]['IpPermissionsEgress']}")
print(f"Deleting SG rules for {sg_id}")
ec2_client.revoke_security_group_ingress(GroupId=sg_id,IpPermissions= sg_data['SecurityGroups'][0]['IpPermissions'])
ec2_client.revoke_security_group_egress(GroupId=sg_id,IpPermissions= sg_data['SecurityGroups'][0]['IpPermissionsEgress'])