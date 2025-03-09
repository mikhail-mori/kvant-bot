from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

def use_database(db_url: str, query: str, params: dict | None = None, fetchone: bool = True):
    """
    Execute a database query using SQLAlchemy.
    
    :param db_url: The database URL (e.g., 'sqlite:///database.db', 'postgresql://user:password@localhost/dbname')
    :type db_url: str
    
    :param query: The SQL query to execute
    :type query: str
    
    :param params: The parameters to bind to the query (optional)
    :type params: dict (default None)
    
    :param fetchone: If True, fetch only one result; otherwise, fetch all results
    :type fetchone: bool (default True)
    
    :return: The result of the query (tuple or list of tuples), or None if no results
    :rtype: tuple | list[tuple] | None
    
    Example of usage:
    use_database('sqlite:///database.db', 'SELECT * FROM users WHERE id = :id', {'id': 3})
    """
    # Initialize the engine
    engine = create_engine(db_url)
    try:
        # Connect to the database
        with engine.connect() as connection:
            # Execute the query with parameters
            result_proxy = connection.execute(text(query), params)
            
            # If the query modifies data (INSERT, UPDATE, DELETE), commit the transaction
            if not result_proxy.returns_rows:
                connection.commit()
            
            # Fetch the result based on the fetchone flag
            if result_proxy.returns_rows:
                result = result_proxy.fetchone() if fetchone else result_proxy.fetchall()
                if result is None:
                    logging.warning(f"No rows found for query: {query} with params: {params}")
            else:
                result = None
            
            # Log the executed query and its result
            logging.debug(f'Executed query "{query}" with parameters "{params}", returned "{result}"')
            return result

    except SQLAlchemyError as error:
        # Log any database errors
        logging.error(f'Database error: {error}')
        return None