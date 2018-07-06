#!/usr/bin/env python
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
import sys
import re
import time
import datetime
import random
import yaml
import subprocess
import argparse

from twisted.internet import reactor, protocol, task
from twisted.python import log
from twisted.words.protocols import irc

def minute_tick(nagbot, channel):
    # Using local time for now
    now = datetime.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M')
    dow_str = now.strftime('%a')

    # TODO:
    # - Configurable events
    # - Happy birthdays?
    # - Calendar integration?
    if dow_str in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'] and time_str == '10:13':
        nagbot.msg(channel, "Standup time!")

    if dow_str == 'Fri' and time_str == '16:49':
        nagbot.msg(channel, "Have a good weekend everyone!")

class NagBotProtocol(irc.IRCClient):

    def signedOn(self):
        self.lineRate = 2
        for channel in self.factory.channels:
            print("Joining {}".format(channel))
            self.join(channel)
            task.LoopingCall(minute_tick, self, channel).start(60.0)

    # Given a prefix and message, if the message starts with
    # the prefix then remove it and return the rest of the message.
    # If the prefix is not found return None. Match the prefix with
    # or without a ':' char.
    def prefix_match_message(self, prefix, message):
        pattern = r"^(?:hey )?{}[:,]? (.*)$".format(prefix)
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

        if re.match(r".*team average.*", message):
            self.msg(channel, subprocess.check_output([
                "/usr/bin/python3",
                "gerrit-nag.py",
                self.factory.nagbot_opts.gerrit,
                self.factory.nagbot_opts.project,
                self.factory.nagbot_opts.users,
                "--shortest"]))
            self.msg(channel, "Code reviews are fun! Let's all do some code reviews!")
            return

        matches = re.match(r".*how many.*\s(\w+)\??$", message)
        if matches:
            self.msg(channel, subprocess.check_output([
                "/usr/bin/python3",
                "gerrit-nag.py",
                self.factory.nagbot_opts.gerrit,
                self.factory.nagbot_opts.project,
                matches.group(1),
                "--short"]))
            return

        if re.match(r".*(hello|hi\b).*", message):
            self.msg(channel, "Hello " + nick)
            return

        if re.match(r".*thanks.*", message):
            self.msg(channel, "You're welcome " + nick)
            return

        self.msg(channel, subprocess.check_output(["/usr/bin/fortune", "-s"]))

    def handle_channel_message(self, nick, channel, message):
        if re.match(r".*thanks.*\s{}".format(self.nickname), message):
            self.msg(channel, "You're welcome " + nick)
            return

        if re.match(r".*(hi|hello).*\s{}".format(self.nickname), message):
            self.msg(channel, "Hi " + nick)
            return

        if re.match(r".*(bye|good-bye).*\s{}".format(self.nickname), message):
            self.msg(channel, "Bye " + nick)
            return

        matches = re.match(r".*good (morning|afternoon|evening|night).*\s{}".format(self.nickname), message)
        if matches:
            self.msg(channel, "Good {} {}".format(matches.group(1), nick))
            return

        if re.match(r".*merry (xmas|christmas).*\s{}".format(self.nickname), message):
            if datetime.datetime.now().strftime('%b') == "Dec":
                self.msg(channel, "Merry Christmas " + nick + "!")
            else:
                self.msg(channel, "...okay sure " + nick)
            return

        if re.match(r".*happy holidays.*\s{}".format(self.nickname), message):
            if datetime.datetime.now().strftime('%b') == "Dec":
                self.msg(channel, "Happy Holidays " + nick + "!")
            else:
                self.msg(channel, "...okay sure " + nick)
            return

        if message == "mornings":
            self.msg(channel, "mornings {}".format(nick))
            return

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

    NagBotFactory.channels = []
    channels_list = opts.channels.split(',')
    for channel in channels_list:
        if not channel.startswith('#'):
            channel = '#{}'.format(channel)
        NagBotFactory.channels.append(channel)

    # So we can access them in our protocol methods
    NagBotFactory.nagbot_opts = opts

    return NagBotFactory()

def get_opts():
    p = argparse.ArgumentParser()
    p.add_argument('--host',     type=str,                          help='IRC host')
    p.add_argument('--port',     type=int, default=6667,            help='IRC port, default 6667')
    p.add_argument('--channels', type=str,                          help='IRC channels, comma separated')
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
