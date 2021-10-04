#using this lambda ARN as target for default event bus in this account once created.
import boto3
import sys

def run_it(event, context):
    lambda_client = boto3.client('lambda')
    lambda_functions= event["lambda_functions"]
    for func in lambda_functions:
        try:
            response = lambda_client.invoke(FunctionName=func)
            print(response)
        except Exception as e:
                print('Unable to trigger lambda---- {func}'.format(func=func))
                continue
    print("Done") 
    
def lambda_handler(event, context):
    return run_it(event, context)