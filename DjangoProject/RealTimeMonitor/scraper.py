import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

def getSoup(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    else:
        print(f"Failed to fetch {url}, Status Code: {response.status_code}")
        return None

def extractData(MASTER_PAGE_URL):
    soup = getSoup(MASTER_PAGE_URL)
    if not soup:
        return []

    data = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) == 4:
            route = cells[0].get_text(strip=True)
            county = cells[1].get_text(strip=True)
            nearbyPlace = cells[2].get_text(strip=True)
            a_tag = cells[3].find("a")
            if a_tag:
                streamSource = urljoin(MASTER_PAGE_URL, a_tag["href"])
                streamSourceName = a_tag.get_text(strip=True)
                data.append({
                    "route": route,
                    "county": county,
                    "nearbyPlace": nearbyPlace,
                    "streamSource": streamSource,
                    "streamSourceName": streamSourceName
                })

    # Remove duplicates based on streamSource
    unique_data = []
    seen_streamSources = set()  # Track seen streamSource values
    for item in data:
        if item["streamSource"] not in seen_streamSources:
            unique_data.append(item)
            seen_streamSources.add(item["streamSource"])

    return unique_data