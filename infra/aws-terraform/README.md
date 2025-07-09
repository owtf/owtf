This script automates the process of modifying a Terraform configuration file, checking for unsafe modifications, and running Terraform commands. It also handles different operating systems (macOS and Linux) and allows the user to choose whether to run the script in a "safe mode" or "unsafe mode."

## Deployment Steps

1. **Clone the Repository**

    First, clone the repository containing the deployment script and Kubernetes manifests:
    ```bash
    git clone https://github.com/owtf/owtf.git

    cd owtf/infra/terraform
    ```

2. **Install Terraform and AWS CLI**

    Make sure to install [Terraform](https://developer.hashicorp.com/terraform/install) and [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

3. **Setting Up AWS Roles and Permissions**

      To ensure secure and efficient use of Terraform with AWS, you need to set up AWS IAM roles and permissions correctly. This section provides instructions for setting up roles with either Single Sign-On (SSO) or user-based role assumption.

      ### Using Single Sign-On (SSO)

   AWS Single Sign-On (SSO) allows you to manage access to your AWS resources using your organization's SSO provider. Here's how to set it up:

   1. **Configure AWS SSO:**
      - Sign in to the [AWS SSO Console](https://console.aws.amazon.com/singlesignon/).
      - Follow the [AWS documentation](https://docs.aws.amazon.com/singlesignon/latest/userguide/getting-started.html) to set up SSO with your identity provider.

   2. **Create IAM Roles for SSO:**
      - Go to the [IAM Console](https://console.aws.amazon.com/iam/home).
      - Create a new role and select **AWS SSO** as the trusted entity.
      - Assign permissions that are necessary for Terraform operations `AmazonEC2FullAccess`, `AmazonVPCFullAccess`, `ElasticLoadBalancingFullAccess`, and `IAMFullAccess`.

   3. **Assign Roles to Users:**
      - Go back to the AWS SSO Console.
      - Assign the newly created IAM roles to users or groups within your SSO setup.

   4. **Configure Terraform to Use SSO:**
      - Update your Terraform provider configuration to use the `aws` profile that corresponds to your SSO setup in `provider.tf`:
      ```hcl
      provider "aws" {
         profile = "your-sso-profile"
         region  = "us-west-2"
      }
      ```

   5. **Authenticate Using SSO:**
      - Use the AWS CLI to authenticate with SSO before running Terraform commands:
      ```bash
      aws sso login --profile your-sso-profile
      ```

   ### Using IAM User Role Assumption

   For environments where SSO is not used, you can set up IAM users with minimal permissions and grant them the ability to assume a more powerful role.

   1. **Create a Role with Necessary Permissions:**
      - Go to the [IAM Console](https://console.aws.amazon.com/iam/home).
      - Assign permissions that are necessary for Terraform operations `AmazonEC2FullAccess`, `AmazonVPCFullAccess`, `ElasticLoadBalancingFullAccess`, and `IAMFullAccess`.

   2. **Create a Trust Policy for the Role:**
      - Add a trust policy to allow specific IAM users or roles to assume this role. Example trust policy:
      ```json
      {
         "Version": "2012-10-17",
         "Statement": [
            {
            "Effect": "Allow",
            "Principal": {
               "AWS": [
                  "arn:aws:iam::<aws_account_id>:user/terraform-user"
               ]
            },
            "Action": "sts:AssumeRole"
            }
         ]
      }
      ```

   3. **Create IAM Users with Limited Permissions:**
      - Create IAM users who will use Terraform.
      - Grant these users only the permission to assume the previously created role. Example policy for the user:
      ```json
      {
         "Version": "2012-10-17",
         "Statement": [
            {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:iam::<aws_account_id>:role/terraform-role"
            }
         ]
      }
      ```

   4. **Configure AWS CLI for Role Assumption:**
      - Update the AWS CLI configuration to use the assumed role:
      ```bash
      aws configure set role_arn arn:aws:iam::123456789012:role/terraform-role --profile terraform-user
      aws configure set source_profile default --profile terraform-user
      ```

   5. **Configure Terraform to Use the IAM User Profile:**
      - Update your Terraform provider configuration in `provider.tf`:
      ```hcl
      provider "aws" {
         profile = "terraform-user"
         region  = "us-west-2"
      }
      ```

   6. **Run Terraform Commands:**
      - When you run Terraform commands, the AWS CLI will assume the specified role and use the permissions defined for that role.

   ### Additional Resources

   - [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
   - [Terraform AWS Provider Security Best Practices](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/security.html)
   - [Assuming IAM Roles with Terraform](https://developer.hashicorp.com/terraform/tutorials/aws/aws-assumerole)

5. **Define Variables**

   ```bash
   variables.tf
   ```
   This file holds the variables of the Terraform configuration that can be modified as required by the user.

6. **Run the Script**

    ```bash
    bash apply-script.sh
    ```

    Run this command to initiate, format, validate, and plan Terraform scripts.

7. **Apply Infrastructure**

    ```
    terraform apply
    ```
    Run this command to apply the Terraform scripts to create infrastructure on your AWS account.

8. **Logs Location**    
    You can connect to the machine using **Session Manager** to check the logs at this location using this command:

    ```
    tail -f /var/log/setup.log
    ```
    
    **Please wait for the logs to show that OWTF has started**

    > Note: If you have not configured SMTP for your OWTF application, use the logs of the OWTF Docker container to get the verification link during login. Make sure to replace the appropriate IP address in that link with the **ALB DNS Name**. 
    
    Use this command to get the logs of the Docker container inside the EC2 instance:

    ```
    docker logs <Container_ID/Container_Name>
    ```

9. **Destroy Infrastructure**

    ```
    terraform destroy
    ```
    Run this command if you want to destroy the created infrastructure on your AWS account.

### Creating and Adding SSL Certificates to an Application Load Balancer (ALB)

> Note: If you want to use HTTPS for your application, follow the steps below. Otherwise, these steps can be skipped.

### Creating an SSL Certificate

#### Using AWS Certificate Manager (ACM)

1. **Sign in to AWS Management Console**: Open the [AWS Certificate Manager Console](https://console.aws.amazon.com/acm/home).

2. **Request a Public Certificate**:
   - Click on **Request a certificate**.
   - Choose **Request a public certificate** and click **Next**.

3. **Add Domain Names**:
   - Enter the domain name(s) for the certificate. Wildcards like `*.example.com` are supported.
   - Click **Next**.

4. **Choose Validation Method**:
   - **DNS Validation**: Add the CNAME record provided to your DNS settings for your Domain Provider.
   - Select the validation method and click **Next**.

5. **Review and Confirm**:
   - Confirm the details and click **Confirm and request**.

6. **Complete Domain Validation**:
   - Follow the necessary steps to validate your domain.
   - Once validated, the certificate status will change to **Issued**.

### Adding SSL Certificates to an Application Load Balancer (ALB)

1. **Sign in to AWS Management Console**: Open the [EC2 Dashboard](https://console.aws.amazon.com/ec2/v2/home).

2. **Navigate to Load Balancers**:
   - In the EC2 Dashboard, click on **Load Balancers** under **Load Balancing**.

3. **Select Your Load Balancer**:
   - Choose the ALB to which you want to add the SSL certificate.

4. **Configure Listener for Port 80 (HTTP)**:
   - Click on the **Listeners** tab.
   - Click **View/edit rules** for the HTTP listener on port 80.
   - **Add/Edit Rule**:
     - Ensure there is a rule that forwards traffic to the target group on port `8009`.
   - Click **Save**.

5. **Configure Listener for Port 443 (HTTPS)**:
   - Click on the **Listeners** tab.
   - Click **View/edit rules** for the HTTPS listener on port 443.
   - **Add or Edit HTTPS Listener**:
     - Click **Add listener** if one does not already exist for port 443.
     - Set the **Protocol** to `HTTPS` and **Port** to `443`.
     - **Add ACM Certificate**:
       - Click on **Add certificate**.
       - Choose **ACM Certificate** from the options and select your certificate from the dropdown menu.
       - Click **Save**.
     - Configure a **Forward to** action:
       - Choose the **Target Group** that listens on port `8009`.
     - Set up a **Redirect** rule (optional):
       - Choose **Redirect to** and set the **Protocol** to `HTTP`, **Port** to `80`, and **Path** to `#{path}`.
       - This redirects HTTPS traffic to HTTP, then HTTP traffic will be forwarded to port 8009.
     - Click **Save**.

6. **Update Security Groups**:
   - Ensure your ALB's security group allows inbound traffic on ports 80 and 443.
   - Navigate to **Security Groups** in the EC2 Dashboard.
   - Check or update the inbound rules to allow HTTP (port 80) and HTTPS (port 443) traffic.

7. **Test the Configuration**:
   - Visit your domain using `http://` and `https://`.
   - Verify that HTTP traffic is forwarded correctly to port 8009 on the target group.
   - Verify that HTTPS traffic is either redirected to HTTP and then forwarded to port 8009 or directly forwarded if redirection is not applied.
