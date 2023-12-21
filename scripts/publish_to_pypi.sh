#!/bin/bash
# Script to automate publishing to pypi
# Dave T 2023-12-21
pypi_config_file=~/.pypirc

pip install twine

if [ ! -f dist/*.tar.gz ]; then
    echo "No releases found. Please run python3 -m setup.py sdist"
    exit
fi
twine check dist/*

echo "Ready to publish."
echo "Default is publishing to testpypi."
read -r -p "If you are fully ready, please publish to pypi by typing 'thisisnotatest'<enter>: " response
echo "response=$response"
if [ "$response" = "thisisnotatest" ]; then
    repository=pypi
else
    repository=testpypi
fi

if [ -f $pypi_config_file ]; then
    echo "Using $pypi_config_file for API keys"
else 
    echo "$pypi_config_file not found, please paste pypi API token below:"
    read twine_api_key
    export TWINE_USERNAME=__token__
    export TWINE_PASSWORD=$twine_api_key
fi
echo "Publishing to $repository..."
twine upload --repository $repository dist/*
echo "Publishing complete!"
echo
echo "Don't forget to tag this release!"