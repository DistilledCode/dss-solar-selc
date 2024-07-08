
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

### `ECScraper`

The `ECScraper` class is designed to scrape articles from the Economic Times website. Here is an example of how to use the `ECScraper` class to fetch articles for different topics:

```python
from scrap import ECScraper

# Create a Scraper object
scrap = ECScraper()

# Fetch articles for different topics
scrap.fetch_ec("hybrid")
scrap.fetch_ec("renewable-regulation")
scrap.fetch_ec("solar")
```
