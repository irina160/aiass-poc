# Azure Search OpenAI Demo

This codebase is designed to integrate Azure Search with OpenAI's GPT model, providing a powerful tool for document analysis and search functionality. It leverages the capabilities of Azure's AI Form Recognizer, Blob Storage, and Search services, along with OpenAI's GPT model, to analyze and search through documents.

## Main Functionalities

1. **Document Analysis**: Utilizes Azure's AI Form Recognizer for document analysis.
2. **Search Functionality**: Leverages Azure Search for powerful document search capabilities.
3. **AI Integration**: Integrates OpenAI's GPT model for advanced AI capabilities.
4. **Blob Storage**: Uses Azure's Blob Storage for storing and retrieving documents.

## Installation

This codebase does not require a specific installation process as it is a collection of Python scripts and Azure configurations. However, you will need to have Python installed on your machine and the necessary dependencies.

## Dependencies

This codebase requires the following Python libraries:

- argparse
- base64
- glob
- html
- io
- os
- re
- time
- openai
- azure.ai.formrecognizer
- azure.core.credentials
- azure.identity
- azure.search.documents
- azure.search.documents.indexes
- azure.storage.blob
- pypdf
- tenacity

You can install these dependencies using pip:

```bash
pip install argparse base64 glob html io os re time openai azure.ai.formrecognizer azure.core.credentials azure.identity azure.search.documents azure.search.documents.indexes azure.storage.blob pypdf tenacity
```

## Usage

The main script in this codebase is the `openai.py` script. This script sets up the OpenAI GPT model with Azure's AI services. It also includes configurations for Azure's Blob Storage and Search services.

Here is an example of how to use this script:

```python
python openai.py --model_name "GPT-3" --model_version "3.0"
```

In this example, the `--model_name` argument specifies the name of the OpenAI model to use, and the `--model_version` argument specifies the version of the model.

## Authors and Maintainers

This codebase is maintained by the Azure and OpenAI teams. For any queries or issues, please contact the respective teams.

## Contributing

We welcome contributions from the community. Here's how you can contribute:

- **Reporting a Bug**: If you find a bug, please create an issue on the GitHub repository detailing the bug and how it can be reproduced.
- **Code of Conduct**: We have a [Code of Conduct](..\azure-search-openai-demo\.github\CODE_OF_CONDUCT.md) that all contributors must adhere to.
- **Making a Pull Request (PR)**: If you have a fix for a bug or a new feature you'd like to add, please create a pull request. Make sure to describe the changes in detail and ensure that your code is in line with our coding standards.
- **Support**: If you need support with using this codebase, please create an issue on the GitHub repository detailing your problem.
- **Donations**: If you'd like to make a donation, please email the maintainer of the repository.
- **Commercial Support**: For commercial support, please contact the Azure or OpenAI teams directly.

## License

This codebase is licensed under the MIT License. Please see the LICENSE file in the repository for more details.