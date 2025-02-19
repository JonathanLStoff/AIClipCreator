import json

import requests
from bs4 import BeautifulSoup


def search_reddit(videoid: str) -> list[dict]:
    """
    Fetch data from the given URL using a GET request.

    Args:
        videoid (str): The videoid to send the GET request to.

    Returns:
        str or None: The response text if the request is successful;
                     None if an error occurs.
    """
    try:
        response = requests.get(
            f" https://www.reddit.com/search/?q={videoid}&type=posts&sort=relevance"
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        results = []

        # Find all the elements with the data-testid="search-sdui-post" attribute. This assumes
        # each result is contained within such an element. Adjust if the structure is different.
        result_elements = soup.find_all(
            "search-telemetry-tracker", {"data-testid": "search-sdui-post"}
        )

        for result_element in result_elements:
            try:
                # Extract the JSON from the data-faceplate-tracking-context attribute
                json_data_str = result_element.get("data-faceplate-tracking-context")
                if json_data_str:
                    json_data = json.loads(json_data_str)

                    # Extract the title and URL
                    title_element = result_element.find(
                        "a", {"data-testid": "post-title"}
                    )
                    title = title_element.text.strip() if title_element else None
                    url = title_element.get("href") if title_element else None

                    # Extract subreddit name
                    subreddit_element = result_element.find(
                        "a",
                        {
                            "class": (
                                "flex items-center text-neutral-content-weak"
                                " font-semibold"
                            )
                        },
                    )
                    subreddit_name = (
                        subreddit_element.text.strip().replace("r/", "")
                        if subreddit_element
                        else None
                    )

                    # Extract votes and comments
                    counter_elements = result_element.find_all(
                        "div", {"data-testid": "search-counter-row"}
                    )
                    votes = None
                    comments = None

                    if counter_elements:
                        for counter_element in counter_elements:
                            vote_span = counter_element.find_all("span")[0]
                            comment_span = counter_element.find_all("span")[2]

                            votes = (
                                int(vote_span.find("faceplate-number").get("number"))
                                if vote_span.find("faceplate-number")
                                else None
                            )
                            comments = (
                                int(comment_span.find("faceplate-number").get("number"))
                                if comment_span.find("faceplate-number")
                                else None
                            )

                    result = {
                        "title": title,
                        "url": url,
                        "subreddit": subreddit_name,
                        "votes": votes,
                        "comments": comments,
                        "post_id": json_data.get("post", {}).get(
                            "id"
                        ),  # Include other json data if needed
                        "nsfw": json_data.get("search", {}).get("nsfw"),
                        # ... other data from json_data as needed
                    }
                    results.append(result)

            except (json.JSONDecodeError, AttributeError, ValueError) as e:
                print(f"Error parsing a result: {e}")
                continue  # Skip to the next result if there's an error

        return results

    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return []  # Return empty list if request fails

    except Exception as e:  # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        return []


def check_top_comment(
    search_results: list[dict], max_words: int
) -> tuple[str | None, list[dict]]:
    """
    Check the top comment from the search results.

    Args:
        search_results (list[dict]): A list of search results.

    Returns:
        str: The top comment text, or an error message if no comment is found.
    """
    top_comment = None
    top_comment_upvotes = 0
    top_comment_url = ""
    comments: list[dict] = []
    for result in search_results:
        try:
            comment_url = (
                f' https://www.reddit.com/svc/shreddit/comments/r/playstation/t3_{result["url"].split("comments/")[-1].split("/")[0]}?render-mode=partial&is_lit_ssr=false&force_seo=1'
            )
            response = requests.get(comment_url)
            soup = BeautifulSoup(response.content, "html.parser")

            comment_elements = soup.find_all("shreddit-comment")

            for comment_element in comment_elements:
                try:
                    author = comment_element.get("author")

                    # Find the <p> tag within the comment content
                    p_tag = (
                        comment_element.find("div", {"slot": "comment"}).find("p")
                        if comment_element.find("div", {"slot": "comment"})
                        else None
                    )
                    comment_text = p_tag.text.strip() if p_tag else ""

                    # Extract upvotes (score)
                    upvotes = (
                        int(comment_element.get("score", 0))
                        if comment_element.get("score")
                        else 0
                    )

                    comments.append({
                        "author": author,
                        "text": comment_text,
                        "upvotes": upvotes,
                        "url": comment_url,
                    })

                except (AttributeError, ValueError) as e:
                    print(f"Error parsing a comment: {e}")
                    continue  # Skip to the next comment

        except requests.exceptions.RequestException as e:
            print(f"Error during request: {e}")
            continue

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            continue

    for comment in comments:
        if (
            len(comment["text"].split()) <= max_words
            and comment["upvotes"] > top_comment_upvotes
        ):
            top_comment = comment["text"]
            top_comment_upvotes = comment["upvotes"]
            top_comment_url = comment["url"]
    return top_comment, comments, top_comment_url
