
# SELC-Lab

## Overview

This repository contains code contributing to the work done in the SELC Lab under the guidance of [Prof. Arpit Rana](https://daiict.ac.in/faculty/arpit-rana).

## Installation

This project requires Python 3.10 or higher. You can install the required dependencies using `pip`:

Clone the repository

```bash
git clone https://github.com/DistilledCode/dss-solar-selc
cd dss-solar-selc
```

Install the requiremtents and setup the pre-commit config
```bash
pip install -r requirements.txt
pre-commit install
```

## Usage

### `ECScrapper`

The `ECScrapper` class is designed to scrape articles from the Economic Times website. Here is an example of how to use the `ECScrapper` class to fetch articles for different topics:

```python
from scrapper import ECScrapper

# Create a Scrapper object
scrapper = ECScrapper()

# Fetch articles for different topics
scrapper.fetch_ec("hybrid")
scrapper.fetch_ec("renewable-regulation")
scrapper.fetch_ec("solar")
```
