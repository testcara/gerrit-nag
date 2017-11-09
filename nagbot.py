#!/usr/bin/env python
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Example usage:
#
#   ./nagbot.py \
#     --host irc.example.com \
#     --port 6667 \
#     --channel foodev \
#     --users finn,jake,marcy,pb,lsp \
#     --gerrit https://gerrit.example.com \
#     --project foo
#
# In IRC:
#   <finn> nagbot: team report please
#
# Based on beerbot by Peter "Who-T" Hutterer
# http://who-t.blogspot.com.au/
#
import sys
import re
import time
import datetime
import random
import yaml
import subprocess
import argparse

from twisted.internet import reactor, protocol
from twisted.python import log
from twisted.words.protocols import irc

class NagBotProtocol(irc.IRCClient):

    def signedOn(self):
        self.lineRate = 2
        for channel in self.factory.channels:
            print("Joining {}".format(channel))
            self.join(channel)

    def handle_direct_message(self, nick, message):
        print("Private message from {}: {}".format(nick, message))
        pass

    def handle_channel_message(self, nick, channel, message):
        print("Channel message from {} on {}: {}".format(nick, channel, message))

        if re.match(r".*team report.*", message):
            self.msg(channel, "Team Report:")
            self.msg(channel, subprocess.check_output([
                "/usr/bin/python3",
                "gerrit-nag.py",
                self.factory.nagbot_opts.gerrit,
                self.factory.nagbot_opts.project,
                self.factory.nagbot_opts.users,
                "--shorter"]))
            self.msg(channel, "Please do some code reviews soon!")

        elif re.match(r".*hello.*", message):
            self.msg(channel, "Hi " + nick)

        else:
            self.msg(channel, "Huh?")

    def privmsg(self, user, channel, message):
        nick, _, host = user.partition('!')
        message.strip()

        if channel == self.nickname:
            # Direct message
            self.handle_direct_message(nick, message)

        elif (message.startswith(self.nickname + ': ') or message.startswith(self.nickname + ' ')):
            # In-channel ping
            self.handle_channel_message(nick, channel, message)

class NagBotFactory(protocol.ReconnectingClientFactory):
    protocol = NagBotProtocol

#-----------------------------------------------------------------------------

def get_client_factory(opts):
    NagBotProtocol.nickname = opts.nickname
    NagBotProtocol.realname = opts.realname

    channel = opts.channel
    if not channel.startswith('#'):
        channel = '#{}'.format(channel)
    NagBotFactory.channels = [channel]

    # So we can access them in our protocol methods
    NagBotFactory.nagbot_opts = opts

    return NagBotFactory()

def get_opts():
    p = argparse.ArgumentParser()
    p.add_argument('--host',     type=str,                          help='IRC host')
    p.add_argument('--port',     type=int, default=6667,            help='IRC port, default 6667')
    p.add_argument('--channel',  type=str,                          help='IRC channel')
    p.add_argument('--users',    type=str,                          help='Gerrit users to nag, comma separated')
    p.add_argument('--gerrit',   type=str,                          help='Gerrit URL')
    p.add_argument('--project',  type=str,                          help='Gerrit project')
    p.add_argument('--nickname', type=str, default='nagbot',        help='IRC nick, default "nagbot"')
    p.add_argument('--realname', type=str, default='Gerrit Nagbot', help='IRC real name, default "Gerrit Nagbot"')
    return p.parse_args()

if __name__ == '__main__':
    opts = get_opts()
    reactor.connectTCP(opts.host, opts.port, get_client_factory(opts))
    log.startLogging(sys.stdout)
    reactor.run()
