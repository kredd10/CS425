# Real Estate Management Application


Database Organization Project (CS425) for Spring 2025

### Team Members
1. Kimberley Catherine Goveas
2. Manish Kamalakar Reddy
3. Elijah Perez

## Setup

### Prerequisites
- Python 3.6+
- pip
- PostgreSQL

### Installation

1. Clone the repository:
```bash
git clone https://github.com/kredd10/CS425.git
```

2. Create and activate a virtual environment:
```bash
# Create the environment
python -m venv .venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source .venv/bin/activate
```

3. Install required dependencies:

```bash
python3 -m pip install -r requirements.txt
```

### Database Setup

You must run the following SQL files to setup the database.

1. The `DDLcreate.sql` contains all the `CREATE TABLE` commands.
2. The remaining data files must be loaded in the following order:
    1. `DATAentry-user.sql`
    2. `DATAentry-agent.sql`
    3. `DATAentry-all.sql`


### Application Configuration
You can configure the database URL and secret key under `config.py`.

The database URI must follow the format: `postgresql://<username>:<password>@<host>/<database>`

## Usage

To run the Flask application:
```bash
python app.py
```
