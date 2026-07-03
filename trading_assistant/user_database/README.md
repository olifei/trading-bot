# Trading Bot - User Database

This module is designed for generating and managing mock user data for the Trading Bot demo. It's completely decoupled from the main trading bot implementation, focusing solely on data generation and Firestore database operations.

## Overview

The User Database module provides tools to:

- Generate realistic mock data including user profiles, portfolios, market prices, and transactions
- Upload this data to a Firestore database
- Update market data periodically to simulate changing market conditions
- Clear data from the database when needed

## Setup

### Prerequisites

1. Python 3.8 or higher
2. Google Firebase account with Firestore enabled
3. Firebase service account key

### Installation

1. Install required dependencies:

```bash
pip install firebase-admin google-cloud-firestore
```

2. Configure Firebase:

   - Create a Firebase project in the [Firebase Console](https://console.firebase.google.com/)
   - Enable Firestore database
   - Generate a service account key (Project Settings → Service Accounts → Generate new private key)
   - Save the key JSON file in a secure location
   - Update the `config/firebase_config.json` file with your project details and service account key path

## Directory Structure

```
user_database/
│
├── config/                    # Configuration files
│   ├── firebase_config.json   # Firebase configuration
│   └── schema.json            # Firestore collections schema
│
├── data_templates/            # Template files for data generation
│
├── outputs/                   # Generated data files storage
│
├── scripts/                   # Utility scripts
│   ├── generate_data.py       # Generate mock data
│   ├── upload_data.py         # Upload data to Firestore
│   ├── update_market_data.py  # Update market prices
│   └── clear_data.py          # Clear Firestore data
│
├── main.py                    # Main entry point
└── README.md                  # This file
```

## Usage

All operations are performed through the `main.py` script.

### Initialize Environment

```bash
python main.py init
```

This creates the necessary directory structure and checks configuration files.

### Generate Mock Data

```bash
python main.py generate
```

Options:
- `--users <count>`: Number of users to generate (default: 20)
- `--transactions <count>`: Number of transactions per user (default: 5)

Generated data is saved in the `outputs/` directory as JSON files.

### Upload Data to Firestore

```bash
python main.py upload
```

Options:
- `--type <data_type>`: Type of data to upload (choices: all, users, portfolios, market, transactions, rules; default: all)

Uploads the generated data to your Firestore database.

### Update Market Data

```bash
python main.py update_market
```

Options:
- `--variation <percent>`: Maximum price variation percentage (default: 2.0)

Updates market prices with random variations to simulate market changes.

### Clear Firestore Data

```bash
python main.py clear
```

Options:
- `--type <data_type>`: Type of data to clear (choices: all, users, portfolios, market, transactions, rules; default: all)

Deletes specified data from the Firestore database.

## Schema

The Firestore database uses the following collections:

- **users**: User profiles, compliance status, and preferences
- **portfolios**: User cryptocurrency holdings and balances
- **market_data**: Cryptocurrency prices and exchange rates
- **transactions**: Trading and conversion history
- **compliance_rules**: Regional restrictions and rules

See `config/schema.json` for the complete schema definition.

## Integration with Trading Bot

This module is designed to be completely decoupled from the trading bot implementation. The bot can interact with the same Firestore database, but this module is only concerned with data generation and management.

To integrate with the trading bot:
1. Generate and upload data using this module
2. Configure the trading bot to connect to the same Firestore database
3. Implement API services in the bot to retrieve data from Firestore instead of using hardcoded mock data