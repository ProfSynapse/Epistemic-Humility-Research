# Desktop SSH address selection

A short Windows hostname can resolve through LAN DNS instead of Tailscale.
An SSH timeout at that address does not establish that the desktop is offline
or Docker is stopped.

1. Check the short name with `getent hosts desktop-2a4u5kr`.
2. Check the intended peer with `tailscale ping desktop-2a4u5kr` and its current
   Tailscale status. Verify the peer identity and current tailnet address.
3. If the LAN route times out while that peer is reachable, connect to its
   verified tailnet address. Use `HostKeyAlias=desktop-2a4u5kr` to retain the
   existing SSH host-key check. Keep `BatchMode=yes`, `SendEnv=-`, and the
   registered identity key. The same address/alias flags apply to `scp`.
4. Do not disable host-key checking, infer an SSH-service failure from DNS,
   hardcode a transient address into a skill, or change global SSH/DNS settings.

Use the peer's verified MagicDNS name when available. If the correct tailnet
address also fails, diagnose that exact connection before requesting an owner
service action. Docker checks follow only after SSH reaches the intended host.
