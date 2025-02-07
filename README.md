# LinkedIn Profile Scraper

An automated tool for ethically scraping LinkedIn profiles using Playwright. This tool provides a robust and maintainable way to collect public LinkedIn profile information for data analysis and research purposes.

## Features

- **Automated Login**: Secure LinkedIn authentication using environment variables
- **Smooth Scrolling**: Implements natural scrolling behavior to avoid detection
- **Profile Data Extraction**: Collects key information including:
  - Profile name
  - About section
  - Location
  - Profile URL
- **Data Storage**: Structured data storage using Pydantic models
- **Error Handling**: Robust error handling and logging system

## Project Structure

- `tool.py`: Main scraper implementation containing the `LinkedInTool` class
- `models.py`: Pydantic models for data validation and storage
- `.env`: Configuration file for environment variables

## Prerequisites

- Python 3.7+
- Playwright
- A LinkedIn account

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd linkedin1
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

3. Install required packages:
```bash
pip install playwright
pip install python-dotenv
pip install pydantic
pip install pandas
playwright install
```

## Configuration

Create a `.env` file in the project root with your LinkedIn credentials:
```
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

⚠️ **Security Note**: Never commit your `.env` file to version control.

## Usage

Run the scraper:
```bash
python tool.py
```

## Features in Detail

### LinkedInTool Class
- Handles browser automation using Playwright
- Implements smooth scrolling for natural behavior
- Manages LinkedIn authentication
- Extracts profile information using structured selectors

### Data Models
- Uses Pydantic for data validation
- Structured profile data storage
- Type hints for better code maintainability

## Best Practices

- Respect LinkedIn's terms of service and rate limits
- Use appropriate delays between requests
- Handle your credentials securely
- Follow ethical scraping guidelines

## Error Handling

The tool includes comprehensive error handling for:
- Authentication failures
- Network issues
- Page loading problems
- Data extraction errors

## Logging

Includes detailed logging for:
- Script execution progress
- Error tracking
- Debug information

## License

This project is licensed under the MIT License.

## Disclaimer

This tool is for educational purposes only. Users are responsible for ensuring their use of this tool complies with LinkedIn's terms of service and applicable laws.
