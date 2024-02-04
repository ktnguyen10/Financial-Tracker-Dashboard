# Financial Dashboard
## Video Demo:  <https://youtu.be/Rl-kc3qla_w>
## Description:
This project is a Flask application that people 
can use to keep track of their finances through 
automated interactive charts and summaries.

Users are required to log into their own profile 
to access their financial information, and as such 
will be redirected to the login page if not already 
logged in. There is an option to register for an account
where the user will provide username, password, and income.
Once registered with a valid username and password, 
the username will become the identifier for querying 
financial data from the local database. 

The "Home" page contains a small table with the 
current and previous month's spend. This gives users
an immediate summary of how they are doing with their
budgeting progress and compare it tohow they did 
previously.

#### Future Release to include a more comprehensive breakdown of monthly expense and motivational messages to improve budgeting motivation.

Under the "Upload" page, users can upload bank 
statement or credit/debit card transaction data
in a txt or CSV format. For the current release,
the data must be tabular and contain specific
columns in order to successfully add transactions
into the database. Multiple file uploads are accepted.

The "Dashboard" page is a Plotly Dash dashboard with
various charts and tables to detail spending statistics 
and trends. Users can gain an understanding of their habits
and use this information to build a budget.

#### Future Release to include an operation to generate your own personalized budget based on provided income and spending habits.

User profiles is planned to contain their username, income, and option 
to change password. Other information is TBD while budget 
generator is under development.

## Dashboard Specifics
Data for the dashboard is taken from a sqlite3 local database, 
which is provided by user uploaded data. Data is queried from the
transactions table and users table using SQL and passed on to the 
Dash app. A series of pie charts, bar charts, a Sankey diagram, 
and tables can be used to observe annual, monthly, and overall spending
broken down by person and category. 

At the bottom of the dashboard is a series of tables for those 
who prefer a tabular format. Each plot has valuable information 
that can be extracted.


## Program File Specifics

* financial_dashboard
  * dashboard : initiates a Dash application
    * data_cleanup.py : data processing between SQLite3 database and results to display in Dash
    * data_helpers.py : additional tools that do not directly involve the dataset
  * routes : defines the folder architecture of the web application and initializes the database
    * paths.py : folder architecture
  * login_manager.py : deals with managing the username using shelve
  * gen_database.py : generates the database to be used in the web application
  * helpers.py : borrowed from CS50 Flask lecture to support functions in routes

### Financial Data Upload (\upload)
The uploading feature currently supports TXT and CSV files. It uses 
pandas read_csv function to save the data into a dataframe, which is 
then pushed to the sqlite3 database.

The upload feature supports multiple files at once through the use 
of a loop.

The files being uploaded must be in a particular format and have the following columns:
* Transaction Date: date of the transaction occurence
* Post Date: if credit card, date that the transaction was confirmed
* Description
* Category: category as defined by the bank
* Amount
* Custom Category: user defined categories, if applicable
* User: user defined, person who performed the purchase
* Custom Group: user defined groups, if applicable

Three additional columns are added to the table during upload:
* ID: incremental identification number of data row
* User ID: login username of current user
* Date: Transaction date without the time elements

#### Future Release to include dynamic column matching to avoid having to preprocess data before uploading.

### SQLite3 Database
The database contains a transactions table for finance information
and a users table for user login and salary information. When data is
pulled using the dashboard.data_cleanup.gen_dataframe() function, there
are several checks to ensure that there are no duplicate entries when 
using that data in the dashboard. These include:
* Setting categories referring to countries and cities as 'Travel'.
* Check spelling and capitalization to prevent duplicate categories.

Data is queried using SQL. The most important filter is using the 
login username to access only financial data that belongs to the user.

Data is processed using pandas. We use dataframes for fast accessibility 
and ease of use when working with tabular data. 

#### Future Release to include duplication checks at upload, prior to being pushed to the database.

## Design Choices

### Login Credentials
Credentials of the current login are stored using the shelve module. 
Only the login username is stored; this is for easy access among 
other functions in the program.

The login and logout schema was borrowed from the CS50 2023 Flask 
lecture, as well as a template for the .css file. 

### Procedural vs Object-Oriented
For the first iteration of this project and for the Final Project submission,
I went with a procedural format rather than Object-Oriented Programming for
quicker deployment. I plan to update the app to be fully OOP-based and set 
it up for personal use.



