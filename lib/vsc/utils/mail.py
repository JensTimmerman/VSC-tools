#!/usr/bin/env python
##
# Copyright 2012 Ghent University
# Copyright 2012 Andy Georges
#
# This file is part of VSC-tools,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://vscentrum.be/nl/en),
# the Hercules foundation (http://www.herculesstichting.be/in_English)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# http://github.com/hpcugent/VSC-tools
#
# VSC-tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# VSC-tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with VSC-tools. If not, see <http://www.gnu.org/licenses/>.
##
"""
Wrapper around the standard Python mail library.

  - Send a plain text message
  - Send an HTML message, with a plain text alternative
"""

import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import vsc.fancylogger as fancylogger


class VscMailError(Exception):
    """Raised if the sending of an email fails for some reason."""

    def __init__(self, mail_host=None, mail_to=None, mail_from=None, mail_subject=None, err=None):
        """Initialisation.

        @type mail_host: string
        @type mail_to: string
        @type mail_from: string
        @type mail_subject: string
        @type err: Exception subclass

        @param mail_host: the SMTP host for actually sending the mail.
        @param mail_to: a well-formed email address of the recipient.
        @param mail_from: a well-formed email address of the sender.
        @param mail_subject: the subject of the mail.
        @param err: the original exception, if any.
        """
        self.mail_host = mail_host
        self.mail_to = mail_to
        self.mail_from = mail_from
        self.mail_subject = mail_subject
        self.err = err


class VscMail(object):
    """Class providing functionality to send out mail."""

    def __init__(self, mail_host=None):
        self.mail_host = mail_host
        self.log = fancylogger.getLogger(self.__class__.__name__)

    def _send(self,
              mail_from,
              mail_to,
              mail_subject,
              msg):
        """Actually send the mail.

        @type mail_from: string representing the sender.
        @type mail_to: string representing the recipient.
        @type mail_subject: string representing the subject.
        @type msg: MIME message.
        """

        try:
            if self.mail_host:
                s = smtplib.SMTP(self.mail_host)
            else:
                s = smtplib.SMTP()
            s.connect()
            try:
                s.sendmail(mail_from, mail_to, msg.as_string())
            except smtplib.SMTPHeloError, err:
                self.log.error("Cannot get a proper response from the SMTP host" +
                               (self.mail_host and " %s" % (self.mail_host) or ""))
                raise
            except smtplib.SMTPRecipientsRefused, err:
                self.log.error("All recipients were refused by SMTP host" +
                               (self.mail_host and " %s" % (self.mail_host) or "") +
                               " [%s]" % (mail_to))
                raise
            except smtplib.SMTPSenderRefused, err:
                self.log.error("Sender was refused by SMTP host" +
                               (self.mail_host and " %s" % (self.mail_host) or "") +
                               "%s" % (mail_from))
                raise
            except smtplib.SMTPDataError, err:
                raise
        except smtplib.SMTPConnectError, err:
            self.log.error("Cannot connect to the SMTP host" + (self.mail_host and " %s" % (self.mail_host) or ""))
            raise VscMailError(mail_host=self.mail_host,
                               mail_to=mail_to,
                               mail_from=mail_from,
                               mail_subject=mail_subject,
                               err=err)
        except Exception, err:
            self.log.error("Some unknown exception occurred in VscMail.sendTextMail. Raising a VscMailError.")
            raise VscMailError(mail_host=self.mail_host,
                               mail_to=mail_to,
                               mail_from=mail_from,
                               mail_subject=mail_subject,
                               err=err)

    def sendTextMail(self,
                     mail_to,
                     mail_from,
                     reply_to,
                     mail_subject,
                     message):
        """Send out the given message by mail to the given recipient(s).

        @type mail_to: string or list of strings
        @type mail_from: string
        @type reply_to: string
        @type mail_subject: string
        @type message: string

        @param mail_to: a valid recipient email address
        @param mail_from: a valid sender email address.
        @param reply_to: a valid email address for the (potential) replies.
        @param mail_subject: the subject of the email.
        @param message: the body of the mail.
        """
        self.log.info("Sending mail [%s] to %s." % (mail_subject, mail_to))

        if reply_to is None:
            reply_to = mail_from
        msg = MIMEText(message)
        msg['Subject'] = mail_subject
        msg['From'] = mail_from
        msg['To'] = mail_to
        msg['Reply-to'] = reply_to

        self._send(mail_from, mail_to, mail_subject, msg)

    def _replace_images_cid(self, html, images):
        """Replaces all occurences of the src="IMAGE" with src="cid:IMAGE" in the provided html argument.

        @type html: string
        @type images: list of strings

        @param html: HTML data, containing image tags for each of the provided images
        @param images: references to the images occuring in the HTML payload

        @return: the altered HTML string.
        """

        for im in images:
            re_src = re.compile("src=\"%s\"" % im)
            (html, count) = re_src.subn("src=\"cid:%s\"" % im, html)
            if count == 0:
                self.log.raiseException("Could not find image %s in provided HTML." % im, VscMailError)

        return html

    def sendHTMLMail(self,
                     mail_to,
                     mail_from,
                     reply_to,
                     mail_subject,
                     html_message,
                     text_alternative,
                     images=None,
                     css=None):
        """
        Send an HTML email message, encoded in a MIME/multipart message.

        The images and css are included in the message, and should be provided separately.

        @type mail_to: string or list of strings
        @type mail_from: string
        @type reply_to: string
        @type mail_subject: string
        @type html_message: string
        @type text_alternative: string
        @type images: list of strings
        @type css: string

        @param mail_to: a valid recipient email addresses.
        @param mail_from: a valid sender email address.
        @param reply_to: a valid email address for the (potential) replies.
        @param html_message: the actual payload, body of the mail
        @param text_alternative: plain-text version of the mail body
        @param images: the images that are referenced in the HTML body. These should be available as files on the
                      filesystem in the directory where the script runs. Caveat: assume jpeg image type.
        @param css: CSS definitions
        """

        # Create message container - the correct MIME type is multipart/alternative.
        msg_root = MIMEMultipart('alternative')
        msg_root['Subject'] = mail_subject
        msg_root['From'] = mail_from
        msg_root['To'] = mail_to

        msg_root.preamble = 'This is a multi-part message in MIME format. If your email client does not support this (correctly), the first part is the plain text version.'

        # Create the body of the message (a plain-text and an HTML version).
        if images is not None:
            html_message = self.replace_images_cid(html_message, images)

        # Record the MIME types of both parts - text/plain and text/html_message.
        msg_plain = MIMEText(text_alternative, 'plain')
        msg_html = MIMEText(html_message, 'html_message')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg_root.attach(msg_plain)
        msg_alt = MIMEMultipart('related')
        msg_alt.attach(msg_html)

        if css is not None:
            msg_html_css = MIMEText(css, 'css')
            msg_html_css.add_header('Content-ID', '<newsletter.css>')
            msg_alt.attach(msg_html_css)

        if images is not None:
            for im in images:
                image_fp = open(im, 'r')
                msg_image = MIMEImage(image_fp.read(), 'jpeg')  # FIXME: for now, we assume jpegs
                image_fp.close()
                msg_image.add_header('Content-ID', "<%s>" % im)
                msg_alt.attach(msg_image)

        msg_root.attach(msg_alt)

        self._send(mail_from, mail_to, mail_subject, msg_root)
