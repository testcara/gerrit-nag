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

    # Given a prefix and message, if the message starts with
    # the prefix then remove it and return the rest of the message.
    # If the prefix is not found return None. Match the prefix with
    # or without a ':' char.
    def prefix_match_message(self, prefix, message):
        pattern = r"^{}:? (.*)$".format(prefix)
        if re.match(pattern, message):
            return re.sub(pattern, '\\1', message)
        return None

    def handle_direct_message(self, nick, message):
        print("Private message from {}: {}".format(nick, message))

        say_message = self.prefix_match_message('say', message)
        if say_message:
            # Send message to the channel
            # (Note we're assuming just one channel here)
            self.msg(self.factory.nagbot_opts.channel, say_message)
            return

        self.msg(nick, "Huh?")

    def handle_channel_request(self, nick, channel, message):
        print("Command from {} on {}: {}".format(nick, channel, message))

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
            return

        if re.match(r".*hello.*", message):
            self.msg(channel, "Hello " + nick)
            return

        if re.match(r".*thanks.*", message):
            self.msg(channel, "You're welcome " + nick)
            return

        self.msg(channel, "Huh?")

    def handle_channel_message(self, nick, channel, message):
        # Ignore for now
        pass

    def privmsg(self, user, channel, message):
        nick, _, host = user.partition('!')
        message.strip()

        if channel == self.nickname:
            # A direct message
            self.handle_direct_message(nick, message)
        else:
            # An in-channel message
            command = self.prefix_match_message(self.nickname, message)
            if command:
                # A message for our attention
                self.handle_channel_request(nick, channel, command)
            else:
                # A general channel message
                self.handle_channel_message(nick, channel, message)

class NagBotFactory(protocol.ReconnectingClientFactory):
    protocol = NagBotProtocol

#-----------------------------------------------------------------------------

def get_client_factory(opts):
    NagBotProtocol.nickname = opts.nickname
    NagBotProtocol.realname = opts.realname

    if not opts.channel.startswith('#'):
        opts.channel = '#{}'.format(opts.channel)
    NagBotFactory.channels = [opts.channel]

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
