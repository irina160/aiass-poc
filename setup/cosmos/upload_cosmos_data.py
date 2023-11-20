import argparse
import json
import os
import logging
from azure.cosmos import CosmosClient, exceptions, PartitionKey


def setup_cosmosdb(args):
    """
    Script to upload data to CosmosDB from JSON files.
    The directories in the "data" folder are considered to be the database names and contain json files.
    The names of the json files are considered to be the container names and contain items which are to be uploaded to the containers.
    If a database/container/item already exists it is replaced by the new data.

    Args:
        args (_type_): --cosmosservice: Name of the CosmosDB service (must exist already), only the name, not the whole url of the endpoint
                       --apikey: API Key of the Azure directory where to authenticate, to be found at https://portal.azure.com/
    """
    cosmos_client = CosmosClient(
        url=f"https://{args.cosmosservice}.documents.azure.com/",
        credential=args.apikey,
    )

    # all directories in current folder are databases
    # TODO: Read only the correct folders (currently it also reads Azure RBAC, which fails because the files in there are different and not made for this usage)
    database_dirs = [
        dir
        for dir in os.listdir(os.path.dirname(__file__) + "/Data")
        if os.path.isdir(os.path.dirname(__file__) + "/Data/" + dir)
    ]

    for d_dir in database_dirs:
        try:
            current_db = cosmos_client.create_database(id=d_dir)
        except exceptions.CosmosResourceExistsError:
            logging.info(f"Database {d_dir} exists, is deleted and created newly.")
            cosmos_client.delete_database(database=d_dir)
            current_db = cosmos_client.create_database(id=d_dir)
            # current_db = cosmos_client.get_database_client(database=d_dir)
        logging.info(f"Start filling database: {d_dir}")
        # all json file names in current database directory are containers of current database
        containers = [
            json_file.split(".")[0]
            for json_file in os.listdir(os.path.dirname(__file__) + "/Data/" + d_dir)
        ]
        for container in containers:
            try:
                current_container = current_db.create_container(
                    id=container, partition_key=PartitionKey(path="/id")
                )
            except exceptions.CosmosResourceExistsError:
                logging.info(
                    f"Container {container} exists, is deleted and created newly."
                )
                current_db.delete_container(container)
                current_container = current_db.create_container(
                    id=container, partition_key=PartitionKey(path="/id")
                )
            logging.info(f"Start filling container: {container}")
            # json files include list of items to upload in the current container
            with open(
                f"{os.path.dirname(__file__)}/Data/{d_dir}/{container}.json",
                encoding="utf-8",
            ) as fh:
                data = json.load(fh)
            for data_item in data:
                try:
                    current_container.create_item(data_item)
                except exceptions.CosmosResourceExistsError:
                    logging.info(
                        f"item {data_item['id']} already exists in container {container} in database {d_dir}"
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cosmosservice",
        required=True,
        help="Name of the CosmosDB service (must exist already)",
    )
    parser.add_argument(
        "--apikey",
        required=True,
        help="Use this to define the Azure directory where to authenticate",
    )

    args = parser.parse_args()

    setup_cosmosdb(args)
