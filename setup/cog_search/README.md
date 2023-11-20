### Index upload script

The script needs an endpoint and a tenantID or Azure Cognitive Search account key as given arguments to connect to cognitive search. <br>
The directory "index_configuration" contains json files with configurations to create new indexes, all are created by running the script. The index names are set to the names of the json files ("gptkbindex-we" includes the embeddings field, "gptkbindex-woe" does not). If an index already exists, it is skipped.
