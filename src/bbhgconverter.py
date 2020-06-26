#!/usr/bin/env python
import argparse
import datetime
import os
import shutil
import subprocess
import sys
from getpass import getpass

import requests
from requests.auth import HTTPBasicAuth

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote


def get_repositories(
    username, password, team
):
    auth = None
    repos = []
    try:
        if all((username, password)):
            auth = HTTPBasicAuth(username, password)
        if auth is None:
            exit("Must provide username/password or oath credentials")
        if not team or username:
            response = requests.get("https://api.bitbucket.org/2.0/user/", auth=auth)
            username = response.json().get("username")
        url = "https://api.bitbucket.org/2.0/repositories/{}/".format(team)

        response = requests.get(url, auth=auth)
        response.raise_for_status()
        repos_data = response.json()
        for repo in repos_data.get("values"):
            repos.append(repo)
        while repos_data.get("next"):
            response = requests.get(repos_data.get("next"), auth=auth)
            repos_data = response.json()
            for repo in repos_data.get("values"):
                repos.append(repo)
    except requests.exceptions.RequestException as e:

        if e.response.status_code == 401:
            exit(
                "Unauthorized! Check your credentials and try again.", 22
            )  # EINVAL - Invalid argument
        else:
            exit(
                "Connection Error! Bitbucket returned HTTP error [%s]."
                % e.response.status_code
            )
    return repos

def export_repos(username, password,team):
    
    repos = get_repositories(username, password, team)
    repo_list = []
    git_repos = []
    hg_repos = []
    repos = sorted(repos, key=lambda repo_: repo_.get("name"))
    for repo in repos:
        repo_list.append(repo.get("slug"))
        repo_list_file = open("all_repo_list.txt","a+")
        repo_list_file.write("%s \n" % repo['slug']) 
        repo_list_file.close()
        if repo.get('scm') == "hg":
            hg_repos.append(repo.get("slug"))
            hg_repo_list = open("hg_repo_list.txt","a+")
            hg_repo_list.write("%s \n" % repo['slug'])
            hg_repo_list.close
        else:
            git_repos.append(repo.get("slug"))
            git_repo_list = open("git_repo_list.txt","a+")
            git_repo_list.write("%s \n" % repo['slug'])
            git_repo_list.close 
    return git_repos, hg_repos, repos

def reposdir(dir, team, scm):
    dir = dir + "/" + team + "_" + scm
    # print(dir)
    if os.path.isdir(dir):
        print("dir exists!")
    else:
        print("The dir doesnt exist,creating one now..")
        os.makedirs(dir)
    return dir

def exec_command(command):
    subprocess.call(command, shell=True)

def clone_repos(git_repos, hg_repos, team, repodir, hgclone, gitclone, repos):

    if hgclone == "yes" :
        scm = "hg"
        owd = os.getcwd()
        hgreposdir = reposdir(repodir, team, scm)
        print(hgreposdir)
        os.chdir(hgreposdir)
        pwd = os.getcwd()
        for repo in repos:
            slug = repo.get("slug")
            owner = repo.get("owner").get("username") or repo.get("owner").get("nickname")
            owner_url = quote(owner)
            slug_url = quote(slug)
            command = "hg clone ssh://hg@bitbucket.org/%s/%s" % (owner_url, slug_url)
            exec_command(command)
        return pwd
        os.chdir(owd)
    if  gitclone == "yes":
        scm = "git"
        gitreposdir = reposdir(repodir, team, scm)
    
def convert_repos(hg_cloned_repos, hg_repos, team, repodir, rootpath):
    converted_hg_dir = repodir + "/" + team + "converted_hg" 
    if os.path.isdir(converted_hg_dir):
        print("%s path exists", converted_hg_dir)
    else:
        os.makedirs(converted_hg_dir)
    os.chdir(converted_hg_dir)
    pwd = os.getcwd()
    print(pwd)
    for repo in hg_repos:
        if os.path.isdir(repo):
            print("not empty")
        else:
            os.mkdir(repo)
            os.chdir(repo)
            gitcommand = "git init"
            exec_command(gitcommand)
            convertcommand = "%s/fast-export/hg-fast-export.sh -r %s/%s" % ( rootpath, hg_cloned_repos, repo)
            print(convertcommand)
            exec_command(convertcommand)
            os.chdir(pwd)

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True)
    parser.add_argument('-p', '--password',  required=True)
    parser.add_argument('-t', '--team', required=True)
    parser.add_argument('-m', '--hgclone',  required=False)
    parser.add_argument('-g', '--gitclone',  required=False)    
    parser.add_argument('-d', '--repodir', required=False )
    parser.add_argument('-c', '--convert', required=False )    
    args = parser.parse_args()
    print(args.username)
    username = args.username
    password = args.password
    team = args.team
    repodir = args.repodir
    hgclone = args.hgclone
    gitclone = args.gitclone

    rootpath = os.getcwd()
    # print(rootpath)
    if hgclone or gitclone:
        git_repos, hg_repos, repos = export_repos(username, password, team)
        hg_cloned_repos = clone_repos(git_repos, hg_repos, team, repodir, hgclone, gitclone, repos)
    if args.convert == "yes":
        convert_repos(hg_cloned_repos, hg_repos, team, repodir, rootpath)
    else:
         export_repos(username, password, team)


if __name__ == "__main__":
    main()

