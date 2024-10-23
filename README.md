#GitHub Issue Report Downloader
This project allows you to download issue reports from specified GitHub repositories. Follow the instructions below to set up and run the script.

#Getting Started
1. Configuration
Before running the main script, you need to configure a few files.

a. GitHub Token
Navigate to the config folder.

#Open credentials.json.

Locate the Bearer field and insert your GitHub personal access token.

json
Copy code
{
    "Bearer": "YOUR_GITHUB_TOKEN"
}
b. Repository URLs

#Open the github_urls file.

Below the existing column header, add the URLs of the GitHub repositories from which you want to download issue reports. Ensure that you do not change the column name.

Example:

ruby
Copy code
repository_url
https://github.com/user/repo1
https://github.com/user/repo2
2. Output Directory
All downloaded files will be stored in the data folder, which is located inside the config folder.

3. Download Verification
The verification.json file is used to track the download progress. If your download process is interrupted (e.g., due to a network issue), the next time you run the script, it will resume from where it left off. It will not re-download any information that has already been successfully downloaded.

If you wish to re-download specific information, simply delete the relevant entries in verification.json to reset the download status for those repositories.

#Running the Script
To run the downloader, execute the following command:

bash
Copy code
python main.py
Note
Make sure you have all dependencies installed, and your environment is correctly set up.

Conclusion
This project is designed to facilitate the downloading of issue reports from multiple GitHub repositories easily. If you have any questions or issues, please feel free to reach out!
