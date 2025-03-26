import json
import random as rand
import time
import traceback
from datetime import UTC, datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from clip_creator.conf import (
    LOGGER,
    REDDIT_DOMAIN,
    REDDIT_POST_DOMAIN,
    SUB_REDDITS,
    SUB_REDDITS_COM,
)
from clip_creator.utils.scan_text import reg_get_og


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
        if "height<" in comment["text"]:
            continue
        if (
            len(comment["text"].split()) <= max_words
            and comment["upvotes"] > top_comment_upvotes
        ):
            top_comment = comment["text"]
            top_comment_upvotes = comment["upvotes"]
            top_comment_url = comment["url"]
    return top_comment, comments, top_comment_url


def next_page_finder(soup: BeautifulSoup, prefix: str):
    for element in soup.find_all("faceplate-partial"):
        if element.get("id") and element.get("id", "").startswith(prefix):
            return element.get("id", "").replace(prefix, "")
    return ""


def find_sub_reddit_posts(
    used_posts: list[str], min_posts: int = 10, max_posts: int = 20
) -> list[str]:
    """
    Find posts from a list of subreddits.
    """
    prefix = "partial-more-posts-"
    next_view = {}
    href_list: list[str] = []
    number_runs = 0
    rand_order_subs = SUB_REDDITS.copy()
    rand.shuffle(rand_order_subs)
    LOGGER.info(f"Subreddits in ran order: {rand_order_subs}")
    while len(href_list) < max_posts:
        for suby in tqdm(rand_order_subs, desc="Subreddit, finding posts"):
            try:
                if number_runs == 0:
                    response = requests.get(REDDIT_DOMAIN + suby)
                    soup = BeautifulSoup(response.content, "html.parser")
                    next_view[suby] = next_page_finder(soup, prefix)
                else:
                    response = requests.get(
                        REDDIT_DOMAIN + suby + "&after=" + next_view[suby] + "%3D%3D"
                    )
                    soup = BeautifulSoup(response.content, "html.parser")
                    next_view[suby] = next_page_finder(soup, prefix)

                # Find all article elements containing posts
                for article in soup.find_all("article", class_="w-full"):
                    # Extract the shreddit-post element
                    post = article.find("shreddit-post")

                    if post:
                        post_id = post.get("id")

                        # Skip if post ID is already processed
                        if post_id in used_posts:
                            continue

                        # Find the href in either of these locations
                        href = post.get("permalink") or post.find(
                            "a", {"slot": "full-post-link"}
                        ).get("href")

                        if href:
                            href_list.append(href)
                            used_posts.append(post_id)
            except Exception:
                LOGGER.error(
                    f"Error processing subreddit {suby}: {traceback.format_exc()}"
                )
                time.sleep(15)
        if number_runs > 10:
            break
        time.sleep(5)
        number_runs += 1

    return href_list


def extract_text_from_element(html_string):
    """
    Extracts text from a specified HTML element using BeautifulSoup.

    Args:
        html_string: The HTML string to parse.
        tag_name: The name of the HTML tag (e.g., 'p', 'div', 'span').
        attributes: A dictionary of attributes to filter the element.

    Returns:
        The text content of the found element, or None if not found.
    """
    soup = BeautifulSoup(html_string, "html.parser")

    text_body_div = soup.find(
        "div", class_="text-neutral-content", attrs={"slot": "text-body"}
    )

    if text_body_div:
        md_div = text_body_div.find("div", class_="md")
        if md_div:
            paragraphs = md_div.find_all("p")
            text = "\n".join(p.get_text() for p in paragraphs)
            return text
        else:
            LOGGER.error("Could not find the 'md' div.")

    else:
        LOGGER.error("Could not find the 'text-neutral-content' div.")
    return None


def extract_title_from_element(html_string):
    soup = BeautifulSoup(html_string, "html.parser")

    title_h1 = soup.find("h1", id="post-title-t3_1j0dzp4", attrs={"slot": "title"})

    if title_h1:
        text = title_h1.get_text(strip=True)
        LOGGER.debug("title: %s", text)
        return text
    else:
        LOGGER.error("Could not find the reddit post title element. %s", html_string)
        return None


def extract_all(html):
    soup = BeautifulSoup(html, "html.parser")
    post = soup.find("shreddit-post")

    if post:
        data = {
            "author": post.get("author"),
            "post-title": post.get("post-title"),
            "comment-count": int(post.get("comment-count", 0)),
            "created-timestamp": post.get("created-timestamp"),
            "score": int(post.get("score", 0)),
        }
        LOGGER.debug(data)
        return data
    else:
        LOGGER.error("Post not found")
        return {}


def reddit_posts_orch(
    href_list, used_posts: list | None = None, min_post: int = 10, max_post: int = 40
) -> list[dict]:
    """
    Orchestrates the process of finding Reddit posts.
    """

    if used_posts is None:
        used_posts = []
    posts = []
    for _i, href in tqdm(enumerate(href_list), desc="Processing posts"):
        queue = [href]
        while queue != []:
            try:
                if "/" not in queue[0] or "https" == queue[0]:
                    queue.pop(0)
                    continue
                url = REDDIT_POST_DOMAIN + queue.pop(0)
                if "www.reddit.comhttps" in str(url) or url == REDDIT_POST_DOMAIN:
                    continue
                try:
                    response_jboi = requests.get(url + ".json").json()
                except Exception:
                    LOGGER.debug(
                        f"Error getting author from json: {traceback.format_exc()}"
                    )
                    time.sleep(15)
                    continue
                json_data, try_again = reddit_json_all(response_jboi)
                if try_again:
                    try:
                        time.sleep(5)
                        response_jboi = requests.get(url + ".json").json()
                    except Exception:
                        LOGGER.debug(
                            f"Error getting author from json: {traceback.format_exc()}"
                        )
                        time.sleep(15)
                        continue
                    json_data, try_again = reddit_json_all(response_jboi)
                if json_data.get("score", 0) < 150:
                    continue
                og_links, content_text = reg_get_og(
                    json_data.get("content", ""), json_data.get("title", "")
                )

                # Get author from json
                if not content_text:
                    continue
                post = {
                    "title": json_data.get("title", ""),
                    "content": content_text,
                    "upvotes": json_data.get("score", 0),
                    "comments": json_data.get("comments", 0),
                    "nsfw": json_data.get("nsfw", 0),
                    "posted_at": json_data.get(
                        "posted_at",
                        datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f+0000"),
                    ),
                    "url": json_data.get("url", url),
                    "post_id": json_data.get("post_id", ""),
                    "author": json_data.get("author", ""),  # the username not the id
                    "parent_href": None if og_links == [] else og_links[-1],
                }
                posts.append(post)
                LOGGER.debug(f"Processed post: {post}")
            except Exception:
                LOGGER.error(f"Error processing post {href}: {traceback.format_exc()}")
                time.sleep(15)
            time.sleep(5)
            if not og_links or og_links == [href] or og_links == []:
                break
            queue.extend(og_links)

        # if i >= max_post:
        #     break
    return posts


def check_profile_reddit(author_id: str, post_id: str) -> list[dict]:
    """
    Check the profile of a Reddit user.
    """
    try:
        response = requests.get(f"https://www.reddit.com/user/{author_id}/about.json")
        response.raise_for_status()
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return []  # Return empty list if request fails

    except Exception as e:  # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        return []


def reddit_get_comments(html_str) -> list[dict]:
    """
    Get comments from a Reddit post.
    """
    soup = BeautifulSoup(html_str, "html.parser")

    comments = soup.find_all("shreddit-comment")
    comments_list = []
    for comment in comments:
        if "slot" not in comment.attrs or not comment.attrs["slot"].startswith(
            "children-"
        ):
            author = comment.get("author")
            score = comment.get("score")
            p_tag = comment.find("p")
            if p_tag:
                text = p_tag.get_text(strip=True)
                comments_list.append({"author": author, "score": score, "text": text})

    return comments_list


def format_href(href: str) -> str:
    """
    Format the href for a Reddit post to get comment url.
    """
    tmp_href = ""
    for i, url_part in enumerate(href.split("/")):
        if i < 3:
            tmp_href += "/" + url_part
    return tmp_href


def find_sub_reddit_coms(used_posts: list[str], min_posts: int = 10) -> list[str]:
    """
    Find posts from a list of subreddits.
    """
    prefix = "partial-more-posts-"
    next_view = {}
    href_list: list[str] = []
    number_runs = 0
    rand_order_subs = SUB_REDDITS_COM.copy()
    rand.shuffle(rand_order_subs)
    while len(href_list) < min_posts:
        for suby in tqdm(rand_order_subs, desc="Subreddit, finding posts"):
            try:
                if number_runs == 0:
                    response = requests.get(REDDIT_DOMAIN + suby)
                    soup = BeautifulSoup(response.content, "html.parser")
                    next_view[suby] = next_page_finder(soup, prefix)
                else:
                    response = requests.get(
                        REDDIT_DOMAIN + suby + "&after=" + next_view[suby] + "%3D%3D"
                    )
                    soup = BeautifulSoup(response.content, "html.parser")
                    next_view[suby] = next_page_finder(soup, prefix)

                # Find all article elements containing posts
                for article in soup.find_all("article", class_="w-full"):
                    # Extract the shreddit-post element
                    post = article.find("shreddit-post")

                    if post:
                        post_id = post.get("id")

                        # Skip if post ID is already processed
                        if post_id in used_posts:
                            continue

                        # Find the href in either of these locations
                        href = post.get("permalink") or post.find(
                            "a", {"slot": "full-post-link"}
                        ).get("href")

                        if href:
                            href_list.append(href)
                            used_posts.append(post_id)
            except Exception:
                LOGGER.error(
                    f"Error processing subreddit {suby}: {traceback.format_exc()}"
                )
                time.sleep(15)
        if number_runs > min_posts:
            break
        time.sleep(5)
        number_runs += 1

    return href_list


def find_top_sub_reddit_posts(used_posts: list[str], min_posts: int = 10) -> list[str]:
    """
    Find posts from a list of subreddits.
    """
    prefix = "partial-more-posts-"
    next_view = {}
    href_list: list[str] = []
    number_runs = 0
    rand_order_subs = SUB_REDDITS.copy()
    suffix = "/top/?t=all"
    rand.shuffle(rand_order_subs)
    while len(href_list) < min_posts:
        for suby in tqdm(rand_order_subs, desc="Subreddit, finding posts"):
            try:
                if number_runs == 0:
                    response = requests.get(REDDIT_DOMAIN + suby + suffix)
                    soup = BeautifulSoup(response.content, "html.parser")
                    next_view[suby] = next_page_finder(soup, prefix)
                else:
                    response = requests.get(
                        REDDIT_DOMAIN
                        + suby
                        + suffix
                        + "&after="
                        + next_view[suby]
                        + "%3D%3D"
                    )
                    soup = BeautifulSoup(response.content, "html.parser")
                    next_view[suby] = next_page_finder(soup, prefix)

                # Find all article elements containing posts
                for article in soup.find_all("article", class_="w-full"):
                    # Extract the shreddit-post element
                    post = article.find("shreddit-post")

                    if post:
                        post_id = post.get("id")

                        # Skip if post ID is already processed
                        if post_id in used_posts:
                            continue

                        # Find the href in either of these locations
                        href = post.get("permalink") or post.find(
                            "a", {"slot": "full-post-link"}
                        ).get("href")

                        if href:
                            href_list.append(href)
                            used_posts.append(post_id)
            except Exception:
                LOGGER.error(
                    f"Error processing subreddit {suby}: {traceback.format_exc()}"
                )
                time.sleep(15)
        if number_runs > 30:
            break
        time.sleep(5)
        number_runs += 1

    return href_list


def find_top_sub_reddit_coms(used_posts: list[str], min_posts: int = 10) -> list[str]:
    """
    Find posts from a list of subreddits.
    """
    prefix = "partial-more-posts-"
    next_view = {}
    href_list: list[str] = []
    number_runs = 0
    rand_order_subs = SUB_REDDITS_COM.copy()
    suffix = "/top/?t=all"
    rand.shuffle(rand_order_subs)
    while len(href_list) < min_posts:
        for suby in tqdm(rand_order_subs, desc="Subreddit, finding posts"):
            try:
                if number_runs == 0:
                    response = requests.get(REDDIT_DOMAIN + suby + suffix)
                    soup = BeautifulSoup(response.content, "html.parser")
                    next_view[suby] = next_page_finder(soup, prefix)
                else:
                    response = requests.get(
                        REDDIT_DOMAIN
                        + suby
                        + suffix
                        + "&after="
                        + next_view[suby]
                        + "%3D%3D"
                    )
                    soup = BeautifulSoup(response.content, "html.parser")
                    next_view[suby] = next_page_finder(soup, prefix)

                # Find all article elements containing posts
                for article in soup.find_all("article", class_="w-full"):
                    # Extract the shreddit-post element
                    post = article.find("shreddit-post")

                    if post:
                        post_id = post.get("id")

                        # Skip if post ID is already processed
                        if post_id in used_posts:
                            continue

                        # Find the href in either of these locations
                        href = post.get("permalink") or post.find(
                            "a", {"slot": "full-post-link"}
                        ).get("href")

                        if href:
                            href_list.append(href)
                            used_posts.append(post_id)
            except Exception:
                LOGGER.error(
                    f"Error processing subreddit {suby}: {traceback.format_exc()}"
                )
                time.sleep(15)
        if number_runs > 30:
            break
        time.sleep(5)
        number_runs += 1

    return href_list


def straight_update_reddit(href: str) -> dict:
    try:
        if "www.reddit.com" not in href:
            href = REDDIT_POST_DOMAIN + href
        LOGGER.info(f"href: {href}")
        try:
            response = requests.get(href + ".json").json()
            if response is None or response == {}:
                time.sleep(15)
                response = requests.get(href + ".json").json()
        except Exception:
            LOGGER.debug(f"Error getting author from json: {traceback.format_exc()}")
            time.sleep(15)
            response = requests.get(href + ".json").json()
        LOGGER.debug(f"response: {response}")
        datasx, _ = reddit_json_all(response)
        LOGGER.info(f"datasx: {datasx}")
        _, content = reg_get_og(datasx.get("content", ""), datasx.get("title", ""))
        post = {
            "title": datasx.get("title", ""),
            "content": content,
            "upvotes": datasx.get("score", 0),
            "comments": datasx.get("comments", 0),
            "nsfw": datasx.get("nsfw", False),
            "posted_at": datasx.get(
                "posted_at", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f+0000")
            ),
            "url": datasx.get("url", href),
            "post_id": datasx.get("post_id", ""),
            "author": datasx.get("author", ""),  # the username not the id
        }
        return post
    except Exception:
        LOGGER.debug(f"Error getting author from json: {traceback.format_exc()}")
        time.sleep(15)
        return {}


def straight_update_reddit_coms(href: str) -> dict:
    try:
        if "www.reddit.com" not in href:
            href = REDDIT_POST_DOMAIN + href
        LOGGER.info(f"href: {href}")
        try:
            response = requests.get(REDDIT_POST_DOMAIN + href + ".json").json()
            if response is None or response == {}:
                time.sleep(15)
                try_again = True
            else:
                datasx, try_again = reddit_json_all(response)
            if try_again:
                try:
                    time.sleep(5)
                    response = requests.get(REDDIT_POST_DOMAIN + href + ".json").json()
                except Exception:
                    LOGGER.debug(
                        f"Error getting author from json: {traceback.format_exc()}"
                    )
                    time.sleep(5)
                    return {}
                datasx, _ = reddit_json_all(response)

            post = {
                "title": datasx.get("title", ""),
                "content": datasx.get("content", ""),
                "upvotes": datasx.get("score", 0),
                "comments": datasx.get("comments", 0),
                "nsfw": datasx.get("nsfw", False),
                "posted_at": datasx.get(
                    "posted_at", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f+0000")
                ),
                "url": datasx.get("url", href),
                "post_id": datasx.get("post_id", ""),
                "author": datasx.get("author", ""),  # the username not the id
                "comments_list": datasx.get("comments_list", []),
            }
            return post
        except Exception:
            LOGGER.error(f"Error processing post {href}: {traceback.format_exc()}")
            time.sleep(5)
            return {}
    except Exception:
        LOGGER.error(f"Error processing post {href}: {traceback.format_exc()}")
        time.sleep(5)
        return {}


def reddit_json_all(dict_list: list[dict]):
    """
    Extracts the needed info from a json from reddit."""
    # find post and comments sections
    post_data: dict = {
        "title": None,
        "author": None,
        "score": 0,
        "comments": None,
        "url": None,
        "nsfw": None,
        "comments_list": [],
        "content": None,
        "posted_at": None,
        "post_id": None,
    }
    try_again = False
    for ppart in dict_list:
        if isinstance(ppart, str):
            try_again = True
            continue
        if ppart.get("kind", "") == "Listing":
            datap = ppart.get("data", {})
            for child in datap.get("children", []):
                if child.get("kind") == "t3":  # t3 is a post
                    data = child.get("data", {})
                    post_data["title"] = data.get("title")
                    post_data["author"] = data.get("author")
                    post_data["score"] = int(data.get("score", 0))
                    post_data["comments"] = int(data.get("num_comments", 0))
                    post_data["url"] = data.get("permalink")
                    post_data["nsfw"] = data.get("over_18")
                    post_data["content"] = data.get("selftext")
                    post_data["posted_at"] = datetime.fromtimestamp(
                        data.get("created_utc"), UTC
                    ).strftime("%Y-%m-%dT%H:%M:%S.%f+0000")
                    post_data["post_id"] = data.get("id")

                elif child.get("kind") == "t1":  # t1 is a comment
                    data = child.get("data", {})
                    if int(data.get("score", 0)) < 1:
                        continue
                    comment = {
                        "author": data.get("author"),
                        "upvotes": int(data.get("score", 0)),
                        "content": data.get("body"),
                        "parent_id": data.get("parent_id"),
                        "posted_at": datetime.fromtimestamp(
                            data.get("created_utc"), UTC
                        ).strftime("%Y-%m-%dT%H:%M:%S.%f+0000"),
                        "best_reply": {},
                    }
                    best_comment: dict[str, int | str] = {"upvotes": 0}
                    if data.get("replies") == "":
                        continue
                    for kid in (
                        data.get("replies", {}).get("data", {}).get("children", [])
                    ):
                        if kid.get("kind") == "t1":
                            kid_data = kid.get("data", {})
                            if int(kid_data.get("score", 0)) < 2:
                                continue
                            if kid_data.get("score", 0) > best_comment.get(
                                "upvotes", 0
                            ):
                                best_comment = {
                                    "author": kid_data.get("author"),
                                    "upvotes": int(kid_data.get("score", 0)),
                                    "content": kid_data.get("body"),
                                    "posted_at": datetime.fromtimestamp(
                                        kid_data.get("created_utc"), UTC
                                    ).strftime("%Y-%m-%dT%H:%M:%S.%f+0000"),
                                    "parent_id": kid_data.get("parent_id"),
                                }
                    comment["reply"] = best_comment
                    post_data["comments_list"].append(comment)
    if post_data.get("title") is None:
        try_again = True
    return post_data, try_again


def reddit_coms_orch(
    href_list, used_posts: list | None = None, min_post: int = 10, max_post: int = 20
) -> list[dict]:
    """
    Orchestrates the process of finding Reddit posts.
    """

    if used_posts is None:
        used_posts = []
    posts = []
    for _i, href in tqdm(enumerate(href_list), desc="Processing posts"):
        try:
            response = requests.get(REDDIT_POST_DOMAIN + href + ".json").json()
            if response is None:
                continue
            datasx, try_again = reddit_json_all(response)
            if try_again:
                try:
                    time.sleep(5)
                    response = requests.get(REDDIT_POST_DOMAIN + href + ".json").json()
                except Exception:
                    LOGGER.debug(
                        f"Error getting author from json: {traceback.format_exc()}"
                    )
                    time.sleep(15)
                    continue
                datasx, try_again = reddit_json_all(response)

            post = {
                "title": datasx.get("title", ""),
                "content": datasx.get("content", ""),
                "upvotes": datasx.get("score", 0),
                "comments": datasx.get("comments", 0),
                "nsfw": datasx.get("nsfw", False),
                "posted_at": datasx.get(
                    "posted_at", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f+0000")
                ),
                "url": datasx.get("url", href),
                "post_id": datasx.get("post_id", ""),
                "author": datasx.get("author", ""),  # the username not the id
                "comments_list": datasx.get("comments_list", []),
            }
            posts.append(post)
        except Exception:
            LOGGER.error(f"Error processing post {href}: {traceback.format_exc()}")
            time.sleep(15)
        time.sleep(5)
    return posts


if __name__ == "__main__":
    print(
        straight_update_reddit(
            "/r/AmItheAsshole/comments/1j9dagd/aita_for_taking_an_uber_home_instead_of_sitting/"
        )
    )
