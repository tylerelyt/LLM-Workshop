"""Verify local Feishu CLI authorization and optionally read a Feishu document outline."""

import argparse
from pathlib import Path
import sys

# The standalone Skill also supplies the CLI helpers for the course examples.
sys.path.insert(0, str(Path(__file__).resolve().parent / "skills/feishu-document-search/scripts"))
from search_documents import run_lark, workspace_environment


def read_outline(doc, environment):
    payload = run_lark(
        ["docs", "+fetch", "--as", "user", "--doc", doc, "--scope", "outline", "--max-depth", "3"],
        environment,
    )
    document = payload.get("data", {}).get("document", {})
    if (payload.get("ok") is not True or payload.get("identity") != "user"
            or document.get("revision_id") is None or "content" not in document):
        raise RuntimeError("The Feishu response did not confirm a user read with a document revision.")
    return document["revision_id"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doc", help="Optional authorized Feishu Docx or Wiki teaching document")
    args = parser.parse_args()
    environment = workspace_environment()

    stage = "user authorization"
    try:
        identity = run_lark(["whoami", "--as", "user"], environment)
        if identity.get("identity") != "user" or identity.get("available") is not True:
            raise RuntimeError("No usable Feishu user identity in this workspace.")
        status = run_lark(["auth", "status", "--json", "--verify"], environment)
        user = status.get("identities", {}).get("user", {})
        if user.get("verified") is not True or user.get("tokenStatus") != "valid":
            raise RuntimeError(f"Feishu did not verify the user token ({user.get('tokenStatus', 'unavailable')}).")
        print("PASS user authorization: Feishu verified the user token.")

        if args.doc:
            stage = "document access"
            revision = read_outline(args.doc, environment)
            print(f"PASS document access: read the outline at revision {revision}.")
        else:
            print("Document access: supply --doc to verify access to a specific document.")
    except RuntimeError as error:
        parser.exit(1, f"FAIL {stage}: {error}\n")


if __name__ == "__main__":
    main()
