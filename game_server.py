#!/usr/bin/env -S python3 -u
from random import choice
from string import digits
import itertools

import sys
import json
import struct
import os
import subprocess
from shlex import split
import json, random, asyncio, argparse
import aioquic, aioquic.asyncio, aioquic.h3.connection
import webtransport

BIND_ADDRESS = '::1'
BIND_PORT = 4433

class CowboyHandler:
  def __init__(self, protocol, session_id, http):
    # global client_counter
    self._protocol = protocol
    # self.client_counter = client_counter
    # client_counter += 1
    self._session_id = session_id
    self._http = http

  def send_json_datagram(self):
    # self._http.send_datagram(self._session_id, json.dumps(data).encode('utf-8'))
    # Tell the aioquic library that it should now immediately initiate actual network
    # transfers for the data we want to send. Without this, there can be 5-10 seconds
    # long delays before the datagrams actually reach the network.
    # TODO: Should probably refactor to call .transmit() only after processing
    # a full batch of H3 messages that were received in one go, but would be good to
    # first get some kind of lower level profiling tool going to be able to examine
    # the effect.
    for chunk in iter(lambda: ''.join(choice(digits) for i in range(512)).encode(), b''):
      if chunk is not None:
        self._http.send_datagram(self._session_id, chunk) 
        self._protocol.transmit()

  def h3_event_received(self, event):
    if isinstance(event, aioquic.h3.events.DatagramReceived):
      self.send_json_datagram()
     
def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('certificate')
  parser.add_argument('key')
  args = parser.parse_args()
  port = 4433
  configuration = aioquic.quic.configuration.QuicConfiguration(alpn_protocols=aioquic.h3.connection.H3_ALPN, is_client=False, max_datagram_frame_size=65536)
  configuration.load_cert_chain(args.certificate, args.key)
  loop = asyncio.get_event_loop()
  loop.run_until_complete(aioquic.asyncio.serve(BIND_ADDRESS, BIND_PORT, configuration=configuration, create_protocol=webtransport.create_web_transport_protocol(CowboyHandler)))
  try:
    print("Listening for webtransport connections at https://{}:{}/".format(BIND_ADDRESS, BIND_PORT))
    loop.run_forever()
  except KeyboardInterrupt:
    pass

if __name__ == "__main__":
  main()
