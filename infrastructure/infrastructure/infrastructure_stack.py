"""TechNova Varejo | CI/CD do ambiente atual.

Os buckets, o Glue, o Redshift Serverless, o DataBrew e o QuickSight
ja existem e NAO sao recriados nem removidos por esta stack.
Esta stack gerencia apenas a automacao GitHub -> CodePipeline ->
CodeBuild (dbt + CDK) e a notificacao de falhas via SNS/EventBridge.
"""

import os

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as actions,
    aws_ec2 as ec2,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
)
from constructs import Construct


class InfrastructureStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Recursos que ja existem na conta; informados aqui como referencias.
        account = self.account
        region = self.region
        redshift_host = (
            f"technova-workgroup.{account}.{region}.redshift-serverless.amazonaws.com"
        )
        connection_arn = (
            f"arn:aws:codeconnections:{region}:{account}:"
            "connection/41877cb3-0609-4769-95d7-8b0dbc002a99"
        )

        # O segredo e criado uma vez no Secrets Manager (fora deste CDK),
        # com JSON {"username": "...", "password": "..."}.
        secret_name = "technova/redshift/dbt"
        secret = secretsmanager.Secret.from_secret_name_v2(
            self, "ExistingRedshiftDbtSecret", secret_name
        )

        # Log do build: mantido mesmo quando esta stack for apagada.
        build_logs = logs.LogGroup(
            self,
            "BuildLogs",
            log_group_name="/aws/codebuild/technova-dbt-cicd",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # CodeBuild pode usar a VPC do Redshift, quando configurada.
        # Configuracao opcional via TECHNOVA_CODEBUILD_VPC_ID e
        # TECHNOVA_CODEBUILD_SG_ID. A VPC precisa de subnets privadas
        # com saida para a internet/NAT para instalar dependencias.
        vpc_id = os.getenv("TECHNOVA_CODEBUILD_VPC_ID")
        sg_id = os.getenv("TECHNOVA_CODEBUILD_SG_ID")
        network_props = {}
        if vpc_id or sg_id:
            if not (vpc_id and sg_id):
                raise ValueError(
                    "Informe TECHNOVA_CODEBUILD_VPC_ID e "
                    "TECHNOVA_CODEBUILD_SG_ID juntos."
                )
            vpc = ec2.Vpc.from_lookup(self, "ExistingVpc", vpc_id=vpc_id)
            security_group = ec2.SecurityGroup.from_security_group_id(
                self, "ExistingCodeBuildSg", sg_id, mutable=False
            )
            network_props = {
                "vpc": vpc,
                "security_groups": [security_group],
                "subnet_selection": ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ),
            }

        build_project = codebuild.PipelineProject(
            self,
            "TechNovaDbtBuild",
            project_name="technova-dbt-cicd",
            description="dbt Redshift e CDK: validacao, testes e deploy",
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                environment_variables={
                    "REDSHIFT_HOST": codebuild.BuildEnvironmentVariable(
                        value=redshift_host
                    ),
                    "REDSHIFT_SECURITY_GROUP": codebuild.BuildEnvironmentVariable(
                        value="sg-023a1931ab3a5adae"
                    ),
                    "REDSHIFT_USER": codebuild.BuildEnvironmentVariable(
                        value=f"{secret_name}:username",
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER,
                    ),
                    "REDSHIFT_PASSWORD": codebuild.BuildEnvironmentVariable(
                        value=f"{secret_name}:password",
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER,
                    ),
                },
            ),
            timeout=Duration.minutes(30),
            logging=codebuild.LoggingOptions(
                cloud_watch=codebuild.CloudWatchLoggingOptions(
                    log_group=build_logs
                )
            ),
            **network_props,
        )
        secret.grant_read(build_project)

        # Permitir abertura e fechamento temporario da porta do Redshift.
        build_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:AuthorizeSecurityGroupIngress",
                    "ec2:RevokeSecurityGroupIngress",
                ],
                resources=[
                    f"arn:aws:ec2:{region}:{account}:security-group/sg-023a1931ab3a5adae"
                ],
            )
        )

        # O deploy automatico do CDK usa APENAS os papeis criados
        # pelo 'cdk bootstrap' na conta e regiao corretas.
        qualifier = "hnb659fds"  # qualifier padrao do bootstrap CDK
        role_names = (
            "deploy-role", "file-publishing-role", "image-publishing-role", "lookup-role"
        )
        deploy_roles = [
            f"arn:aws:iam::{account}:role/cdk-{qualifier}-{name}-{account}-{region}"
            for name in role_names
        ]
        build_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"], resources=deploy_roles
            )
        )
        build_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudformation:DescribeStacks",
                    "cloudformation:DescribeStackEvents",
                    "cloudformation:ListStacks",
                    "cloudformation:GetTemplate",
                    "ssm:GetParameter",
                ],
                resources=["*"],
            )
        )

        source = codepipeline.Artifact("SourceArtifact")
        source_action = actions.CodeStarConnectionsSourceAction(
            action_name="GitHubMain",
            owner="Fobious",
            repo="technova-enterprise-dataops",
            branch="main",
            connection_arn=connection_arn,
            output=source,
            trigger_on_push=True,
        )

        pipeline = codepipeline.Pipeline(
            self,
            "TechNovaPipeline",
            pipeline_name="technova-dataops-cicd",
            pipeline_type=codepipeline.PipelineType.V2,
            restart_execution_on_update=False,
            cross_account_keys=False,
        )
        pipeline.add_stage(stage_name="Source", actions=[source_action])
        pipeline.add_stage(
            stage_name="BuildAndDeploy",
            actions=[actions.CodeBuildAction(
                action_name="DbtBuildAndCdkDeploy",
                project=build_project,
                input=source,
            )],
        )

        # Monitorar falhas da NOVA pipeline; nao recria Step Functions antigas.
        alert_topic = sns.Topic(
            self,
            "PipelineFailureTopic",
            topic_name="technova-cicd-failure-alerts",
        )
        alert_email = self.node.try_get_context("alert_email")
        if alert_email:
            alert_topic.add_subscription(
                subscriptions.EmailSubscription(str(alert_email))
            )
        pipeline.on_state_change(
            "PipelineFailed",
            event_pattern=events.EventPattern(detail={"state": ["FAILED"]}),
            target=targets.SnsTopic(alert_topic),
        )

        CfnOutput(self, "PipelineName", value=pipeline.pipeline_name)
        CfnOutput(self, "BuildProject", value=build_project.project_name)
        CfnOutput(self, "AlertsTopicArn", value=alert_topic.topic_arn)
        CfnOutput(self, "ExistingGlueJob", value="TechNova_Raw_To_Bronze_Silver")
        CfnOutput(self, "ExistingRedshiftWorkgroup", value="technova-workgroup")
        CfnOutput(self, "ExistingRedshiftDatabase", value="dev")
