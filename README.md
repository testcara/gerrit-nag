# Gerrit Nag Bot

A python script that queries Gerrit and shows a list of how many patch sets
are waiting on reviews by each team member. If slow code reviews are a
bottle-neck in your team, this list can help remind and encourage developers
to do their reviews.

You can share the output via email or IRC. The intention is for it to become
an IRC bot, but this has not yet been implemented.

Based on an original script created by [@rohanpm](https://github.com/rohanpm).

## Usage

````
usage: gerrit-nag.py [-h] [--short] [--shorter] [--include-all]
                     URL PROJECT users

positional arguments:
  URL            Gerrit URL
  PROJECT        Gerrit project name
  users          List of users to query, comma separated

optional arguments:
  -h, --help     show this help message and exit
  --short        Short output
  --shorter      Even shorter output
  --include-all  Don't exclude patch sets with two +1s or a +2
````

## Example output

````
$ ./gerrit-nag.py https://gerrit.example.com/ my-project sbaird,rjoost
2 reviews waiting on sbaird
 - Fix some bug: (Waiting at least 4 days) https://gerrit.example.com/12345
 - Implement some feature: (Last updated at least 2 days ago) https://gerrit.example.com/12346
1 reviews waiting on rjoost
 - Fix some bug: (Waiting at least 4 days) https://gerrit.example.com/12345

$ ./gerrit-nag.py https://gerrit.example.com/ my-project sbaird,rjoost --short
2 reviews waiting on sbaird - https://gerrit.example.com/#/q/project:my-project+status:open+reviewer:sbaird+-owner:sbaird+-reviewedby:sbaird+-label:Verified-1+-label:Code-Review-2+-label:Code-Review2
1 reviews waiting on rjoost - https://gerrit.example.com/#/q/project:my-project+status:open+reviewer:rjoost+-owner:rjoost+-reviewedby:rjoost+-label:Verified-1+-label:Code-Review-2+-label:Code-Review2

$ ./gerrit-nag.py https://gerrit.example.com/ my-project sbaird,rjoost --shorter
2 reviews waiting on sbaird
1 reviews waiting on rjoost
Team average: 1.5
https://gerrit.example.com/#/q/project:my-project+status:open+reviewer:self+-owner:self+-reviewedby:self+-label:Verified-1+-label:Code-Review-2+-label:Code-Review2
````
