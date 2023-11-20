#!/bin/bash

echo ""
echo "Start installing extensions..."
echo ""

extensions=(
    "bradlc.vscode-tailwindcss"
    "esbenp.prettier-vscode"
    "mohsen1.prettify-json"
    "ms-azuretools.azure-dev"
    "ms-azuretools.vscode-bicep"
    "ms-dotnettools.vscode-dotnet-runtime"
    "ms-python.black-formatter"
    "ms-python.python"
    "ms-python.vscode-pylance"
    "ms-toolsai.jupyter"
    "ms-toolsai.jupyter-keymap"
    "ms-toolsai.jupyter-renderers"
    "ms-toolsai.vscode-jupyter-cell-tags"
    "ms-toolsai.vscode-jupyter-slideshow"
    "ms-vscode-remote.remote-containers"
    "ms-vscode.azurecli"
    "oouo-diogo-perdigao.docthis"
    "wayou.vscode-todo-highlight"
    "njpwerner.autodocstring"
)

for extension in "${extensions[@]}"; do
  code --install-extension "$extension"
done
