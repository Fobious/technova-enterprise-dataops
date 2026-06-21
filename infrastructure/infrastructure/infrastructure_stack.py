from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    aws_glue as glue,
)
from constructs import Construct


class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        raw_bucket = s3.Bucket(
            self,
            "TechNovaRawBucket",
            bucket_name=f"technova-raw-zone-{self.account}-{self.region}",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        bronze_bucket = s3.Bucket(
            self,
            "TechNovaBronzeBucket",
            bucket_name=f"technova-bronze-zone-{self.account}-{self.region}",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        silver_bucket = s3.Bucket(
            self,
            "TechNovaSilverBucket",
            bucket_name=f"technova-silver-zone-{self.account}-{self.region}",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        scripts_bucket = s3.Bucket(
            self,
            "TechNovaScriptsBucket",
            bucket_name=f"technova-scripts-{self.account}-{self.region}",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        athena_results_bucket = s3.Bucket(
            self,
            "TechNovaAthenaResultsBucket",
            bucket_name=f"technova-athena-results-{self.account}-{self.region}",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        s3deploy.BucketDeployment(
            self,
            "DeployRawData",
            sources=[s3deploy.Source.asset("../data")],
            destination_bucket=raw_bucket,
        )

        s3deploy.BucketDeployment(
            self,
            "DeployGlueScripts",
            sources=[s3deploy.Source.asset("../glue")],
            destination_bucket=scripts_bucket,
            destination_key_prefix="glue",
        )

        glue_role = iam.Role(
            self,
            "TechNovaGlueRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            role_name="TechNovaGlueServiceRole",
        )

        glue_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
        )

        raw_bucket.grant_read(glue_role)
        bronze_bucket.grant_read_write(glue_role)
        silver_bucket.grant_read_write(glue_role)
        scripts_bucket.grant_read(glue_role)
        athena_results_bucket.grant_read_write(glue_role)

        glue_database = glue.CfnDatabase(
            self,
            "TechNovaGlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="technova_enterprise_catalog",
                description="Catálogo de dados da TechNova Varejo para o AT.",
            ),
        )

        glue_job = glue.CfnJob(
            self,
            "TechNovaRawToBronzeSilverJob",
            name="TechNova_ETL_RawToBronzeSilver_job",
            role=glue_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{scripts_bucket.bucket_name}/glue/raw_to_bronze_silver.py",
            ),
            glue_version="5.0",
            worker_type="G.1X",
            number_of_workers=2,
            timeout=10,
            default_arguments={
                "--job-language": "python",
                "--RAW_BUCKET": raw_bucket.bucket_name,
                "--BRONZE_BUCKET": bronze_bucket.bucket_name,
                "--SILVER_BUCKET": silver_bucket.bucket_name,
                "--enable-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
            },
        )

        crawler_role = iam.Role(
            self,
            "TechNovaCrawlerRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            role_name="TechNovaCrawlerServiceRole",
        )

        crawler_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
        )

        bronze_bucket.grant_read(crawler_role)
        silver_bucket.grant_read(crawler_role)

        glue.CfnCrawler(
            self,
            "TechNovaSilverCrawler",
            name="technova-crawler-silver",
            role=crawler_role.role_arn,
            database_name=glue_database.ref,
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue.CfnCrawler.S3TargetProperty(
                        path=f"s3://{silver_bucket.bucket_name}/vendas_curadas/"
                    )
                ]
            ),
            schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
                update_behavior="UPDATE_IN_DATABASE",
                delete_behavior="LOG",
            ),
        )
