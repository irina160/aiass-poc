```python
import os
import openai
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType

# Replace these with your own values, either in environment variables or directly here
AZURE_STORAGE_ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT") or "mystorageaccount"
AZURE_STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER") or "content"
AZURE_SEARCH_SERVICE = os.environ.get("AZURE_SEARCH_SERVICE") or "gptkb"
AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX") or "gptkbindex"
AZURE_OPENAI_SERVICE = os.environ.get("AZURE_OPENAI_SERVICE") or "myopenai"
AZURE_OPENAI_GPT_DEPLOYMENT = os.environ.get("AZURE_OPENAI_GPT_DEPLOYMENT") or "davinci"
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.environ.get("AZURE_OPENAI_CHATGPT_DEPLOYMENT") or "chat"
AZURE_OPENAI_CHATGPT_MODEL = os.environ.get("AZURE_OPENAI_CHATGPT_MODEL") or "gpt-35-turbo"
AZURE_OPENAI_EMB_DEPLOYMENT = os.environ.get("AZURE_OPENAI_EMB_DEPLOYMENT") or "embedding"

KB_FIELDS_CONTENT = os.environ.get("KB_FIELDS_CONTENT") or "content"
KB_FIELDS_CATEGORY = os.environ.get("KB_FIELDS_CATEGORY") or "category"
KB_FIELDS_SOURCEPAGE = os.environ.get("KB_FIELDS_SOURCEPAGE") or "sourcepage"

# Use the current user identity to authenticate with Azure OpenAI, Cognitive Search and Blob Storage (no secrets needed, 
# just use 'az login' locally, and managed identity when deployed on Azure). If you need to use keys, use separate AzureKeyCredential instances with the 
# keys for each service
azure_credential = DefaultAzureCredential(exclude_shared_token_cache_credential = True)

# Used by the OpenAI SDK
openai.api_base = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
openai.api_version = "2023-05-15"

# Comment these two lines out if using keys, set your API key in the OPENAI_API_KEY environment variable and set openai.api_type = "azure" instead
openai.api_type = "azure_ad"
openai.api_key = azure_credential.get_token("https://cognitiveservices.azure.com/.default").token

# Set up clients for Cognitive Search and Storage
search_client = SearchClient(
    endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
    index_name=AZURE_SEARCH_INDEX,
    credential=azure_credential)
```


```python
# Chat roles
SYSTEM = "system"
USER = "user"
ASSISTANT = "assistant"

system_message_chat_conversation = """Assistant helps the company employees with their healthcare plan questions, and questions about the employee handbook. Be brief in your answers.
Answer ONLY with the facts listed in the list of sources below. If there isn't enough information below, say you don't know. Do not generate answers that don't use the sources below. If asking a clarifying question to the user would help, ask the question.
Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response. Use square brackets to reference the source, e.g. [info1.txt]. Don't combine sources, list each source separately, e.g. [info1.txt][info2.pdf].
"""
chat_conversations = [{"role" : SYSTEM, "content" : system_message_chat_conversation}]

summary_prompt_template = """
Given the chat history and user question generate a search query that will return the best answer from the knowledge base.
Try and generate a grammatical sentence for the search query.
Do NOT use quotes and avoid other search operators.
Do not include cited source filenames and document names such as info.txt or doc.pdf in the search query terms.
Do not include any text inside [] or <<>> in the search query terms.
If the question is not in English, translate the question to English before generating the search query.

Search query:
"""
query_summary_conversations = [{"role" : SYSTEM, "content" : summary_prompt_template}]
```


```python
# Execute this cell multiple times updating user_input to accumulate chat history
user_input = "Does my plan cover annual eye exams?"
query_summary_conversations.append({"role": USER, "content": user_input })

# Exclude category, to simulate scenarios where there's a set of docs you can't see
exclude_category = None

query_completion = openai.ChatCompletion.create(
    deployment_id=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
    model=AZURE_OPENAI_CHATGPT_MODEL,
    messages=query_summary_conversations, 
    temperature=0.7, 
    max_tokens=1024, 
    n=1)
search = query_completion.choices[0].message.content

# Use Azure OpenAI to compute an embedding for the query
query_vector = openai.Embedding.create(engine=AZURE_OPENAI_EMB_DEPLOYMENT, input=search)["data"][0]["embedding"]

# Alternatively simply use the following if not using reranking with semantic search:
# search_client.search(search, 
#                      top=3, 
#                      vector=query_vector if query_vector else None, 
#                      top_k=50 if query_vector else None, 
#                      vector_fields="embedding" if query_vector else None)

print("Searching:", search)
print("-------------------")
filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None
r = search_client.search(search, 
                         filter=filter,
                         query_type=QueryType.SEMANTIC, 
                         query_language="en-us", 
                         query_speller="lexicon", 
                         semantic_configuration_name="default", 
                         top=3,
                         vector=query_vector if query_vector else None, 
                         top_k=50 if query_vector else None, 
                         vector_fields="embedding" if query_vector else None)
results = [doc[KB_FIELDS_SOURCEPAGE] + ": " + doc[KB_FIELDS_CONTENT].replace("\n", "").replace("\r", "") for doc in r]
content = "\n".join(results)

user_content = user_input + " \nSOURCES:\n" + content

chat_conversations.append({"role": USER, "content": user_content })

chat_completion = openai.ChatCompletion.create(
    deployment_id=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
    model=AZURE_OPENAI_CHATGPT_MODEL,
    messages=chat_conversations, 
    temperature=0.7, 
    max_tokens=1024, 
    n=1)
chat_content = chat_completion.choices[0].message.content
'''
reset user content to avoid sources in conversation history
add source as a single shot in query conversation
'''
chat_conversations[-1]["content"] = user_input
chat_conversations.append({"role":ASSISTANT, "content": chat_content})
query_summary_conversations.append({"role":ASSISTANT, "content": chat_content})

print("\n-------------------\n")
for conversation in chat_conversations:
    print(conversation)
```
