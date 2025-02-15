import requests

def search_data(videoid:str):
    """
    Fetch data from the given URL using a GET request.

    Args:
        url (str): The URL to send the GET request to.

    Returns:
        str or None: The response text if the request is successful;
                     None if an error occurs.
    """
    try:
        response = requests.get(f'reddit.com/search/?q={videoid}&type=posts&sort=relevance')
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"An error occurred during the GET request: {e}")
        return None

if __name__ == "__main__":
    # Example usage: Get the latest posts from r/python on Reddit.
    test_url = "https://api.reddit.com/r/python"
    result = fetch_data(test_url)
    
    if result:
        print("Data retrieved successfully!")
        print(result)
    else:
        print("Failed to retrieve data.")