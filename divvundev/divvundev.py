#!/usr/bin/env python3
"""Development tools for GiellaLT repos."""

import os
import subprocess
import sys
from argparse import ArgumentParser, Namespace

from git import Repo


def getdeps(repodir: str):
    """Get dependencies of the repo.

    Currently just scanning configure.ac."""
    deps = []
    with open(os.path.join(repodir, "configure.ac"),
              encoding="utf-8") as config:
        for line in config:
            if line.startswith("gt_USE_SHARED"):
                dep = line.split(",")[1].strip().lstrip("[").rstrip("]")
                if not dep:
                    print("Error: couldn't parse dep from config line:\n" +
                          line)
                else:
                    deps.append(dep)
    return deps


def clone(repodir: str, options: Namespace):
    """clone new repo."""
    repourl = "https://github.com/giellalt/" + os.path.basename(repodir)
    if options.verbose:
        print(f"cloning {repourl} to {repodir}")
    _ = Repo.clone_from(repourl, repodir)


def pull(repodir: str, options: Namespace):
    """pull repo."""
    if options.verbose:
        print(f"pulling {repodir}")
    repo = Repo(repodir)
    if repo.is_dirty():
        print(f"cannot update {repodir} because it's dirty")
        return
    repo.remote().pull()


def update(repodir: str, options: Namespace):
    """Update repo and its dependents."""
    if options.verbose:
        print(f"updating {repodir}")
    giellacoredir = os.path.join(repodir, os.pardir, "giella-core")
    if not os.path.isdir(giellacoredir):
        print(f"missing giella-core {giellacoredir}")
        answer = input("Clone? ")
        if answer in ["y", "Y", "yes"]:
            clone(giellacoredir, options)
        elif answer in ["n", "N", "no"]:
            print(f"please clone {giellacoredir} manually and retry")
            sys.exit(1)
        else:
            print(f"I assume {answer} means no, exitting...")
            sys.exit(1)
    else:
        if options.verbose:
            print(f"updating giella-core {giellacoredir} first")
        pull(giellacoredir, options)
    os.chdir(giellacoredir)
    configure(giellacoredir, options)
    build(giellacoredir, options)
    deps = getdeps(repodir)
    for dep in deps:
        depdir = os.path.join(repodir, os.pardir, dep)
        if not os.path.isdir(depdir):
            print(f"missing dependency {depdir}")
            answer = input("Clone? ")
            if answer in ["y", "Y", "yes"]:
                clone(depdir, options)
            elif answer in ["n", "N", "no"]:
                print(f"please clone {depdir} manually and try again")
                sys.exit(1)
            else:
                print(f"I assume {answer} means no, quitting...")
                sys.exit(1)
        else:
            if options.verbose:
                print(f"updating dep {depdir} first")
            pull(depdir, options)
        os.chdir(depdir)
        configure(depdir, options)
        build(depdir, options)
    os.chdir(repodir)
    pull(repodir, options)


def configure(repodir: str, options: Namespace):
    """Configure repo."""
    if options.verbose:
        print(f"configuring {repodir}")
    autogen = os.path.join(repodir, "autogen.sh")
    if os.path.exists(autogen):
        subprocess.run([autogen], check=True)
    else:
        print(f"Missing {autogen}")
        sys.exit(1)
    configstatus = os.path.join(repodir, "config.status")
    config = os.path.join(repodir, "configure")
    if os.path.exists(configstatus):
        subprocess.run([configstatus], check=True)
    elif os.path.exists(config):
        subprocess.run([config], check=True)


def build(repodir: str, options: Namespace):
    """Build repo."""
    if options.verbose:
        print(f"building {repodir}")
    subprocess.run(["make"], check=True)


def test(repodir: str, options: Namespace):
    """Run tests in repo."""
    if options.verbose:
        print(f"testing {repodir}")
    subprocess.run(["make", "check"], check=True)


def main():
    """CLI for divvundev tool."""
    argp = ArgumentParser()
    argp.add_argument("subcommand",
                      choices=["configure", "update", "build", "test"])
    argp.add_argument("-v", "--verbose", action="store_true", default=False,
                      help="print something")
    argp.add_argument("-d", "--debug", action="store_true", default=False,
                      help="print more somethings")
    argp.add_argument("-r", "--repo-dir", type=str, metavar="REPODIR",
                      help="Use REPODIR as repository (defaults current dir)")
    argp.add_argument("-y", "--no-interactive", action="store_true",
                      default=False,
                      help="Run non-interactively (answer yes to all)")
    options = argp.parse_args()
    repodir = os.getcwd()
    if options.repo_dir:
        repodir = options.repo_dir
        os.chdir(repodir)
        if options.verbose:
            print(f"Using {repodir} as repository")
    else:
        if options.verbose:
            print(f"Using current dir: {repodir} as repository")
    if options.subcommand == "update":
        if options.verbose:
            print("updating")
        update(repodir, options)
    elif options.subcommand == "build":
        build(repodir, options)
    elif options.subcommand == "configure":
        configure(repodir, options)
    elif options.subcommand == "test":
        test(repodir, options)
    else:
        print("Unknown command {subcommand}")
        sys.exit(1)


if __name__ == "__main__":
    main()
