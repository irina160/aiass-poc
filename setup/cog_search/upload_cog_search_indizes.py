import argparse
import json
import os
import logging
from azure.cosmos import exceptions
from azure.identity import AzureDeveloperCliCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex


def create_search_index(search_creds):
    index_client = SearchIndexClient(
        endpoint=f"https://{args.searchservice}.search.windows.net/",
        credential=search_creds,
    )

    # all directories in current folder hold index configuration files
    index_dirs = [
        dir
        for dir in os.listdir(os.path.dirname(__file__))
        if os.path.isdir(os.path.dirname(__file__) + "/" + dir)
    ]

    for i_dir in index_dirs:
        indexes = [
            json_file.split(".")[0]
            for json_file in os.listdir(os.path.dirname(__file__) + "/" + i_dir)
        ]
        for index in indexes:
            try:
                with open(
                    f"{os.path.dirname(__file__)}/{i_dir}/{index}.json",
                    encoding="utf-8",
                ) as fh:
                    data = json.load(fh)

                data["name"] = index
                index_json = SearchIndex.from_dict(data=data)

                index_client.create_index(index_json)
                logging.info(f"Created index: {index}")
            except exceptions.HttpResponseError as error:
                logging.info(error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tenantid",
        required=False,
        help="Optional. Use this to define the Azure directory where to authenticate)",
    )
    parser.add_argument(
        "--searchkey",
        required=False,
        help="Optional. Use this Azure Cognitive Search account key instead of the current user identity to login (use az login to set current user for Azure)",
    )
    parser.add_argument(
        "--searchservice",
        help="Name of the Azure Cognitive Search service where content should be indexed (must exist already)",
    )
    args = parser.parse_args()

    # Use the current user identity to connect to Azure services unless a key is explicitly set for any of them
    azd_credential = (
        AzureDeveloperCliCredential()
        if args.tenantid is None
        else AzureDeveloperCliCredential(tenant_id=args.tenantid, process_timeout=60)
    )
    default_creds = azd_credential if args.searchkey is None else None
    search_creds = (
        default_creds if args.searchkey is None else AzureKeyCredential(args.searchkey)
    )

    create_search_index(search_creds)
