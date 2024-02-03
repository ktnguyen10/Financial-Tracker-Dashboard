# Financial Dashboard
### Video Demo:  <URL HERE>
### Description:
This project is a Flask application that people 
can use to keep track of their finances through 
automated interactive charts and summaries.

Users are required to log into their own profile 
to access their financial information. Once 
registered with a valid username and password, the
username will become the identifier for querying
financial data from the local database. 

The "Home" page contains a small table with the 
current and previous month's spend.

Under the "Upload" page, users can upload bank 
statement or credit/debit card transaction data
in a txt or CSV format. For the current release,
the data must be tabular and contain specific
columns in order to successfully add transactions
into the database. Multiple file uploads are accepted.

#### Future Release to include dynamic column matching to avoid having to preprocess data before uploading.

The "Dashboard" page is a Plotly Dash dashboard with
various charts and tables to detail spending statistics 
and trends. Users can gain an understanding of their habits
and use this information to build a budget.

#### Future Release to include an operation to generate your own personalized budget based on provided income and spending habits.

User profiles will contain their income. Other information 
is TBD while budget generator is under development.