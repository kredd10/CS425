# CS425 Project

Project for Spring 2025

## Setup

### Prerequisites
- Python 3.6+
- pip
- PostgreSQL
- pgAdmin 4

### Installation

1. Clone the repository:
```bash
git clone https://github.com/kredd10/CS425.git
cd cs425
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

4. Install required dependencies:
```bash
pip install -r requirements.txt
```

### Database Setup

1. Open pgAdmin 4 and connect to your PostgreSQL server
2. Create a new database named `real_estate_db`
3. Run the SQL scripts in the following order:
   - First run `DDLcreate.sql` to create the database schema
   - Then run the data entry files in this order:
     - `DATAentry-user.sql`
     - `DATAentry-agent.sql`
     - `DATAentry-all.sql`

Alternatively, you can run the SQL files from the command line:
```bash
psql -U admin -d real_estate_db -f DDLcreate.sql
psql -U admin -d real_estate_db -f DATAentry-user.sql
psql -U admin -d real_estate_db -f DATAentry-agent.sql
psql -U admin -d real_estate_db -f DATAentry-all.sql
```

### Environment Configuration

The application uses environment variables for configuration:
- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://admin:secret@localhost:5432/real_estate_db`)
- `SECRET_KEY`: Secret key for Flask sessions
- `FLASK_CONFIG`: Configuration environment (`development`, `production`, or `testing`)

## Usage

After installation, you can use the command-line interface:

```bash
cs425 --help
```

To run the Flask application:
```bash
python run.py
```

## Development

To set up the development environment:

```bash
pip install -e ".[dev]"
```

## License

[Your License]
