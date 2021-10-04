"""
Steps to use the Script:
1. Pass list of IAM users in a text file which are line by line
2. export AWS_PROFILE=profile_name (The profile/account where you are running the script)
3. Run the script. Eg. python3 iam_user_delete.py --inputfile test.txt
"""
import boto3
import argparse
from botocore.exceptions import ClientError

def iam_delete(user,iam_client):
    try:
        resp=iam_client.list_attached_user_policies(
            UserName = user
        )
        if len(resp['AttachedPolicies'])>0:
            for user_policy in resp['AttachedPolicies']:
                try:
                    iam_client.detach_user_policy(
                        UserName = user,
                        PolicyArn=user_policy['PolicyArn']
                    )
                except ClientError as e:
                    raise Exception(f"Error while detaching policy for {user} and error is {e.response}")

    except ClientError as e:
        raise Exception(f"Error while listing user policies attached for {user} and error is {e.response}")
    try:
        iam_client.delete_login_profile(
            UserName = user
        )
    except ClientError as e:
        raise Exception(f"Error while deleting Login profile for {user} and error is {e.response}")
    try:
        iam_client.delete_user(
            UserName = user
        )
    except ClientError as e:
        raise Exception(f"Error while deleting user {user} and error is {e.response}")

def do_iam_delete(inputfile,profile):
    session = boto3.Session(profile_name=profile)
    iam_client = session.client('iam')
    with open(inputfile) as f:
        lines = f.read().splitlines() 
    print("These are list of IAM users which will be deleted, Are you sure want to delete?[y/n]") 
    for line in lines:
        print(line)
    user_input=input()
    if user_input=='y':        
        for line in lines:
            print(f"Trying to delete IAM user {line}")
            try:
                response = iam_client.get_user(UserName=line)
            except ClientError as e:
                raise Exception(f"Error while getting user {line} ,user not found and error is {e.response}")
            try:
                response=iam_client.list_groups_for_user(
                    UserName = line
                )
                if len(response['Groups'])>0:
                    for group in response['Groups']:
                        try:
                            response=iam_client.remove_user_from_group(
                                    GroupName=group['GroupName'],
                                    UserName=line
                                )
                        except ClientError as e:
                            raise Exception(f"Error while removing user {line} from group {group['GroupName']} and error is {e.response}")
                    iam_delete(line,iam_client)
                else:
                    iam_delete(line,iam_client)
            except ClientError as e:
                print(f"Error while listing groups for user {line}")
    else:
        print("Exiting script to not delete users")
        quit()
        

def main():
    parser = argparse.ArgumentParser(description='Read Inputs given to Delete IAM users',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--inputfile', required=True,
                        help='Pass a valid file which contains IAM users as list')
    parser.add_argument('--profile', required=True,
                        help='Pass a valid AWS profile name')
    args = parser.parse_args()
    assert args.inputfile is not None , "Input file should be given to delete users"
    do_iam_delete(args.inputfile,args.profile)
    print("Users Deletion Completed") 

if __name__ == '__main__':
    main()