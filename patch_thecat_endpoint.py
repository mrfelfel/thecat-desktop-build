#!/usr/bin/env python3
"""Patch official TDesktop built-in DCs + RSA keys for theCat private server."""
import pathlib
import re
import sys

default = pathlib.Path(__file__).resolve().parent / "tdesktop/Telegram/SourceFiles/mtproto/mtproto_dc_options.cpp"
path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else default
text = path.read_text()

# DC2 (server-reported) → public MTProto endpoint.
new_dcs = """const BuiltInDc kBuiltInDcs[] = {
	{ 2, "62.220.127.238", 30001 },
};"""

new_dcs_v6 = """const BuiltInDc kBuiltInDcsIPv6[] = {
	// theCat exposes IPv4 only; keep a single dummy so the array is non-empty.
	{ 2, "2001:db8::2", 30001 },
};"""

new_rsa = """const char *kPublicRSAKeys[] = { "\\
-----BEGIN RSA PUBLIC KEY-----\\n\\
MIIBCgKCAQEA2LnOaBr+GoK84cDv4c0h3cLZ2EAJsnI+syy7L7VdFV9JkHQ3ODA8\\n\\
ydSND5DfmDp7ZMG5AQWu+ca9jrRNqgiHtmTdLcZfLM/2XXEqYznNfikpmelv0qA3\\n\\
UvNdDTD24PVwXpMwe86j+On45NgZcvS464DUGcM2wPDY0zOIFInVL+R3u+XmIJ8E\\n\\
FxdZxR+4ktDx6Pb+OoxmpH4Y9KHbLNwQ7MmFSW9Luw7z02D2ySD3edQIrdeXI6pW\\n\\
aNOZhRIKfL94qJbdG0+7fUp0M7d2WjKKoyZ2Vb1Yt6BDUqr+pG/6/lJOL4p4EKEg\\n\\
MwitjfUc+a9fPtKx25osD33c0L5889yVkQIDAQAB\\n\\
-----END RSA PUBLIC KEY-----" };"""

def replace_block(src, decl_name, replacement):
    # Match "const TYPE NAME[] = { ... };"
    pattern = re.compile(
        r"const [^=\n]*\b" + re.escape(decl_name) + r"\s*\[\s*\]\s*=\s*\{.*?\};",
        re.S,
    )
    new_src, n = pattern.subn(replacement, src, count=1)
    if n != 1:
        raise SystemExit(f"failed to replace {decl_name} (matches={n})")
    return new_src

text = replace_block(text, "kBuiltInDcs", new_dcs)
text = replace_block(text, "kBuiltInDcsIPv6", new_dcs_v6)
text = replace_block(text, "kPublicRSAKeys", new_rsa)

# Skip advertising the documentation IPv6 dummy: force IPv6 list unused in production
# by making constructFromBuiltIn only apply IPv4 when the IP is our host.
# Safer: patch the IPv6 apply loop to skip non-global / documentation prefixes.
old_v6_loop = """	const auto listv6 = isTestMode()
		? gsl::make_span(kBuiltInDcsIPv6Test)
		: gsl::make_span(kBuiltInDcsIPv6).subspan(0);
	for (const auto &entry : listv6) {
		const auto flags = Flag::f_static | Flag::f_ipv6;
		applyOneGuarded(entry.id, flags, entry.ip, entry.port, {});
		DEBUG_LOG(("MTP Info: adding built in DC %1 IPv6 connect option: "
			"%2:%3"
			).arg(entry.id
			).arg(entry.ip
			).arg(entry.port));
	}"""
new_v6_loop = """	// theCat private server: IPv4 only (62.220.127.238:30001). Do not add IPv6."""
if old_v6_loop not in text:
    raise SystemExit("IPv6 apply loop not found — check upstream shape")
text = text.replace(old_v6_loop, new_v6_loop, 1)

path.write_text(text)
print("patched", path)
