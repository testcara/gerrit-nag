#!/usr/bin/env python3

from typing import AnyStr, Iterable, List, TypeVar, Dict
import argparse
import requests
import json
from datetime import datetime

def prepare_gerrit_query(parser, user):
    return '+'.join([
        # Specify the project
        'project:{project}',

        # Exclude merged or abandoned patches
        'status:open',

        # Include patches you were invited to review
        'reviewer:{user}',

        # Don't need to review your own patches
        '-owner:{user}',

        # Exclude patch sets you already reviewed.
        # Gerrit considers that a comment counts as a review
        # but if the owner posts a comment later than yours then
        # you need to review it again.
        '-reviewedby:{user}',

        # Exclude patches where Jenkins tests failed
        # (An alternative here would be to use label:Verified+1
        # which would exclude patch sets where Jenkins didn't run yet)
        '-label:Verified-1',

        # Exclude patches where someone already gave a -2
        '-label:Code-Review-2',

        # Exclude patches where someone already gave a +2
        # since they're likely to be merged soon regardless
        '-label:Code-Review2',

    ]).format(project = parser.project, user = user)

def prepare_rest_url(parser, user):
    return "{gerrit}/changes/?q={query}&{options}".format(
        gerrit = parser.gerrit,
        query = prepare_gerrit_query(parser, user),
        options = 'o=DETAILED_LABELS&o=DETAILED_ACCOUNTS')

def prepare_clickable_url(parser, user):
    return "{gerrit}/#/q/{query}".format(
        gerrit = parser.gerrit,
        query = prepare_gerrit_query(parser, user))

def prepare_review_url(parser, change_number):
    return "{}/{}".format(parser.gerrit, change_number)

def query_gerrit(parser, user) -> bytes:
    """Return current outstanding gerrit changes owned by user"""
    response = requests.get(prepare_rest_url(parser, user))
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
    parser.add_argument('--short', action='store_true', help="Short output")
    parser.add_argument('--shorter', action='store_true', help="Even shorter output")
    parser.add_argument('--include-all', action='store_true', help="Don't exclude patch sets with two +1s or a +2")
    return parser.parse_args()

def get_user_list(users: str) -> List[str]:
    return sorted([u.strip() for u in users.split(',')])

def main():
    parser = get_opts()

    user_changes = {}
    waiting_count = 0
    waiting_sum = 0

    for user in get_user_list(parser.users):
        all_changes = query_gerrit(parser, user)
        if parser.include_all:
            user_changes[user] = all_changes
        else:
            user_changes[user] = [c for c in all_changes if not review_not_needed(c)]

    for user,changes in sorted(user_changes.items(), key=lambda t: -len(t[1])):
        waiting_count += 1
        waiting_sum += len(changes)

        if parser.shorter:
            print("{} reviews waiting on {}".format(len(changes), user))
            continue
        elif parser.short:
            print("{} reviews waiting on {} - {}".format(len(changes), user, prepare_clickable_url(parser, user)))
            continue
        else:
            print("{} reviews waiting on {}".format(len(changes), user))

        for change in changes:
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

            print(" - {}: {} {}".format(
                change['subject'],
                waiting_message,
                prepare_review_url(parser, change['_number'])))

    if parser.shorter:
        print("Team average: {:.1f}".format(waiting_sum / waiting_count))
        print(prepare_clickable_url(parser, 'self'))


if __name__ == '__main__':
    main()
