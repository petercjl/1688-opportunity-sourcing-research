#!/usr/bin/env python3
import argparse,json,os,subprocess

def atomic_command():
    entry=os.environ.get("ALI1688_CLI_ENTRY")
    node=os.environ.get("ALI1688_NODE")
    if not entry or not node:
        raise RuntimeError("DEPENDENCY_UNAVAILABLE: run through 1688-opportunity-sourcing-research script")
    return [node,entry]

def invoke(args):
    proc=subprocess.run(atomic_command()+args,text=True,encoding="utf-8",capture_output=True,timeout=180,check=False)
    try: value=json.loads(proc.stdout or proc.stderr)
    except ValueError: value={"ok":False,"error":{"code":"INVALID_RESPONSE","message":"Capability returned no JSON"}}
    return value,proc.returncode

def inspect():
    c,code=invoke(["capabilities","--json"])
    if code or c.get("contracts",{}).get("products")!="1688-products@1" or c.get("contracts",{}).get("suppliers")!="1688-suppliers@1":
        raise RuntimeError("CONTRACT_UNSUPPORTED: require 1688-products@1 and 1688-suppliers@1")
    return c

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--require-all",action="store_true");parser.parse_args()
    c=inspect();source,code=invoke(["skill","source","--json"])
    print(json.dumps({"ok":code==0,"package":c["package"],"version":c["version"],"contracts":c["contracts"],"skill_source":source.get("source")},ensure_ascii=False))
    raise SystemExit(code)
if __name__=="__main__":main()
