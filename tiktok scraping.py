import json
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


# ============================================================
# 1. GET USERNAME
# ============================================================

username = input("Enter TikTok username: ").strip()
username = username.lstrip("@")

profile_url = f"https://www.tiktok.com/@{username}"


# ============================================================
# 2. START CHROME
# ============================================================

options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)


try:

    # ========================================================
    # 3. OPEN TIKTOK
    # ========================================================

    print("\nOpening TikTok...")

    driver.get("https://www.tiktok.com/")

    time.sleep(5)

    print("TikTok opened.")


    # ========================================================
    # 4. LOAD COOKIES
    # ========================================================

    print("\nLoading cookies.json...")

    with open("cookies.json", "r", encoding="utf-8") as file:
        cookies = json.load(file)

    print("Cookies found:", len(cookies))


    # ========================================================
    # 5. ADD COOKIES
    # ========================================================

    added = 0
    failed = 0

    for cookie in cookies:

        try:

            new_cookie = {
                "name": cookie["name"],
                "value": cookie["value"],
                "path": cookie.get("path", "/"),
            }

            # Do not send the original domain.
            # We are already on TikTok.

            if "expiry" in cookie:
                new_cookie["expiry"] = int(cookie["expiry"])

            if "secure" in cookie:
                new_cookie["secure"] = cookie["secure"]

            if "httpOnly" in cookie:
                new_cookie["httpOnly"] = cookie["httpOnly"]

            if cookie.get("sameSite") in ["Strict", "Lax", "None"]:
                new_cookie["sameSite"] = cookie["sameSite"]

            driver.add_cookie(new_cookie)

            added += 1

            print("Added:", cookie["name"])

        except Exception as error:

            failed += 1

            print(
                "Failed:",
                cookie.get("name"),
                "|",
                error
            )


    print("\n================================")
    print("Cookies added :", added)
    print("Cookies failed:", failed)
    print("================================")


    # ========================================================
    # 6. REFRESH
    # ========================================================

    print("\nRefreshing TikTok...")

    driver.refresh()

    time.sleep(7)


    # ========================================================
    # 7. OPEN PROFILE
    # ========================================================

    print("\nOpening profile...")
    print("Profile URL:", profile_url)

    driver.get(profile_url)

    time.sleep(10)


    # ========================================================
    # 8. PAGE INFORMATION
    # ========================================================

    print("\n================================")
    print("PAGE INFORMATION")
    print("================================")

    print("Current URL:", driver.current_url)
    print("Title:", driver.title)


    # ========================================================
    # 9. GET LIVE HTML
    # ========================================================

    html = driver.page_source

    print("HTML length:", len(html))


    # ========================================================
    # 10. SAVE LIVE HTML
    # ========================================================

    with open(
        "tiktok_live.html",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    print("Live HTML saved to tiktok_live.html")


    # ========================================================
    # 11. BEAUTIFULSOUP
    # ========================================================

    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    # ========================================================
    # 12. DEFAULT DATA
    # ========================================================

    profile = {
        "nickname": None,
        "username": username,
        "followers": None,
        "following": None,
        "likes": None,
        "bio": None,
    }


    # ========================================================
    # 13. SEARCH SCRIPT TAGS
    # ========================================================

    scripts = soup.find_all("script")

    print("\nSearching TikTok page data...")

    for script in scripts:

        script_text = script.string

        if not script_text:
            continue


        # ----------------------------------------------------
        # nickname
        # ----------------------------------------------------

        if profile["nickname"] is None:

            match = re.search(
                r'"nickname"\s*:\s*"([^"]*)"',
                script_text
            )

            if match:
                profile["nickname"] = match.group(1)


        # ----------------------------------------------------
        # uniqueId / username
        # ----------------------------------------------------

        if profile["username"] == username:

            match = re.search(
                r'"uniqueId"\s*:\s*"([^"]*)"',
                script_text
            )

            if match:
                profile["username"] = match.group(1)


        # ----------------------------------------------------
        # followers
        # ----------------------------------------------------

        if profile["followers"] is None:

            match = re.search(
                r'"followerCount"\s*:\s*(\d+)',
                script_text
            )

            if match:
                profile["followers"] = match.group(1)


        # ----------------------------------------------------
        # following
        # ----------------------------------------------------

        if profile["following"] is None:

            match = re.search(
                r'"followingCount"\s*:\s*(\d+)',
                script_text
            )

            if match:
                profile["following"] = match.group(1)


        # ----------------------------------------------------
        # likes
        # ----------------------------------------------------

        if profile["likes"] is None:

            match = re.search(
                r'"heartCount"\s*:\s*(\d+)',
                script_text
            )

            if not match:

                match = re.search(
                    r'"heart"\s*:\s*(\d+)',
                    script_text
                )

            if match:
                profile["likes"] = match.group(1)


        # ----------------------------------------------------
        # bio
        # ----------------------------------------------------

        if profile["bio"] is None:

            match = re.search(
                r'"signature"\s*:\s*"([^"]*)"',
                script_text
            )

            if match:
                profile["bio"] = match.group(1)


    # ========================================================
    # 14. FALLBACK: META TITLE
    # ========================================================

    if profile["nickname"] is None:

        meta_title = soup.find(
            "meta",
            attrs={"property": "og:title"}
        )

        if meta_title:

            title = meta_title.get("content")

            if title:
                profile["nickname"] = title


    # ========================================================
    # 15. FALLBACK: DESCRIPTION
    # ========================================================

    if profile["bio"] is None:

        meta_description = soup.find(
            "meta",
            attrs={"name": "description"}
        )

        if meta_description:

            description = meta_description.get("content")

            if description:
                profile["bio"] = description


    # ========================================================
    # 16. CHECK TIKTOK ERROR
    # ========================================================

    page_text = soup.get_text(
        " ",
        strip=True
    )

    if "Something went wrong" in page_text:

        print("\nTikTok returned:")
        print("Something went wrong.")

        print(
            "\nThe browser reached TikTok, "
            "but TikTok did not return the profile data."
        )

    else:

        # ====================================================
        # 17. DISPLAY PROFILE
        # ====================================================

        print("\n")
        print("================================")
        print("       TIKTOK PROFILE")
        print("================================")

        print(
            "Name:",
            profile["nickname"]
            if profile["nickname"]
            else "Not found"
        )

        print(
            "Username:",
            "@" + profile["username"]
            if profile["username"]
            else "Not found"
        )

        print(
            "Following:",
            profile["following"]
            if profile["following"]
            else "Not found"
        )

        print(
            "Followers:",
            profile["followers"]
            if profile["followers"]
            else "Not found"
        )

        print(
            "Likes:",
            profile["likes"]
            if profile["likes"]
            else "Not found"
        )

        print(
            "Bio:",
            profile["bio"]
            if profile["bio"]
            else "Not found"
        )

        print("================================")


    # ========================================================
    # 18. KEEP CHROME OPEN
    # ========================================================

    input("\nPress ENTER to close Chrome...")


finally:

    driver.quit()