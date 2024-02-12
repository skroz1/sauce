#!/bin/bash

# Define names for the policy, role, and user
POLICY_NAME="BillingReadOnlyPolicy"
ROLE_NAME="BillingReadOnlyRole"
USER_NAME="billing_ro"

# Define your AWS Account ID
AWS_ACCOUNT_ID="" # Replace with your actual AWS account ID

# Define the trust relationship JSON for the role (if applicable)
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

# Define the policy JSON
POLICY='{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetCostForecast",
                "ce:GetReservationUtilization",
                "ce:GetTags",
                "ce:GetUsageForecast",
                "ce:ListCostCategoryDefinitions"
            ],
            "Resource": "*"
        }
    ]
}'

# Create IAM policy
aws iam create-policy --policy-name $POLICY_NAME --policy-document "$POLICY"

# Create IAM role and attach the policy
aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document "$TRUST_POLICY"
aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn "arn:aws:iam::$AWS_ACCOUNT_ID:policy/$POLICY_NAME"

# Create IAM user
aws iam create-user --user-name $USER_NAME

# Attach policy to the user
aws iam attach-user-policy --user-name $USER_NAME --policy-arn "arn:aws:iam::$AWS_ACCOUNT_ID:policy/$POLICY_NAME"

# Create access key for the user
aws iam create-access-key --user-name $USER_NAME
