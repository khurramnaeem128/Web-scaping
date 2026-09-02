from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

import json
import time
import re


# ============================================================
# SETTINGS
# ============================================================

SCROLL_COUNT = 20
WAIT_AFTER_PROFILE = 5
WAIT_AFTER_REEL = 4


# ============================================================
# ASK USER FOR INSTAGRAM USERNAME
# ============================================================

username = input("Enter Instagram username: ").strip()

if not username:
    print("Username cannot be empty.")
    exit()


# ============================================================
# CHROME
# ============================================================

options = Options()

options.add_argument("--start-maximized")

options.add_argument(
    "--disable-blink-features=AutomationControlled"
)

driver = webdriver.Chrome(options=options)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(text):

    if not text:
        return None

    return " ".join(text.split())


def absolute_url(url):

    if not url:
        return None

    if url.startswith("/"):
        return "https://www.instagram.com" + url

    return url


def extract_number_from_text(text, pattern):

    if not text:
        return None

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# PROFILE OBJECT
# ============================================================

profile = {

    "username": username,

    "profile_url":
        f"https://www.instagram.com/{username}/",

    "full_name": None,

    "bio": None,

    "followers": None,

    "followers_exact": None,

    "following": None,

    "following_exact": None,

    "posts": None,

    "posts_exact": None,

    "profile_picture": None,

    "website": None,

    "verified": False,

    "reels": []

}


try:

    # ========================================================
    # OPEN PROFILE
    # ========================================================

    print("\nOpening Instagram...")

    driver.get(
        profile["profile_url"]
    )

    time.sleep(
        WAIT_AFTER_PROFILE
    )

    print("Profile opened.")


    # ========================================================
    # SCROLL PROFILE
    # ========================================================

    print("\nLoading posts and Reels...")

    old_height = 0

    for i in range(SCROLL_COUNT):

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

        time.sleep(2)

        new_height = driver.execute_script(
            "return document.body.scrollHeight"
        )

        print(
            f"Scroll {i + 1}/{SCROLL_COUNT}"
        )

        if new_height == old_height:
            break

        old_height = new_height


    # ========================================================
    # PARSE PROFILE HTML
    # ========================================================

    html = driver.page_source

    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    # ========================================================
    # PROFILE PICTURE
    # ========================================================

    profile_img = soup.find(
        "img",
        alt=re.compile(
            r"profile picture",
            re.IGNORECASE
        )
    )

    if profile_img:

        profile["profile_picture"] = (
            profile_img.get("src")
        )


    # ========================================================
    # PROFILE TITLE
    # ========================================================

    title = soup.find("title")

    if title:

        title_text = clean_text(
            title.get_text()
        )

        if title_text:

            profile["full_name"] = (
                title_text
            )


    # ========================================================
    # PROFILE DESCRIPTION
    # ========================================================

    description = soup.find(
        "meta",
        attrs={
            "name": "description"
        }
    )

    profile_description = ""

    if description:

        description_text = (
            description.get("content")
        )

        if description_text:

            profile_description = clean_text(
                description_text
            )

            profile["bio"] = (
                profile_description
            )


    # ========================================================
    # EXTRACT PROFILE COUNTS FROM DESCRIPTION
    # ========================================================

    # Example:
    #
    # 269M Followers, 195 Following, 32K Posts
    #
    # Instagram often puts these numbers inside
    # the meta description.


    # ========================================================
    # FOLLOWERS
    # ========================================================

    followers_match = re.search(
        r"([\d,.]+[KMB]?)\s+Followers",
        profile_description,
        re.IGNORECASE
    )

    if followers_match:

        profile["followers"] = (
            followers_match.group(1)
        )


    # ========================================================
    # EXACT FOLLOWERS
    # ========================================================

    # Look for exact number in title attributes.

    for tag in soup.find_all(
        attrs={"title": True}
    ):

        title_value = clean_text(
            tag.get("title")
        )

        if not title_value:
            continue

        if not re.fullmatch(
            r"[\d,]+",
            title_value
        ):
            continue

        parent_text = ""

        if tag.parent:

            parent_text = tag.parent.get_text(
                " ",
                strip=True
            )

        if "followers" in parent_text.lower():

            profile["followers_exact"] = (
                title_value
            )

            break


    # ========================================================
    # FOLLOWING
    # ========================================================

    following_match = re.search(
        r"([\d,.]+[KMB]?)\s+Following",
        profile_description,
        re.IGNORECASE
    )

    if following_match:

        profile["following"] = (
            following_match.group(1)
        )


    # ========================================================
    # EXACT FOLLOWING
    # ========================================================

    if following_match:

        profile["following_exact"] = (
            following_match.group(1)
        )


    # ========================================================
    # POSTS
    # ========================================================

    posts_match = re.search(
        r"([\d,.]+[KMB]?)\s+Posts",
        profile_description,
        re.IGNORECASE
    )

    if posts_match:

        profile["posts"] = (
            posts_match.group(1)
        )


    # ========================================================
    # EXACT POSTS
    # ========================================================

    if posts_match:

        posts_value = (
            posts_match.group(1)
        )

        try:

            clean_posts = (
                posts_value
                .replace(",", "")
                .upper()
            )

            if clean_posts.endswith("K"):

                number = float(
                    clean_posts[:-1]
                )

                exact_posts = int(
                    number * 1000
                )

            elif clean_posts.endswith("M"):

                number = float(
                    clean_posts[:-1]
                )

                exact_posts = int(
                    number * 1000000
                )

            elif clean_posts.endswith("B"):

                number = float(
                    clean_posts[:-1]
                )

                exact_posts = int(
                    number * 1000000000
                )

            else:

                exact_posts = int(
                    clean_posts
                )

            profile["posts_exact"] = (
                f"{exact_posts:,}"
            )

        except:

            profile["posts_exact"] = (
                posts_value
            )


    # ========================================================
    # WEBSITE
    # ========================================================

    for link in soup.find_all("a"):

        href = link.get("href")

        if not href:
            continue

        if (
            "instagram.com" not in href
            and href.startswith("http")
        ):

            profile["website"] = href

            break


    # ========================================================
    # PAGE TEXT
    # ========================================================

    page_text = soup.get_text(
        " ",
        strip=True
    )


    # ========================================================
    # VERIFIED
    # ========================================================

    if "verified" in page_text.lower():

        profile["verified"] = True


    # ========================================================
    # PRINT PROFILE DATA
    # ========================================================

    print("\n")
    print("=" * 70)

    print("PROFILE DATA")

    print("=" * 70)

    print(
        "Username:",
        profile["username"]
    )

    print(
        "Followers:",
        profile["followers"]
    )

    print(
        "Exact Followers:",
        profile["followers_exact"]
    )

    print(
        "Following:",
        profile["following"]
    )

    print(
        "Exact Following:",
        profile["following_exact"]
    )

    print(
        "Posts:",
        profile["posts"]
    )

    print(
        "Exact Posts:",
        profile["posts_exact"]
    )

    print(
        "Bio:",
        profile["bio"]
    )


    # ========================================================
    # FIND REEL URLS
    # ========================================================

    print("\nFinding Reels...")

    all_links = soup.find_all(
        "a",
        href=True
    )

    reel_urls = []

    seen = set()

    for link in all_links:

        href = link.get("href")

        if not href:
            continue

        if "/reel/" not in href:
            continue

        reel_url = absolute_url(
            href
        )

        reel_url = reel_url.split("?")[0]

        if reel_url not in seen:

            seen.add(
                reel_url
            )

            reel_urls.append(
                reel_url
            )


    print(
        f"Found {len(reel_urls)} Reels."
    )


    # ========================================================
    # PROCESS EACH REEL
    # ========================================================

    for index, reel_url in enumerate(
        reel_urls,
        start=1
    ):

        print("\n")
        print("=" * 70)

        print(
            f"VIDEO {index} / {len(reel_urls)}"
        )

        print("=" * 70)

        print(
            "URL:",
            reel_url
        )


        # ====================================================
        # REEL OBJECT
        # ====================================================

        reel = {

            "video_number": index,

            "username": username,

            "url": reel_url,

            "shortcode": None,

            "caption": None,

            "hashtags": [],

            "mentions": [],

            "likes": None,

            "comments": None,

            "date": None,

            "video_url": None,

            "thumbnail": None,

            "duration": None,

            "location": None,

            "alt_text": None,

            "description": None

        }


        try:

            # =================================================
            # OPEN REEL
            # =================================================

            driver.get(
                reel_url
            )

            time.sleep(
                WAIT_AFTER_REEL
            )


            # =================================================
            # GET HTML
            # =================================================

            reel_html = driver.page_source

            reel_soup = BeautifulSoup(
                reel_html,
                "html.parser"
            )


            # =================================================
            # SHORTCODE
            # =================================================

            shortcode_match = re.search(
                r"/reel/([^/?]+)",
                reel_url
            )

            if shortcode_match:

                reel["shortcode"] = (
                    shortcode_match.group(1)
                )


            # =================================================
            # VIDEO ELEMENT
            # =================================================

            video = reel_soup.find(
                "video"
            )

            if video:

                video_src = video.get(
                    "src"
                )

                poster = video.get(
                    "poster"
                )

                duration = video.get(
                    "duration"
                )


                if video_src:

                    reel["video_url"] = (
                        video_src
                    )


                if poster:

                    reel["thumbnail"] = (
                        poster
                    )


                if duration:

                    reel["duration"] = (
                        duration
                    )


            # =================================================
            # OPEN GRAPH VIDEO
            # =================================================

            og_video = reel_soup.find(
                "meta",
                property="og:video"
            )

            if og_video:

                og_video_url = (
                    og_video.get("content")
                )

                if og_video_url:

                    reel["video_url"] = (
                        og_video_url
                    )


            # =================================================
            # OPEN GRAPH IMAGE
            # =================================================

            og_image = reel_soup.find(
                "meta",
                property="og:image"
            )

            if og_image:

                reel["thumbnail"] = (
                    og_image.get("content")
                )


            # =================================================
            # DESCRIPTION
            # =================================================

            og_description = reel_soup.find(
                "meta",
                property="og:description"
            )

            if og_description:

                reel["description"] = clean_text(
                    og_description.get(
                        "content"
                    )
                )


            # =================================================
            # META DESCRIPTION
            # =================================================

            meta_description = reel_soup.find(
                "meta",
                attrs={
                    "name": "description"
                }
            )

            if meta_description:

                description_text = (
                    meta_description.get(
                        "content"
                    )
                )

                if description_text:

                    reel["description"] = (
                        clean_text(
                            description_text
                        )
                    )


            # =================================================
            # ALT TEXT
            # =================================================

            images = reel_soup.find_all(
                "img"
            )

            for image in images:

                alt = image.get(
                    "alt"
                )

                if alt:

                    alt = clean_text(
                        alt
                    )

                    if (
                        alt
                        and username.lower()
                        in alt.lower()
                    ):

                        reel["alt_text"] = (
                            alt
                        )

                        break


            # =================================================
            # CAPTION
            # =================================================

            if reel["description"]:

                reel["caption"] = (
                    reel["description"]
                )


            if not reel["caption"]:

                reel["caption"] = (
                    reel["alt_text"]
                )


            # =================================================
            # HASHTAGS
            # =================================================

            if reel["caption"]:

                reel["hashtags"] = re.findall(
                    r"#\w+",
                    reel["caption"]
                )


            # =================================================
            # MENTIONS
            # =================================================

            if reel["caption"]:

                reel["mentions"] = re.findall(
                    r"@\w+",
                    reel["caption"]
                )


            # =================================================
            # DATE
            # =================================================

            time_tag = reel_soup.find(
                "time"
            )

            if time_tag:

                reel["date"] = (
                    time_tag.get(
                        "datetime"
                    )
                )


            # =================================================
            # LIKES
            # =================================================

            likes_match = re.search(
                r"([\d,.]+[KMB]?)\s+likes?",
                reel["description"] or "",
                re.IGNORECASE
            )

            if likes_match:

                reel["likes"] = (
                    likes_match.group(1)
                )


            # =================================================
            # COMMENTS
            # =================================================

            comments_match = re.search(
                r"([\d,.]+[KMB]?)\s+comments?",
                reel["description"] or "",
                re.IGNORECASE
            )

            if comments_match:

                reel["comments"] = (
                    comments_match.group(1)
                )


            # =================================================
            # LOCATION
            # =================================================

            location_links = (
                reel_soup.find_all(
                    "a",
                    href=True
                )
            )

            for location_link in location_links:

                href = location_link.get(
                    "href"
                )

                if not href:
                    continue

                if (
                    "/explore/locations/"
                    in href
                ):

                    location_text = clean_text(
                        location_link.get_text(
                            " ",
                            strip=True
                        )
                    )

                    if location_text:

                        reel["location"] = (
                            location_text
                        )

                        break


            # =================================================
            # ADD REEL
            # =================================================

            profile["reels"].append(
                reel
            )


            # =================================================
            # SHOW VIDEO RESULT
            # =================================================

            print("\nVIDEO DATA")

            print(
                "Shortcode:",
                reel["shortcode"]
            )

            print(
                "Caption:",
                reel["caption"]
            )

            print(
                "Hashtags:",
                reel["hashtags"]
            )

            print(
                "Mentions:",
                reel["mentions"]
            )

            print(
                "Likes:",
                reel["likes"]
            )

            print(
                "Comments:",
                reel["comments"]
            )

            print(
                "Date:",
                reel["date"]
            )

            print(
                "Duration:",
                reel["duration"]
            )

            print(
                "Location:",
                reel["location"]
            )

            print(
                "Video URL:",
                reel["video_url"]
            )


        except Exception as error:

            print(
                "Error scraping this Reel:",
                error
            )


    # ========================================================
    # SAVE JSON
    # ========================================================

    filename = (
        f"{username}_instagram_data.json"
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            profile,
            file,
            indent=4,
            ensure_ascii=False
        )


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n")
    print("=" * 70)

    print(
        "INSTAGRAM SCRAPING COMPLETE"
    )

    print("=" * 70)

    print(
        "Username:",
        profile["username"]
    )

    print(
        "Followers:",
        profile["followers"]
    )

    print(
        "Exact Followers:",
        profile["followers_exact"]
    )

    print(
        "Following:",
        profile["following"]
    )

    print(
        "Exact Following:",
        profile["following_exact"]
    )

    print(
        "Posts:",
        profile["posts"]
    )

    print(
        "Exact Posts:",
        profile["posts_exact"]
    )

    print(
        "Bio:",
        profile["bio"]
    )

    print(
        "Reels scraped:",
        len(profile["reels"])
    )

    print(
        "\nSaved to:",
        filename
    )


finally:

    print("\nClosing browser...")

    driver.quit()

    print("Done.")