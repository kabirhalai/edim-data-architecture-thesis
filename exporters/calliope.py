import duckdb

if __name__ == "__main__":
    # Connect to DuckDB
    conn = duckdb.connect(database='data/edim.duckdb')

    # Execute the SQL script
    results=conn.execute("SELECT * FROM gold/calliope_capacity;").fetch_df()

    results.to_csv('output/calliope_capacity.csv', index=False)

    # Close the connection
    conn.close()