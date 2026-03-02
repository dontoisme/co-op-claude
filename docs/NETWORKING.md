# Networking

## Same-Machine Mode (Default)

Both stations share the filesystem at `/tmp/coop-claude/`. The SharedBus writes JSON message files and stations poll for new ones.

No additional setup required.

## Networked Mode (TCP Relay)

For developers on different machines, the host runs a TCP relay server.

### Host Setup

```bash
coop-claude start --name Don --role architect --partner West --serve --port 7723
```

The `--serve` flag starts a TCP relay on the specified port (default 7723).

### Guest Setup

```bash
coop-claude join --name West --role ux --host 192.168.1.100 --port 7723
```

### How It Works

1. Host's `CoopRelay` listens on the specified port
2. Guest's `RelayClient` connects via TCP
3. Messages are bidirectionally forwarded:
   - Host bus → TCP → Guest bus (and vice versa)
   - Each side maintains its own local message files
4. JSON messages are newline-delimited over the TCP connection

### Firewall

Ensure port 7723 (or your custom port) is open on the host machine.

### Limitations

- No encryption (use SSH tunnel for security over public networks)
- No authentication (trusted network assumed)
- Single relay connection at a time (2-player sessions)
