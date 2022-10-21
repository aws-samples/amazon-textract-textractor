#!/bin/bash

rm -f textractor.zip && \
rm -rf lambda_layer && \
mkdir -p lambda_layer/python && \
cd lambda_layer/python && \
pip3 install amazon-textract-textractor==1.0.14 --target=. && \
cd .. && \
zip -r ../textractor.zip python/
