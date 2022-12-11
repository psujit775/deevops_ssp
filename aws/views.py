from django.http import HttpResponse
from django.http import JsonResponse
from .models import EC2Instances
import boto3
import botocore
from django.utils import timezone

def index(request):
    return HttpResponse("Hello, AWS. You're at the start point.")


def get_all_instances(request):
    all_ec2_instances = list(EC2Instances.objects.values())
    #output = ', '.join([q.instance_id for q in all_ec2_instances])
    return JsonResponse(all_ec2_instances,safe=False)

def refresh_instances(request):
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances()
    EC2Instances.truncate()
    http_response = "EC2 instance details reloaded successfully."
    print("Tryning to truncate table.")
    for r in response['Reservations']:
        for i in r['Instances']:
            instance_id = i.get('InstanceId', 'Null')
            created_date = i.get('LaunchTime', 'Null')
            instance_type = i.get('InstanceType', 'Null')
            key_name = i.get('KeyName', 'Null')
            internal_ip = i.get('PrivateIpAddress', 'Null')
            external_ip = i.get('PublicIpAddress', 'Null')
            instance_name = "Null"
            instance_tags = i.get('Tags', 'Null')
            updated_at = timezone.now()

            if instance_tags == "Null":
                print("No Tags found for instance: {}".format(instance_id))
            else:
                for tags in i['Tags']:
                    if tags['Key'] == 'Name':
                        instance_name = tags['Value']

            instance_state = i['State']['Name']
            try:
                save_res = EC2Instances(instance_id=instance_id,created_date=created_date,
                                        instance_type=instance_type,key_name=key_name,
                                        internal_ip=internal_ip,external_ip=external_ip,
                                        instance_name=instance_name,instance_tags=instance_tags,
                                        instance_state=instance_state,
                                        updated_at=updated_at).save()

            except Exception as e:
                print("Error while save response to database: {}".format(e))
                http_response = "EC2 instance details reload failed."
    return HttpResponse(http_response)

def create_ec2_instance(request,*args, **kwargs):
    user_args = {
        'instance_name' : request.GET.get('instance_name'),
        'ami_image_id' : request.GET.get('ami_image_id'),
        'instance_type' : request.GET.get('instance_type'),
        'disk_size_gb' : int(request.GET.get('disk_size_gb')),
        'device_name' : request.GET.get('device_name'),
        'subnet_id' : request.GET.get('subnet_id'),
        'security_groups_ids' : request.GET.get('security_groups_ids'),
        'public_ip' : request.GET.get('public_ip'),
        'key_name' : request.GET.get('key_name'),
        'availability_zone' : request.GET.get('availability_zone'),
        'terminate_date' : request.GET.get('terminate_date')
    }
    dry_run = False
    httpRes = {}
    userdata_script = '''
    # Install awscli
    sudo apt update
    '''
    ec2_client = boto3.client('ec2')
    BlockDeviceMappings = [
        {
            'DeviceName': user_args['device_name'],
            'Ebs': {
                'DeleteOnTermination': True,
                'VolumeSize': user_args['disk_size_gb'],
                'VolumeType': 'gp2'
            }
        },
    ]

    placement = {
        'AvailabilityZone': user_args['availability_zone']
    }

    TagSpecifications = [
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': user_args['instance_name']
                },
                {
                    'Key': 'Django-Managed',
                    'Value': "True"
                },
                {
                    'Key': 'Terminate-on',
                    'Value': user_args['terminate_date']
                }
            ]
        },
        {
            'ResourceType': 'volume',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': user_args['instance_name'] + "-vol"
                },
                {
                    'Key': 'Django-Managed',
                    'Value': "True"
                },
                {
                    'Key': 'Terminate-on',
                    'Value': user_args['terminate_date']
                }
            ]
        }
    ]

    try:
        # Create Elastic/Public IP for instance
        if user_args['public_ip'] == True:
            networkInterfaces = [
                {
                    'DeviceIndex': 0,
                    'SubnetId': user_args['subnet_id'],
                    'Groups': [user_args['security_groups_ids']],
                    'AssociatePublicIpAddress': True,
                    'DeleteOnTermination': True
                }, ]
            response = ec2_client.run_instances(ImageId=user_args['ami_image_id'],
                                                InstanceType=user_args['instance_type'],
                                                NetworkInterfaces=networkInterfaces,
                                                UserData=userdata_script,
                                                MinCount=1, MaxCount=1,
                                                BlockDeviceMappings=BlockDeviceMappings,
                                                TagSpecifications=TagSpecifications,
                                                KeyName=user_args['key_name'],
                                                Placement=placement,
                                                DryRun=dry_run)
        else:
            response = ec2_client.run_instances(ImageId=user_args['ami_image_id'],
                                                InstanceType=user_args['instance_type'],
                                                SubnetId=user_args['subnet_id'],
                                                SecurityGroupIds=[user_args['security_groups_ids']],
                                                UserData=userdata_script,
                                                MinCount=1, MaxCount=1,
                                                BlockDeviceMappings=BlockDeviceMappings,
                                                TagSpecifications=TagSpecifications,
                                                KeyName=user_args['key_name'],
                                                Placement=placement,
                                                DryRun=dry_run)

        instance_id = response['Instances'][0]['InstanceId']
        status = response['ResponseMetadata']['HTTPStatusCode']
        ec2_client.get_waiter('instance_running').wait(
                InstanceIds=[instance_id]
        )
        print('Success! instance:', instance_id, 'is created and running')
        httpRes['instance_id'] = instance_id
        httpRes['status'] = status
        httpRes['response'] = "Success"

    except botocore.exceptions.ParamValidationError as error:
        print('Error! Failed to create instance!')
        print(error)
        httpRes['status'] = "500"
        httpRes['response'] = "Failed to create instance"
        httpRes['Exception'] = str(error)

    except botocore.exceptions.ClientError as error:
        print('Error! Failed to create instance!')
        print(error)
        httpRes['status'] = "500"
        httpRes['response'] = "Failed to create instance"
        httpRes['Exception'] = str(error)

    return JsonResponse(httpRes)

def terminate_ec2_instance(request,*args, **kwargs):
    user_args = {
        'instance_ids': request.GET.get('instance_ids')
    }

    instance_id_list = list(user_args['instance_ids'].split(","))

    httpRes = {}
    try:
        ec2_client = boto3.client('ec2')
        response = ec2_client.terminate_instances(InstanceIds=
                                           instance_id_list,
                                           DryRun=False)

        ec2_client.get_waiter('instance_terminated').wait(
            InstanceIds=instance_id_list
        )
        print('Success! instance:', user_args['instance_ids'], 'is Terminated.')
        status = response['ResponseMetadata']['HTTPStatusCode']
        httpRes['status'] = status
        httpRes['instance_ids'] = user_args['instance_ids']
        httpRes['response'] = "Success"
        print(response['TerminatingInstances'])

    except botocore.exceptions.ParamValidationError as error:
        print('Error! Failed to Terminate instance!')
        print(error)
        httpRes['status'] = "500"
        httpRes['instance_ids'] = user_args['instance_ids']
        httpRes['response'] = "Failed to Terminate instance"
        httpRes['Exception'] = str(error)

    except botocore.exceptions.ClientError as error:
        print('Error! Failed to Terminate instance!')
        print(error)
        httpRes['status'] = "500"
        httpRes['instance_ids'] = user_args['instance_ids']
        httpRes['response'] = "Failed to Terminate instance"
        httpRes['Exception'] = str(error)

    return JsonResponse(httpRes)

def stop_ec2_instance(request,*args, **kwargs):
    user_args = {
        'instance_ids': request.GET.get('instance_ids')
    }

    instance_id_list = list(user_args['instance_ids'].split(","))

    httpRes = {}
    try:
        ec2_client = boto3.client('ec2')
        response = ec2_client.stop_instances(InstanceIds=
                                           instance_id_list,
                                           DryRun=False)

        # ec2_client.get_waiter('instance_stopped').wait(
        #     InstanceIds=instance_id_list
        # )
        print('Success! instance:', user_args['instance_ids'], 'is Stopped.')
        status = response['ResponseMetadata']['HTTPStatusCode']
        httpRes['status'] = status
        httpRes['instance_ids'] = user_args['instance_ids']
        httpRes['response'] = "Success"
        print(response['StoppingInstances'])

    except botocore.exceptions.ParamValidationError as error:
        print('Error! Failed to Stop instance!')
        print(error)
        httpRes['status'] = "500"
        httpRes['instance_ids'] = user_args['instance_ids']
        httpRes['response'] = "Failed to Stop instance"
        httpRes['Exception'] = str(error)

    except botocore.exceptions.ClientError as error:
        print('Error! Failed to Stop instance!')
        print(error)
        httpRes['status'] = "500"
        httpRes['instance_ids'] = user_args['instance_ids']
        httpRes['response'] = "Failed to Stop instance"
        httpRes['Exception'] = str(error)

    return JsonResponse(httpRes)


