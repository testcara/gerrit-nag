This project consists of two components, __[Gerrit Nag](#gerrit-nag)__ and
__[Nagbot](#nagbot)__.

# Gerrit Nag

A Python 3 script that queries Gerrit and shows a list of how many patch sets
are waiting on reviews by each team member. If slow code reviews are a
bottle-neck in your team, this list can help remind and encourage developers
to do their reviews.

The output is plain text which you can share via email or IRC.


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

$ ./gerrit-nag.py https://gerrit.example.com/ my-project sbaird,rjoost --shortest
Team average: 1.5
https://gerrit.example.com/#/q/project:my-project+status:open+reviewer:self+-owner:self+-reviewedby:self+-label:Verified-1+-label:Code-Review-2+-label:Code-Review2
````

# Nagbot

Nagbot is an IRC bot written in Python 2 using Twisted. It can respond to
requests to run Gerrit Nag on IRC and reply with the results.

Nagbot responds to the following commands:

````
nagbot: team report
nagbot: team average
nagbot: how many reviews for sbaird?
````

It can do a few other things and will generally try to be polite and answer
when spoken to.


## Example Usage

````
$ ./nagbot.py \
    --host irc.example.com \
    --port 6667 \
    --channel foodev \
    --users finn,jake,marcy,pb,lsp \
    --gerrit https://gerrit.example.com \
    --project foo
````

# To Do

* Properly support running Nagbot on multiple channels
* More useful features for Nagbot

# License

This project is licensed under the GPL v2. Please see
[LICENSE.txt](LICENSE.txt) for details.

# Authors

* [Simon Baird](https://github.com/simonbaird)
* [Róman Joost](https://github.com/romanofski)

# Acknowledgments

* Gerrit Nag is based on an original script created by
    [Rohan McGovern](https://github.com/rohanpm).
* Nagbot is loosely based on, and inspired by, 'beerbot',
    created by [Peter "Who-T" Hutterer](https://github.com/whot).
* [Red Hat](https://www.redhat.com/).
