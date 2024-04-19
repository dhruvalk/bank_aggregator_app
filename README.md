# Bank Statement Aggregator

Bank Statement Aggregator is a web application designed to streamline the process of managing and analyzing financial transactions from multiple bank accounts. By aggregating bank statements from various sources, the application provides users with a comprehensive overview of their financial activities, enabling them to track expenses, monitor cash flow, and gain valuable insights into their financial health.

## Features

- **Aggregation:** Consolidate bank statements from different financial institutions into a single, unified view.
- **Categorization:** Automatically categorize transactions based on predefined keywords, enhancing organization and analysis.
- **Visualization:** Visualize transaction data through intuitive charts and graphs, allowing users to identify spending patterns and trends.
- **Filtering:** Filter transactions by category, date range, and transaction type for detailed analysis and review.
- **User Authentication:** Secure user authentication and authorization system to ensure data privacy and confidentiality.

## Supported Banks

The Bank Statement Aggregator currently supports the following banks:

- DBS
- POSB
- OCBC
- UOB
- HSBC
- DBS Paylah!

(Note: The list of supported banks can be expanded in future updates.)

## Usage

### Prerequisites

- Python 3.x
- Flask

### Instructions

1. Clone the repository to your local machine:

```bash
git clone https://github.com/dhruvalk/bank-statement-aggregator.git
```

2. Navigate to the project directory:

```bash
cd bank-statement-aggregator
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the Flask application:

```bash
python app.py
```

5. Access the application in your web browser at http://localhost:5000.
6. Upload your own bank statements or use the sample data provided in the app/samples folder to explore the application's features.
