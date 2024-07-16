
# Decision Support System for Solar Solution (SELC Lab, DA-IICT)

## Installation

This project requires Python 3.10 or higher. You can install the required dependencies using `pip`:

Clone the repository

```bash
git clone https://github.com/DistilledCode/dss-solar-selc
cd dss-solar-selc
```

Install gif-lfs

```bash
sudo apt-get install git-lfs
git lfs install
```

Configure git-lfs
```bash
git lfs track "*.json"
git lfs track "*.parquet"
```

Install the requiremtents and setup the pre-commit config
```bash
pip install -r requirements.txt
pre-commit install
```