#!/usr/bin/env python3

from typing import AnyStr, Iterable, List, TypeVar, Dict
import argparse
import requests
import json
from datetime import datetime

GERRIT_URL = '%schanges/?q=%s&o=DETAILED_LABELS&o=DETAILED_ACCOUNTS'
QUERY = 'reviewer:%s+status:open+-owner:%s+-reviewedby:%s'

def query_gerrit(gerrit_url: str, project: str, user: str) -> bytes:
    """Return current outstanding gerrit changes owned by user"""
    query = QUERY % (user, user, user)
    if project:
        query = ("project:%s+" % (project)) + query

    gerrit_url = GERRIT_URL % (gerrit_url, query)
    response = requests.get(gerrit_url)
    return json.loads(response.text.lstrip(")]}'"))

def get_reviews(change):
    return change['labels']['Code-Review']['all']

def review_not_needed(change: Dict[str, int]) -> int:
    """Returns true if processing of a change should be skipped, (e.g. because it
    already has +2 or 2 * +1)."""
    # Consider skipping if patch owner has -1 or -2 on it
    rs = get_reviews(change)
    accum = 0
    for r in rs:
        if r['value'] < 0:
            return False
        accum = accum + r['value']
    # we let 2*+1 == +2
    return accum > 1

def get_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('gerrit', metavar='URL', type=str, help='Gerrit URL')
    parser.add_argument('project', metavar='PROJECT', help='Gerrit project name')
    parser.add_argument('users', type=str, help='List of users to query, comma separated')
    return parser.parse_args()

def get_user_list(users: str) -> List[str]:
    return sorted([u.strip() for u in users.split(',')])

def main():
    parser = get_opts()

    for user in get_user_list(parser.users):
        print("Reviews waiting on %s" % user)
        changes = query_gerrit(parser.gerrit, parser.project, user)

        for change in [c for c in changes if not review_not_needed(c)]:
            user_invite = [invite for invite in get_reviews(change) if invite['username'] == user][0]

            # Not sure why, but sometimes the review has date field present and sometimes there isn't.
            if 'date' in user_invite:
                # We can show how long ago the user was invited to review
                invited_date = user_invite['date']
                date = datetime.strptime(invited_date, '%Y-%m-%d %H:%M:%S.000000000')
                delta = datetime.utcnow() - date
                if delta.days > 0:
                    waiting_message = "(Waiting at least %d days)" % (delta.days)
                else:
                    waiting_message = "(Waiting at least %d hours)" % (delta.seconds / 3600)
            else:
                # Instead show how recent patch was updated
                date = datetime.strptime(change['updated'], '%Y-%m-%d %H:%M:%S.000000000')
                delta = datetime.utcnow() - date
                if delta.days > 0:
                    waiting_message = "(Last updated at least %d days ago)" % (delta.days)
                else:
                    waiting_message = "(Last updated at least %d hours ago)" % (delta.seconds / 3600)

            print(" - {}: {} {} {}".format(
                change['subject'],
                waiting_message,
                change['_number'],
                parser.gerrit))

if __name__ == '__main__':
    main()
