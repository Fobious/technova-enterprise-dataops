import boto3

DATABASE_NAME = "technova_enterprise_catalog"
TABLE_NAME = "vendas_curadas"

PII_COLUMNS = [
    "customer_name",
    "customer_email",
    "cpf"
]

TAG_KEY = "classificacao"
TAG_VALUE = "PII"

lakeformation = boto3.client("lakeformation", region_name="us-east-1")
sts = boto3.client("sts")

account_id = sts.get_caller_identity()["Account"]


def create_lf_tag():
    try:
        lakeformation.create_lf_tag(
            CatalogId=account_id,
            TagKey=TAG_KEY,
            TagValues=[TAG_VALUE]
        )
        print(f"LF-Tag criada: {TAG_KEY}={TAG_VALUE}")

    except Exception as e:
        mensagem = str(e)

        if "Tag key already exists" in mensagem or "AlreadyExists" in mensagem:
            print(f"LF-Tag ja existia: {TAG_KEY}={TAG_VALUE}")
        else:
            raise


def apply_tag_to_columns():
    for column in PII_COLUMNS:
        print(f"Aplicando LF-Tag na coluna: {column}")

        lakeformation.add_lf_tags_to_resource(
            CatalogId=account_id,
            Resource={
                "TableWithColumns": {
                    "CatalogId": account_id,
                    "DatabaseName": DATABASE_NAME,
                    "Name": TABLE_NAME,
                    "ColumnNames": [column]
                }
            },
            LFTags=[
                {
                    "CatalogId": account_id,
                    "TagKey": TAG_KEY,
                    "TagValues": [TAG_VALUE]
                }
            ]
        )

        print(f"Tag aplicada com sucesso em {column}: {TAG_KEY}={TAG_VALUE}")


if __name__ == "__main__":
    create_lf_tag()
    apply_tag_to_columns()
    print("Processo de tagging LGPD concluido.")