#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import sys
import os
import json
import argparse
import re
from pathlib import Path
from urllib import error
from typing import Dict, Any, List

# Hackery to enable importing of utils from ci/scripts/jenkins
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(REPO_ROOT / "ci" / "scripts" / "jenkins"))

from git_utils import git, GitHubRepo, parse_remote


def find_reviewers(body: str) -> List[str]:
    print(f"Parsing body:\n{body}")
    matches = re.findall(r"(cc( @[-A-Za-z0-9]+)+)", body, flags=re.MULTILINE)
    matches = [full for full, last in matches]

    print("Found matches:", matches)
    reviewers = []
    for match in matches:
        if match.startswith("cc "):
            match = match.replace("cc ", "")
        users = [x.strip() for x in match.split("@")]
        reviewers += users

    reviewers = set(x for x in reviewers if x != "")
    return sorted(list(reviewers))


if __name__ == "__main__":
    help = "Add @cc'ed people in a PR body as reviewers"
    parser = argparse.ArgumentParser(description=help)
    parser.add_argument("--remote", default="origin", help="ssh remote to parse")
    parser.add_argument("--testing-reviews-json", help="(testing only) reviews as JSON")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="run but don't send any request to GitHub",
    )
    args = parser.parse_args()

    # 查看提交 PR 的信息
    remote = git(["config", "--get", f"remote.{args.remote}.url"])
    user, repo = parse_remote(remote)

    pr = json.loads(os.environ["PR"])

    # PR 序号
    number = pr["number"]
    # comment 内容 图片也能带上
    body = pr["body"]
    if body is None:
        body = ""

    # 根据提交的 comment 内容查找是否有@或者cc哪些 reviewers
    new_reviewers = find_reviewers(body)
    print("Found these reviewers:", new_reviewers)

    if args.testing_reviews_json:
        existing_reviews = json.loads(args.testing_reviews_json)
    else:
        github = GitHubRepo(token=os.environ["GITHUB_TOKEN"], user=user, repo=repo)
        existing_reviews = github.get(f"pulls/{number}/reviews")
        # List reviews for a pull request

    # PR 请求的审查人员中是否已经有人评论(审查)过该 PR 了
    existing_review_users = [review["user"]["login"] for review in existing_reviews]
    print("PR has reviews from these users:", existing_review_users)
    existing_review_users = set(r.lower() for r in existing_review_users)

    # 请求审查的人中是审查员的人  -> 判断请求的人是否是可以审查的人员 -> 获取到其中审查员列表
    existing_reviewers = [review["login"] for review in pr["requested_reviewers"]]
    print("PR already had these reviewers requested:", existing_reviewers)

    # 转成小写，可能时为了方便排除同一个人大但是由于大小写重复的问题？ reviewers 去重 -> 确定是审查人员的人的全小写姓名
    existing_reviewers_lower = {
        existing_reviewer.lower() for existing_reviewer in existing_reviewers
    }
    to_add = []
    # 判断哪个部分是不是已经被审查过了，审查过了就跳过，没审查过组成一个新的列表
    # 判断请求审查的人员中是否有审查人员 或者 是否有请求审查的人不是审查人员但是该人员已经审查过了 然后就跳过
    for new_reviewer in new_reviewers:
        if (
            new_reviewer.lower() in existing_reviewers_lower
            or new_reviewer.lower() in existing_review_users
        ):
            print(f"{new_reviewer} is already review requested, skipping")
        else:
            to_add.append(new_reviewer)

    print(f"After filtering existing reviewers, adding: {to_add}")

    if not args.dry_run:
        github = GitHubRepo(token=os.environ["GITHUB_TOKEN"], user=user, repo=repo)

        # Add reviewers 1 by 1 since GitHub will error out if any of the
        # requested reviewers aren't members / contributors
        for reviewer in to_add:
            try:
                # 增加审查人员 -> 请求该审查人员进行审查并给予通知 (只能添加 Team 的人员进行审查)
                github.post(f"pulls/{number}/requested_reviewers", {"reviewers": [reviewer]})
            except KeyboardInterrupt:
                sys.exit()
            except (RuntimeError, error.HTTPError) as e:
                # Catch any exception so other reviewers can be processed
                print(f"Failed to add reviewer {reviewer}: {e}")
