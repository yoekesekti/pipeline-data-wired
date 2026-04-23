import json
import re
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGET_COUNT = 50
OUTPUT_FILE = "data/wired_articles.json"

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

def wait_page_ready(driver, timeout=20):
    wait = WebDriverWait(driver, timeout)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def extract_title(driver):
    try:
        h1 = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        return clean_text(h1.text)
    except Exception:
        return ""

def extract_description(driver):
    try:
        meta_desc = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
        content = meta_desc.get_attribute("content")
        if content and len(content) > 20:
            return clean_text(content)
    except Exception:
        pass

    try:
        og_desc = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
        content = og_desc.get_attribute("content")
        if content and len(content) > 20:
            return clean_text(content)
    except Exception:
        pass

    return ""

def extract_authors(driver):
    authors = []
    byline_text = ""

    selectors = [
        '[data-testid="BylineWrapper"]',
        '.byline',
        '.article-header__byline',
        'header .byline',
        '.meta__byline',
        '.authors'
    ]
    
    for selector in selectors:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            byline_text = elem.text
            if byline_text:
                break
        except:
            pass

    if not byline_text:
        try:
            address_elem = driver.find_element(By.CSS_SELECTOR, 'address')
            byline_text = address_elem.text
        except:
            pass

    if byline_text:
        byline_text = re.sub(r'^By\s+', '', byline_text, flags=re.IGNORECASE)
        byline_text = re.sub(r'\s+•\s+.+$', '', byline_text)
        
        if '\n' in byline_text:
            raw_names = byline_text.split('\n')
        else:
            raw_names = re.split(r',|\sand\s', byline_text)
        
        for name in raw_names:
            name = clean_text(name)
            if name and len(name) >= 2 and len(name) <= 50:
                if re.match(r'^[A-Za-zÀ-ÿ\s\.\'\-]+$', name):
                    if name.lower() not in ['photo', 'illustration', 'video', 'wired', 'staff', 'editor', 'photograph', 'getty', 'images', 'by']:
                        authors.append(f"By{name}")
        
        if authors:
            return authors[:4]

    if not authors:
        try:
            meta_author = driver.find_element(By.CSS_SELECTOR, 'meta[name="author"]')
            author_name = meta_author.get_attribute("content")
            if author_name:
                author_name = re.sub(r'^By\s+', '', author_name, flags=re.IGNORECASE)
                author_name = author_name.split(',')[0].strip()
                if author_name and len(author_name) >= 2:
                    return [f"By{author_name}"]
        except:
            pass

    if not authors:
        try:
            scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            for script in scripts:
                try:
                    data = json.loads(script.get_attribute('innerHTML'))
                    if isinstance(data, dict) and 'author' in data:
                        author_data = data['author']
                        if isinstance(author_data, dict) and 'name' in author_data:
                            name = author_data['name'].split(',')[0].strip()
                            return [f"By{name}"]
                        elif isinstance(author_data, list):
                            authors_list = []
                            for a in author_data[:4]:
                                if isinstance(a, dict) and 'name' in a:
                                    name = a['name'].split(',')[0].strip()
                                    authors_list.append(f"By{name}")
                            if authors_list:
                                return authors_list
                except:
                    continue
        except:
            pass

    return ["ByUnknown"]

def scrape_via_api():
    print("Mencoba scraping via API Wired...")
    base_url = "https://www.wired.com/wp-json/wp/v2/posts"
    all_articles = []
    page = 1

    while len(all_articles) < TARGET_COUNT and page <= 10:
        params = {
            'per_page': 20,
            'page': page,
            '_embed': True,
            'status': 'publish'
        }

        try:
            response = requests.get(base_url, params=params, timeout=30)
            if response.status_code != 200:
                break

            posts = response.json()

            for post in posts:
                authors = []
                if '_embedded' in post and 'author' in post['_embedded']:
                    for author in post['_embedded']['author']:
                        author_name = author.get('name', '')
                        if author_name:
                            author_name = re.sub(r'^By\s+', '', author_name, flags=re.IGNORECASE)
                            author_name = author_name.split(',')[0].strip()
                            if author_name and len(author_name) >= 2:
                                authors.append(f"By{author_name}")
                        if len(authors) >= 4:
                            break

                description = post.get('excerpt', {}).get('rendered', '')
                description = re.sub(r'<[^>]+>', '', description)
                description = clean_text(description)

                title = clean_text(post.get('title', {}).get('rendered', ''))
                url = post.get('link', '')

                if title and url:
                    article = {
                        "title": title,
                        "url": url,
                        "description": description if description else "",
                        "author": authors if authors else ["ByUnknown"],
                        "scraped_at": datetime.now().isoformat()
                    }
                    all_articles.append(article)
                    print(f"[{len(all_articles)}] API - {title[:50]}...")

                if len(all_articles) >= TARGET_COUNT:
                    break

            page += 1
            time.sleep(1)

        except Exception as e:
            print(f"API error: {e}")
            break

    return all_articles

def scrape_with_selenium():
    print("Mencoba scraping via Selenium...")
    driver = setup_driver()

    SECTION_URLS = [
        "https://www.wired.com/",
        "https://www.wired.com/category/security/",
        "https://www.wired.com/category/politics/",
        "https://www.wired.com/category/business/",
        "https://www.wired.com/category/science/",
        "https://www.wired.com/category/culture/",
    ]

    try:
        all_urls = []
        seen_urls = set()

        for section in SECTION_URLS:
            try:
                print(f"\nMembuka section: {section}")
                driver.get(section)
                wait_page_ready(driver)
                time.sleep(2)
                
                for scroll in range(10):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                
                links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/story/']")
                
                for link in links:
                    href = link.get_attribute("href")
                    if href and "wired.com/story/" in href:
                        href = href.split("?")[0].rstrip("/") + "/"
                        if href not in seen_urls:
                            seen_urls.add(href)
                            all_urls.append(href)
                    
                    if len(all_urls) >= TARGET_COUNT:
                        break
                
                if len(all_urls) >= TARGET_COUNT:
                    break
                    
            except Exception as e:
                print(f"Gagal ambil link dari {section}: {e}")

        print(f"\nTotal URL artikel terkumpul: {len(all_urls)}")

        results = []
        for i, url in enumerate(all_urls[:TARGET_COUNT], start=1):
            try:
                print(f"Mengambil [{i}]: {url[:80]}...")
                driver.get(url)
                wait_page_ready(driver)
                time.sleep(2)
                
                title = extract_title(driver)
                description = extract_description(driver)
                authors = extract_authors(driver)
                
                if title:
                    results.append({
                        "title": title,
                        "url": url,
                        "description": description,
                        "author": authors,
                        "scraped_at": datetime.now().isoformat()
                    })
                    print(f"  OK - {title[:50]}...")
                else:
                    print(f"  SKIP - no title")
                    
            except Exception as e:
                print(f"  ERROR - {e}")

        return results

    finally:
        driver.quit()
        print("Browser ditutup.")

def scrape_wired():
    print("=" * 50)
    print("Memulai Scraping Wired.com")
    print("Target: 50 artikel")
    print("=" * 50)

    api_results = scrape_via_api()

    if len(api_results) >= TARGET_COUNT:
        final_articles = api_results[:TARGET_COUNT]
        print(f"\nBerhasil mengambil {len(final_articles)} artikel via API")
    else:
        print(f"API hanya mendapat {len(api_results)} artikel, melanjutkan dengan Selenium...")
        selenium_results = scrape_with_selenium()
        
        combined = api_results + selenium_results
        seen_urls = set()
        final_articles = []
        
        for article in combined:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                final_articles.append(article)
            if len(final_articles) >= TARGET_COUNT:
                break
        
        print(f"\nTotal gabungan: {len(final_articles)} artikel")

    final_output = [{
        "session_id": f"wired_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "articles_count": len(final_articles),
        "articles": final_articles
    }]

    import os
    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"\nScraping selesai. Total artikel tersimpan: {len(final_articles)}")
    print(f"Output tersimpan di: {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_wired()