# Finpilot-AI / Data Generator

High-performance synthetic retail transaction data generator engineered to simulate 2 to 5 million+ realistic records without incurring RAM spikes.

## Output Schema
| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `transaction_id` | String | Unique transaction identifier | `TXN_000000001` |
| `date` | Timestamp | Transaction timestamp (YYYY-MM-DD HH:MM:SS) | `2024-06-15 14:23:10` |
| `shop_id` | String | Shop/Store identifier | `SHOP_005` |
| `product` | String | Product name from catalog | `27-Inch 4K UHD Monitor` |
| `category` | String | Merchandising category | `Electronics` |
| `quantity` | Integer | Units purchased | `2` |
| `unit_price` | Float | Price per item ($) | `349.99` |
| `total` | Float | Calculated transaction total (`qty * unit_price`) | `699.98` |
| `customer_id` | String | Customer surrogate ID (Zipfian repeat buyer distribution) | `CUST_004128` |
| `payment_mode` | String | Payment method (`Credit Card`, `Debit Card`, `UPI`, `Cash`, `Digital Wallet`) | `Credit Card` |

## Usage

### Local CLI
```bash
pip install -r requirements.txt

# Generate 2 million records (default)
python generate.py --rows 2000000 --output output/retail_transactions.csv

# Generate 5 million records with custom chunk size
python generate.py --rows 5000000 --chunk-size 250000 --output output/retail_transactions_5m.csv
```

### Docker
```bash
docker build -t finpilot-generator .
docker run -v $(pwd)/output:/app/output finpilot-generator --rows 2000000
```
