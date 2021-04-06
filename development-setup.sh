python -m pip uninstall -y amazon-textract-helper
python -m pip uninstall -y amazon-textract-caller
python -m pip uninstall -y amazon-textract-prettyprinter
python -m pip uninstall -y amazon-textract-overlayer
cd caller/
python -m pip install -e .
cd ../prettyprinter/
python -m pip install -e .
cd ../overlayer/
python -m pip install -e .
cd ../helper/
python -m pip install -e .
