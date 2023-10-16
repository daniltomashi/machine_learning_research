from bs4 import BeautifulSoup
import requests
import pandas as pd
import os
import urllib
import re
from urllib.parse import urlparse, urljoin
import numpy as np



##############################      URL based features      ##############################
def is_ip_in_domain(url):
    # Regular expression to match both IPv4 and IPv6 addresses
    ip_pattern = r'(?:(?:\d{1,3}\.){3}\d{1,3})|(?:[0-9A-Fa-f:]+:[0-9A-Fa-f]*)'

    # Extract the domain from the URL
    domain_pattern = r'^(?:https?://)?([^/]+)'

    # Get the domain from the URL
    match = re.search(domain_pattern, url)
    if match:
        domain = match.group(1)

        # Check if the domain contains an IP address
        if re.search(ip_pattern, domain):
            return True

    return False

def is_url_shortened(url):
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url.replace('www.', ''), allow_redirects=False)

        # Check if the response has a 'Location' header, indicating a redirect
        if 'Location' in response.headers:
            final_url = response.headers['Location']

            # Compare the final URL with the original URL
            if final_url != url:
                return True

    except Exception as e:
        # Handle any exceptions that may occur during the request
        print(f"Error: {e}")

    return False
##############################      URL based features      ##############################


##############################      HYPERLINK based features      ##############################
def find_hyperlinks(tag, check=False):
    if check:
        print(tag)
        print(tag.has_attr('href') or tag.has_attr('src') or (tag.name == 'link' and tag.has_attr('href')))
        print('-'*100)
    return tag.has_attr('href') or tag.has_attr('src') or (tag.name == 'link' and tag.has_attr('href'))
    # I think link not that good, because it will also add scripts and css files
    # or (tag.name == 'link' and tag.has_attr('href'))

##############################      HYPERLINK based features      ##############################



if "benign.csv" not in os.listdir("../data/"):
    df_links = pd.DataFrame(columns=["link", "letters_nums_in_link", "domain_name", "count_subdomain", "ip_in_domain", 
                                     "dog_symbol", "url_length", "url_depth", "redirection", "http_https_domain", 
                                     "https_in_scheme", "url_shortening", "dash_in_domain", "sensetive_words", "brand_names", 
                                     "upper_case", "num_of_dots", "no_hyperlink", "internal_hyperlink_ratio", 
                                     "external_hyperlink_ratio", "external_css", "susp_form_link_action", 
                                     "anchor_null_links_answer", "exist_of_extern_favicon", "freq_of_most_anchor", 
                                     "footer_value", "sfh"])
    i = 0
else:
    df_links = pd.read_csv("../data/benign.csv")
    i = len(df_links)

links = [link[0].strip().replace('www.', '').replace('...', '.').replace('..', '.')
                for link in pd.read_csv("../data/Benign_list_big_final.csv").values]
np.random.shuffle(links)
# clear_domains = []
# new_links = []
# for link in links:
#     domain_name = link.split('//', 1)[-1]
#     clear_domain = domain_name.split('/')[0]

#     if clear_domain not in clear_domains:
#         clear_domains.append(clear_domain)
#         new_links.append(link)

# print(len(links))
# print(len(new_links))

for link in links:
    try:
        # if cannot reach website for 10 seconds, go to another website
        try:

            response = requests.get(link, timeout=10)
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.TooManyRedirects:
            continue
        except urllib.error.URLError as e:
            continue
        except urllib.error.HTTPError as e:
            continue

        status_code = response.status_code
        if status_code != 200:
            continue
    except requests.exceptions.ConnectionError:
        continue

    website_soup = BeautifulSoup(response.text, "html.parser")
    
    # retrieve URL based features
    domain_name = link.split('//', 1)[-1]
    clear_domain = domain_name.split('/')[0]

    letters_nums_in_link = ''.join(re.findall("[A-Za-z0-9]", clear_domain))

    # if letters_nums_in_link in df_links["letters_nums_in_link"].values:
    #     continue
    
    count_subdomain = sum([1 for x in domain_name.split('/')[0] if x == '.'])
    if count_subdomain > 3:
        count_subdomain = 1
    elif count_subdomain == 3:
        count_subdomain = 0.5
    else:
        count_subdomain = 0

    ip_in_domain = is_ip_in_domain(link)

    dog_symbol = True if "@" in link else False

    url_length = len(link)
    if url_length < 75:
        url_length = 0
    elif url_length >= 75 and url_length < 100:
        url_length = 0.5
    else:
        url_length = 1

    url_depths = sum([1 for char in domain_name if char == '/'])

    # NOTE: better to change logic. To go to this url and check if it changes
    redirection = True if "//" in domain_name else False

    http_https_domain = True if "http" in domain_name or "https" in domain_name else False

    https_in_scheme = True if "https" in link else False
    
    shortening_url = is_url_shortened(link)
    
    pre_suf_in_domain = True if '-' in clear_domain else False

    sens_words = ["login", "update", "validate", "activate", "secure", "account", "password",
                    "verification", "confirm", "recovery", "important", "alert", "urgent", 
                    "verify", "warning", "notification", "information", "billing"]
    exist_of_sens = True if [word for word in sens_words if word in link] != [] else False

    trendy_brandy_names = ["Apple", "Microsoft", "PayPal", "Amazon", "Google", "Facebook", 
                            "Netflix", "eBay", "Twitter", "LinkedIn", "Adobe", "Dropbox", 
                            "Yahoo", "Instagram", "WhatsApp", "Spotify", "Chase",
                            "Wells Fargo", "Citibank"]
    exist_of_tr_br_name = True if [word for word in trendy_brandy_names if 
                                    word.lower() in link] != [] else False
    
    find_uppercase = re.search("[A-Z]", link)
    if find_uppercase:
        exist_of_uppercase = True
    else:
        exist_of_uppercase = False

    dots_num = sum([1 for char in domain_name if char == '.'])
    if dots_num > 2:
        dots_num = 1
    else:
        dots_num = 0

    # retrieve hyperlink based features
    hyperlinks = website_soup.find_all(find_hyperlinks)
    if len(hyperlinks) > 0:
        no_hyperlink = False
    else:
        no_hyperlink = True

    # works not that good, because it could redirect to another website, and then every link
    # will be part of another bigger website
    if len(hyperlinks) > 0:
        total_internal = 0
        total_external = 0
        for hyperlink in hyperlinks:
            if hyperlink.get("href"):
                hyperlink = hyperlink.get("href")
            elif hyperlink.get("src"):
                hyperlink = hyperlink.get("src")
            elif hyperlink.get("link"):
                hyperlink = hyperlink.get("link")
            else:
                for tag in hyperlink.find_all():
                    if tag.get("href"):
                        hyperlink = tag.get("href")
                    if tag.get("src"):
                        hyperlink = tag.get("src")
                    if tag.get("link"):
                        hyperlink = tag.get("link")
            
            # count only if href, src or link not empty
            if type(hyperlink) == str:
                parsed_base_url = urlparse(link)
                parsed_link = urlparse(urljoin(link, hyperlink))
                if parsed_base_url.netloc == parsed_link.netloc:
                    total_internal += 1
                else:
                    total_external += 1

        internal_hyperlink_ratio = total_internal / len(hyperlinks)
        if internal_hyperlink_ratio > 0.5:
            internal_hyperlink_ratio = 0
        else:
            internal_hyperlink_ratio = 1
        
        external_hyperlink_ratio = total_external / len(hyperlinks)
        if external_hyperlink_ratio > 0.5:
            external_hyperlink_ratio = 1
        else:
            external_hyperlink_ratio = 0
    else:
        internal_hyperlink_ratio = 1
        external_hyperlink_ratio = 0


    if len(website_soup.find_all('link', rel='stylesheet', href=True)) > 0:
        external_css = True
    else:
        external_css = False
    
    forms = website_soup.find_all("form")
    form_with_actions = []
    for form in forms:
        action_of_form = form.get("action")
        if action_of_form:
            form_with_actions.append(action_of_form)
    
    susp_form_link_action = False
    suspicious_values = ["#", "javascript:void()", "null", "javascript:void(0)"]
    for action in form_with_actions:
        # NOTE: it should be or '.php' or files that contains '.php' in any place in the string
        if action in suspicious_values or action.endswith('.php'):
            susp_form_link_action = True
            break
        elif 'http' in action:
            if action.split('//', 1)[-1].split('/')[0].strip() != clear_domain:
                susp_form_link_action = True
                break
    
    anchor_null_links = 0
    anchor_with_links = website_soup.find_all("a", href=True)
    anch_links_freq = {anchor_link:0 for anchor_link in anchor_with_links}
    for anchor_link in anchor_with_links:
        anch_links_freq[anchor_link] += 1
        anchor_href = anchor_link.get("href")
        if anchor_href.startswith("#") or "javascript:;" in anchor_href or\
                "javascript:void(0)" in anchor_href or anchor_href == '':
            anchor_null_links += 1

    if len(anchor_with_links) != 0:
        if anchor_null_links / len(anchor_with_links) > 0.34:
            anchor_null_links_answer = True
        else:
            anchor_null_links_answer = False
    else:
        anchor_null_links_answer = False

    
    # ideally classifies by this thing
    favicon_links = [favicon_link.get("href") for favicon_link in\
                        website_soup.find_all('link', rel=['icon', 'shortcut icon'])]
    favicon_value = 0
    for favicon_link in favicon_links:
        base_domain = urlparse(link).netloc
        favicon_domain = urlparse(favicon_link).netloc
        if base_domain != favicon_domain:
            favicon_value += 1

    exist_of_extern_favicon = bool(favicon_value)
        
    
    if len(anchor_with_links) > 0:
        freq_of_most_anchor = max(anch_links_freq.values()) / len(anchor_with_links)
    else:
        freq_of_most_anchor = 0

    
    if website_soup.find('footer'):
        footer_links = website_soup.find('footer').find_all("a")
        footer_freq_links = {footer_link:0 for footer_link in footer_links}
        footer_value = 0.0
        if len(footer_links) > 0:
            for footer_link in footer_links:
                footer_freq_links[footer_link] += 1
            footer_value = max(footer_freq_links.values()) / len(footer_links)
    else:
        footer_value = 0.0


    sfh = 0
    for form in forms:
        form_action = form.get("action")
        if not form_action or form_action.strip() == "about:blank":
            sfh = 1
            break
        elif 'http' in form_action:
            if form_action.split('//', 1)[-1].split('/')[0].strip() != clear_domain:
                sfh = 0.5
                break
        else:
            sfh = 0
    


        # save to csv
        df_links.loc[i] = link, letters_nums_in_link, domain_name, count_subdomain, ip_in_domain, dog_symbol, url_length, url_depths, redirection,\
                            http_https_domain, https_in_scheme, shortening_url, pre_suf_in_domain, exist_of_sens,\
                            exist_of_tr_br_name, exist_of_uppercase, dots_num, no_hyperlink, internal_hyperlink_ratio,\
                            external_hyperlink_ratio, external_css, susp_form_link_action, anchor_null_links_answer,\
                            exist_of_extern_favicon, freq_of_most_anchor, footer_value, sfh
        i += 1

        df_links.to_csv("../data/benign.csv", index=False)