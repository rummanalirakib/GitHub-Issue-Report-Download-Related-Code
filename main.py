import requests
import json
import csv
import logging
import os
import time

# Create a custom logger
logging.basicConfig(filename='./config/project.log', encoding='utf-8',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("------------------------------------NEW RUN------------------------------------")

# ------------------------------------------------------------
# OS RELATED FUNCTIONS
# ------------------------------------------------------------
        
# Create a directory for each repository
def create_directory(github_username, github_repository, endpoint):
    directory_name = f"./config/data/{github_username}_{github_repository}/{endpoint}"
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
        logging.info(f"Created directory: '{directory_name}'")
    else:
        logging.info(f"Directory already exists: '{directory_name}'")

# ------------------------------------------------------------
# GITHUB INPUT FILE
# ------------------------------------------------------------
GITHUB_INPUT_URL ='./config/github_urls.csv'

# ------------------------------------------------------------
# GITHUB AUTHENTICATION
# ------------------------------------------------------------
# Credentials file where the GITHUB TOKEN is stored
CONFIG_FILE = "./config/credentials.json"  # this file has GITHUB TOKEN
with open(f'{CONFIG_FILE}', 'r') as json_file:
    json_auth_data = json.load(json_file)

GITHUB_API_TOKEN = json_auth_data["github_auth"]["Bearer"]

print(f"Token: {GITHUB_API_TOKEN}")
GITHUB_API_RATE_COUNTER = 0

# GITHUB HEADERS for the API request of authenticated user
GITHUB_HEADERS = {
    'Authorization': f'Bearer {GITHUB_API_TOKEN}',
}

# ------------------------------------------------------------
# GITHUB BASE URL
# ------------------------------------------------------------
GITHUB_BASE_URL = "https://api.github.com"

# ------------------------------------------------------------
# Check for valid GITHUB TOKEN
# ------------------------------------------------------------ 
def check_token_validity():
    response = requests.get('https://api.github.com/user', headers=GITHUB_HEADERS)
    if response.status_code == 200:
        user_info = response.json()
        logging.info(f"Authenticated user: {user_info.get('login')}")
        return True
    else:
        logging.warning("Token is invalid or unauthorized. Please check and try again.")
        return False
    
# ------------------------------------------------------------
# Get the github urls
# ------------------------------------------------------------
def get_github_urls(github_username, github_repository, endpoint, category):
    if category == "None":
        url = f"{GITHUB_BASE_URL}/repos/{github_username}/{github_repository}/{endpoint}?state=all&per_page=100"
    else:
        url = f"{GITHUB_BASE_URL}/repos/{github_username}/{github_repository}/{endpoint}/{category}?per_page=100"
    return url
    

# ------------------------------------------------------------
# Get the github api request
# ------------------------------------------------------------

MAX_RETRIES = 30
WAIT_TIME_SECONDS = 10
GITHUB_API_RATE_COUNTER = 0

def get_github_api_request(url):
    global GITHUB_API_RATE_COUNTER
    attempt = 0

    # used_limit = get_github_category_value('core', 'used')
    # core_limit = get_github_category_value('core', 'limit')
    reset_time = get_github_category_value('core', 'reset')
    remaining_limit = get_github_category_value('core', 'remaining')
    

    # response = None
    if remaining_limit <= 10:
        wait_time_limit = reset_time - time.time() + 50
        logging.info(f"Sleeping for {wait_time_limit} seconds")
        time.sleep(wait_time_limit)
    else:
        while attempt < MAX_RETRIES:
            try:
                remaining_limit = get_github_category_value('core', 'remaining')
                # if remaining_limit <= 10:
                response = requests.get(url, timeout=10, headers=GITHUB_HEADERS)
                logging.info(f"Status: {response.status_code} for {response.url}")

                if response.status_code == 200:
                    return response  # Successful response, exit the loop
            except requests.exceptions.ReadTimeout:
                print("ReadTimeout occurred. Retrying in {WAIT_TIME_SECONDS} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                logging.warning("ReadTimeout occurred. Retrying in {WAIT_TIME_SECONDS} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(WAIT_TIME_SECONDS)

            except requests.exceptions.ConnectTimeout as e:
                logging.warning(f"Connection timed out. Retrying in {WAIT_TIME_SECONDS} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                print(f"Connection timed out. Retrying in {WAIT_TIME_SECONDS} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(WAIT_TIME_SECONDS)
            except requests.exceptions.RequestException as e:
                print(f"Request failed. Retrying in {WAIT_TIME_SECONDS} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                logging.warning(f"Request failed. Retrying in {WAIT_TIME_SECONDS} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(WAIT_TIME_SECONDS)

            attempt += 1

            # If all retries fail, return the last response (which contains the error status)
        return response

# ------------------------------------------------------------
# GITHUB ENDPOINTS
# ------------------------------------------------------------
GITHUB_MAIN_ENDPOINTS = [
    "issues",
    "pulls", 
    "comments", 
    "commits", 
    "issues_comments",
    "issues_events",
    "pulls_comments"
]

# ------------------------------------------------------------
# Check the github endpoints
# ------------------------------------------------------------
def check_github_endpoints(endpoint):
    if endpoint == "issues_comments":
        return "issues", "comments"
    elif endpoint == "issues_events":
        return "issues", "events"
    elif endpoint == "pulls_comments":
        return "pulls", "comments"
    else:
        return endpoint, "None"

# ------------------------------------------------------------
# GITHUB RATE LIMIT
# ------------------------------------------------------------
def get_github_category_value(category, type):
    r = requests.get('https://api.github.com/rate_limit', headers=GITHUB_HEADERS)
    rjson = r.json()
    return rjson['resources'][category][type]
    

def get_rate_json_category_data(category="core"):
    """
    This function returns the json data for the rate limit
    """
    r = requests.get('https://api.github.com/rate_limit', headers=GITHUB_HEADERS)
    return r.json()['resources'][category]


# ------------------------------------------------------------

def get_verified_and_non_verified_lists():
    verified_list= []
    unverified_list = []
    with open(f'{GITHUB_INPUT_URL}', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        # skip the first row
        next(csv_reader)
        for row in csv_reader:
            for item in row:
                r = requests.get(item, GITHUB_HEADERS)
                # r = get_github_api_request(item)
                if r.status_code == 400:
                    logging.warning(f"INVALID URL: '{item}'")
                    continue
                else:
                    logging.info(f"VALID URL: '{item}'")

                    item = item.strip()
                    item = item.lower()
                    item = item.split("/") 

                    temp1 = []

                    if item[2] == "github.com":
                        temp1.append(item[3])
                        temp1.append(item[4])
                        verified_list.append(temp1)
    return verified_list, unverified_list

# ------------------------------------------------------------
# Get the last page number from the response

def get_last_page_num(response):
    print('response: ', response)
    link_header = response.headers.get("Link")
    print('link_header: ', link_header)
    if link_header:
        # Split the "Link" header into individual links
        links = link_header.split(',')
        print('links: ', links)
        for link in links:
            if 'rel="last"' in link:
              # Extract the page number from the link
              return int(link.split("page=")[-1].split(">")[0])
    return 1



def check_if_file_exists(github_username, github_repository, current_page, last_page_number, endpoint, category):
    if category == "None":
        for item in range(current_page, last_page_number + 1):
            if not os.path.exists(f"./config/data/{github_username}_{github_repository}/{endpoint}/{github_username}_{github_repository}_{endpoint}_page_{item}.json"):
                logging.info(f"The file does not exist: './config/data/{github_username}_{github_repository}/{endpoint}/{github_username}_{github_repository}_{endpoint}_page_{item}.json'")
                return item
    else:
        for item in range(current_page, last_page_number + 1):
            if not os.path.exists(f"./config/data/{github_username}_{github_repository}/{endpoint}_{category}/{github_username}_{github_repository}_{endpoint}_{category}_page_{item}.json"):
                logging.info(f"The file does not exist: './config/data/{github_username}_{github_repository}/{endpoint}_{category}/{github_username}_{github_repository}_{endpoint}_{category}_page_{item}.json'")
                return item
    return 0

        
# ------------------------------------------------------------
# Save the data to the file
# ------------------------------------------------------------

def save_json_data(data, location):
    try:
        new_data = json.loads(data)
    except json.JSONDecodeError:
        logging.warning(f"Error: Provided data is not valid JSON.")
        return 

    # Write the updated data back to the file
    with open(location, 'w') as file:
        json.dump(new_data, file, indent=4, sort_keys=True)
    return len(new_data)
# ------------------------------------------------------------
# -------------Get the verifiation values---------------------
# ------------------------------------------------------------
def get_verification_data_values(user_repo_key, endpoint, category, sub_category):
    print(f"Parameters: {user_repo_key}, {endpoint}, {category}, {sub_category}")
    # endpoint_last_page_number = get_last_page_num(r)
    with open(VERIFICATION_JSON, 'r') as json_file:
        existing_data = json.load(json_file)

        for key, value in existing_data.items():
            # print(f"key: {key}")
            if key == f"{user_repo_key}":
                for k, v in value.items():
                    if category == "None":
                        if k == f"{endpoint}":
                            # print(f"Value: {v}")
                            return v
                    elif category == "None" and sub_category != "None":
                        if k == f"{endpoint}_{sub_category}":
                            # print(f"Value: {v}")
                            return v
                    elif category != "None":
                        if k == f"{endpoint}_{category}":
                            # print(f"Value: {v}")
                            return v
                        
                    elif category != "None" and sub_category != "None":
                        if k == f"{endpoint}_{category}_{sub_category}":
                            return v
                        
# ------------------------------------------------------------
# ----------------VERIFICATION FILE---------------------------
# ------------------------------------------------------------
                
# check if the verifiation file exists
def check_if_verification_file_exists():
    if os.path.exists(VERIFICATION_JSON):
        return True
    else:
        return False
    
# update the verification file with nested_keys
def update_verification_file_with_default_values(github_username, github_repository, github_endpoint):
    with open(VERIFICATION_JSON, 'r') as json_file:
        # Load existing data from the file
        data_list = json.load(json_file)

    for github_endpoint in GITHUB_MAIN_ENDPOINTS:
        endpoint, category = check_github_endpoints(github_endpoint)

        if category == "None":
            data_list.setdefault(f"{github_username}_{github_repository}", {}).setdefault(f"{endpoint}", 0)
            data_list.setdefault(f"{github_username}_{github_repository}", {}).setdefault(f"{endpoint}_last_page_number", 0)
            data_list.setdefault(f"{github_username}_{github_repository}", {}).setdefault(f"{endpoint}_curr_page_number", 0)
   

        else:
            data_list.setdefault(f"{github_username}_{github_repository}", {}).setdefault(f"{endpoint}_{category}", 0)
            data_list.setdefault(f"{github_username}_{github_repository}", {}).setdefault(f"{endpoint}_{category}_last_page_number", 0)
            data_list.setdefault(f"{github_username}_{github_repository}", {}).setdefault(f"{endpoint}_{category}_curr_page_number", 0)

    with open(VERIFICATION_JSON, 'w') as json_file:
        json.dump(data_list, json_file, indent=4)

def update_verification_data(user_repo_key, temp_endpoint, temp_category, current_page, last_page_number, number_of_items_per_page):
    # Load existing data from the file
    try:
        with open(VERIFICATION_JSON, 'r') as json_file:
            verification_data = json.load(json_file)
    except FileNotFoundError:
        # If the file doesn't exist, initialize verification_data as an empty dictionary
        verification_data = {}         

    if number_of_items_per_page is None:
        number_of_items_per_page = 0        

    if category != "None":
        verification_data[user_repo_key][f"{temp_endpoint}_{temp_category}"] += number_of_items_per_page
        verification_data[user_repo_key][f"{temp_endpoint}_{temp_category}_last_page_number"] = last_page_number
        verification_data[user_repo_key][f"{temp_endpoint}_{temp_category}_curr_page_number"] = current_page
    else:
        verification_data[user_repo_key][temp_endpoint] += number_of_items_per_page
        verification_data[user_repo_key][f"{temp_endpoint}_last_page_number"] = last_page_number
        verification_data[user_repo_key][f"{temp_endpoint}_curr_page_number"] = current_page

    with open(VERIFICATION_JSON, 'w') as json_file:
        json.dump(verification_data, json_file, indent=4)
        

def get_issue_events(api_url):
    while check_rate_limit() < 1:
        time.sleep(10)
        
    response = requests.get(api_url, headers=GITHUB_HEADERS, timeout=30)

    if response.status_code == 200:
        try:
            data = response.json()
            return data
        except json.JSONDecodeError:
            print("Error decoding JSON in response:", response.text)
            return None
        
def check_rate_limit():
    url = 'https://api.github.com/rate_limit'
    
    try:
        response = requests.get(url, headers=GITHUB_HEADERS)
        response.raise_for_status()  # Raise an exception for HTTP errors
        rate_limit_info = response.json()
        
        if rate_limit_info:
            core_remaining = rate_limit_info['resources']['core']['remaining']
            return core_remaining
        
        return 0
    except requests.exceptions.RequestException as e:
        print(f"Error checking rate limit: {e}")
        return 0
        
        
def getCommentsByUrl(comments_url, comment_params=None):
    print('Fetching comments from URL:', comments_url)
    comments = get_issue_events(comments_url)
    return comments   

def getIssueEventsByUrl(issue_events_url, issue_url, issue_events_params=None):
    print('Fetching issue events from URL:', issue_events_url)
    
    # Fetch the issue events
    issue_events = get_issue_events(issue_events_url)
    
    # Update the 'url' key in each event with the provided issue_events_url
    for event in issue_events:
        if 'url' in event:
            event['url'] = issue_url
    
    return issue_events  
        

def getReqInfoPerIssue(comments_url, issue_events_url):
    
    full_comments = getCommentsByUrl(comments_url)
    issue_events = getIssueEventsByUrl(issue_events_url, issue_events_url.replace('/events', ''))
    
    return full_comments, issue_events

# ------------------------------------------------------------
# Check whether Data has Downloaded
# ------------------------------------------------------------

# check if the data is already downloaded
def is_data_downloaded(github_username, github_repository, endpoint, category):
    url = get_github_urls(github_username, github_repository, endpoint, category)
    r = get_github_api_request(url)
  
    endpoint_last_page_number = get_last_page_num(r)
    with open(VERIFICATION_JSON, 'r') as json_file:
        # Load existing data from the file
        existing_data = json.load(json_file)

        for key, value in existing_data.items():
            if key == f"{github_username}_{github_repository}":
                for k, v in value.items():
                    if category == "None":
                        if k == f"{endpoint}_curr_page_number":
                            if v < endpoint_last_page_number:
                                logging.info(f"{endpoint}_curr_page_number ({v}) != {endpoint}_last_page_number ({endpoint_last_page_number})for {github_username}_{github_repository}")
                                return False
                            else:
                                logging.info(f"{endpoint}_curr_page_number ({v}) == {endpoint}_last_page_number ({endpoint_last_page_number})for {github_username}_{github_repository}")
                                return True

                    elif category != "None":
                        if k == f"{endpoint}_{category}_curr_page_number":
                            if v < endpoint_last_page_number:
                                logging.info(f"{endpoint}_{category}_curr_page_number ({v}) != {endpoint}_{category}_last_page_number ({endpoint_last_page_number})for {github_username}_{github_repository}")
                                return False
                            else:
                                logging.info(f"{endpoint}_{category}_curr_page_number ({v}) == {endpoint}_{category}_last_page_number ({endpoint_last_page_number})for {github_username}_{github_repository}")

    if check_if_file_exists(github_username, github_repository, 1, endpoint_last_page_number, endpoint, category) == 0:
        logging.info("Exiting 'is_data_downloaded'")
        return True
def save_issue_related_json_data(data, location):
    with open(location, 'w') as json_file:
        json.dump(data, json_file, indent=4)
        
# ----------------------------------------------------------------------------
# ------------------------------------MAIN------------------------------------
# ----------------------------------------------------------------------------
# check if the token is valid
if not check_token_validity():
    print("Please check the token and try again.")

logging.info(get_rate_json_category_data())


# Verification file to keep track of the data downloaded
# trackign with last page number and current page number
VERIFICATION_JSON = "./verification.json"
verification_data = {}

# Create a verification file if it doesn't exist
if not check_if_verification_file_exists():
    with open(VERIFICATION_JSON, 'w') as file:
        json.dump(verification_data, file, indent=4, sort_keys=True)
    logging.info(f"Created file: '{VERIFICATION_JSON}'")

# Load existing data from the file
with open(VERIFICATION_JSON, 'r') as json_file:
    # Load existing data from the file
    existing_data = json.load(json_file)
    existing_data_keys = existing_data.keys()

# Verify the GITHUB URLS and put them in the VERIFICATION FILE
exported_list = get_verified_and_non_verified_lists()
verified_list = exported_list[0]
unverified_list = exported_list[1] # not using this list for now

for user,repo in verified_list:
    for github_endpoint in GITHUB_MAIN_ENDPOINTS:
        create_directory(user, repo, github_endpoint)
        endpoint, category = check_github_endpoints(github_endpoint)
        update_verification_file_with_default_values(user, repo, github_endpoint)

    if f"{user}_{repo}" in existing_data_keys:
        logging.info(f"'{user}_{repo}' already exists in VERIFICATION FILE")
    else:
        logging.info(f"Added '{user}_{repo}' to VERIFICATION FILE")

# list of all the keys in the VERIFICATION FILE
with open(VERIFICATION_JSON, 'r') as json_file:
    # Load existing data from the file
    existing_data = json.load(json_file)
verification_data_keys = {}
for key, value in existing_data.items():
    for k, v in value.items():
        verification_data_keys[k] = v

number_of_items_per_page = 0
# check whether the verified REPO is already in the VERIFICATION FILE
for user, repo in verified_list:
    for github_endpoint in GITHUB_MAIN_ENDPOINTS:
        if github_endpoint == "issues_comments" or github_endpoint == "issues_events":
            continue
        endpoint, category = check_github_endpoints(github_endpoint)
        if is_data_downloaded(user, repo, endpoint, category):
            if category == "None":
                logging.info(f"All '\{endpoint}' are already downloaded for {user}_{repo}")
                continue
            else:
                logging.info(f"All '\{endpoint}\{category}' are already downloaded for {user}_{repo}")
                continue
        else:
            url = get_github_urls(user, repo, endpoint, category)
            r = get_github_api_request(url)
            last_page_number = get_last_page_num(r)

            # There must be some files missing
            # Start downloading data from the page_not_found upto last_page_number
            page_not_found = check_if_file_exists(user, repo, 1, last_page_number, endpoint, category)
            for current_page in range(page_not_found, last_page_number+1):
                url_by_page = url + f"&page={current_page}"
                r = get_github_api_request(url_by_page)
        
                if r is not None:
                    data = r.text
                else:
                    continue

                location = " "

                if category != "None":
                    location = f"./config/data/{user}_{repo}/{endpoint}_{category}/{user}_{repo}_{endpoint}_{category}_page_{current_page}.json"
                else:
                    location = f"./config/data/{user}_{repo}/{endpoint}/{user}_{repo}_{endpoint}_page_{current_page}.json"
                
                number_of_items_per_page = save_json_data(data, location)
                
                if endpoint == 'issues':
                    issues_in_page = json.loads(data)
                    full_comments = []
                    full_issue_events = []
                    for each_issue in issues_in_page:
                        # Check if each_issue is a string and try to convert it to a dictionary
                        comments_url = each_issue.get('comments_url', None)
                        events_url = each_issue.get('events_url', None)
                        
                        # Only call getReqInfoPerIssue if both URLs are present
                        if comments_url is not None and events_url is not None:
                            comments, issue_events = getReqInfoPerIssue(comments_url, events_url)
                            full_comments.extend(comments)
                            full_issue_events.extend(issue_events)
                        
                    location = f"./config/data/{user}_{repo}/{endpoint}_comments/{user}_{repo}_{endpoint}_comments_page_{current_page}.json"
                    save_issue_related_json_data(full_comments, location)
                    location = f"./config/data/{user}_{repo}/{endpoint}_events/{user}_{repo}_{endpoint}_events_page_{current_page}.json"
                    save_issue_related_json_data(full_issue_events, location)
                    
                logging.info(f"Saved '{number_of_items_per_page}' items to '{location}'")
                update_verification_data(f"{user}_{repo}", endpoint, category, current_page, last_page_number, number_of_items_per_page)
                print(current_page, last_page_number, number_of_items_per_page)

print("DONE")
logging.info("------------------------------------END------------------------------------")