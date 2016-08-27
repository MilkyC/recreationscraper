"""Parse recreation.gov to find available sites at specified campground."""

import argparse
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import smtplib

DATE_FORMAT ='%m/%d/%Y' 
PARK_IDS = {
    'north pines': '70927',
    'lower pines': '70928',
    'upper pines': '70925'
}

MATRIX_URL = 'http://www.recreation.gov/campsiteCalendar.do?page=matrix&calarvdate={}&contractCode=NRSO&parkId={}'

# Email Information
MESSAGES_URL = ''
API_KEY = ''
FROM_EMAIL = ''
TO_EMAIL = ''


def build_body(args, row_matches):
    """Build the body of an email."""
    body = 'The following Dates are available at {} campground\n'.format(
            args.campground)
    for match in row_matches:
        row = match['row']
        matches = match['matches']
        for day, date in matches.iteritems():
            body_row = (
                    row['Site#'].replace('Map', '').strip('\n')
                    + ': '+ date.strftime(DATE_FORMAT) + '\n')
            body = body + body_row
    return body


def send_email(body):
    """Send an email."""
    return requests.post(
        MESSAGES_URL,
        auth=('api', API_KEY),
        data={'from': FROM_EMAIL,
              'to': [TO_EMAIL],
              'subject': 'Campground matches found',
              'text': body})   


def mkdate(datestr):
    """Takes a date in string format and returns a datetime."""
    return datetime.strptime(datestr, DATE_FORMAT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--week',
        '-w',
        required=True,
        type=mkdate,
        help='week to search.')

    parser.add_argument(
        '--date',
        '-d',
        default=[],
        type=mkdate,
        action='append',
        help='Date to search availability.')

    parser.add_argument(
        '--campground',
        '-c',
        required=True,
        help='campground to choose from: [{}]'.format(
            ', '.join(PARK_IDS.keys())))

    args = parser.parse_args()
    if args.campground not in PARK_IDS:
        print 'Invalid Campgrond'
        return

    days = {}
    for date in args.date:
         days[date.strftime('%d').lstrip('0')] = date

    session = requests.Session()
    url = MATRIX_URL.format(
            args.week.strftime(DATE_FORMAT), PARK_IDS[args.campground])
    print 'Checking url: {}'.format(url)
    r = session.get(url)
    c = r.content

    soup = BeautifulSoup(c)
    # Parse the calendar table.
    table = soup.find('table', attrs={'name':'calendar'})

    # Parse the calendar table head
    table_header = table.find('thead')
    table_header_row = table_header.find_all('tr')[3]
    header_elements = table_header_row.find_all('th')
    headers = []
    for header_element in header_elements:
        headers.append(header_element.text.strip().split('\n')[0])

    # Parse the calendar table body
    table_body = table.find('tbody')
    data = []
    rows = table_body.find_all('tr')
    for index, row in enumerate(rows):
        cols = row.find_all('td')
        if len(cols) != len(headers):
            continue
        cols = [ele.text.strip() for ele in cols]
        data_dict = dict(zip(headers, cols))
        data.append(data_dict)
    
    # Check if a campsite is available 
    row_matches = []
    for row in data:
        row_match = {}
        for day, date in days.iteritems():
            if day in row and row[day] == u'A':
                row_match[day] = date 
        if len(row_match):
            row_matches.append({'row':row, 'matches': row_match})
    print row_matches
    #print build_body(args, row_matches)
    if row_matches:
        email_sent = send_email(build_body(args, row_matches))
        print email_sent

if __name__ == "__main__":
    main()
