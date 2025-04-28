import boto3
import time
import logging

logger = logging.getLogger("TranscriptionServer")

cloudwatch_client = boto3.client('cloudwatch', region_name="us-east-1")  # Adjust AWS_REGION

def log_metric_to_cloudwatch(metric_name, value, unit="Seconds"):
    try:
        cloudwatch_client.put_metric_data(
            Namespace="OnDemandTranscription",
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Timestamp': time.time(),
                    'Value': value,
                    'Unit': unit
                },
            ]
        )
        logger.info(f"CloudWatch Metric Pushed: {metric_name} = {value:.4f} {unit}")
    except Exception as e:
        logger.error(f"Failed to push metric {metric_name}: {e}")
