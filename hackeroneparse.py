#! /usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import time
import os
from configparser import ConfigParser
from progress.bar import Bar
from progress.spinner import Spinner


def main():
    config = Configuration()
    notify = TelegramNotify(config.get_api_token(), config.get_chat_id())
    req = HackerOneRequests(config.get_pages_per_req(), config.get_retry_time(),
                            config.get_req_timeout(), config.get_req_per_min())

    if config.get_telegram_mode():
        notify.send_message("<b>HackerOneParse</b> was started")

    old_dir_dict = {}
    old_scope_list = {}

    while True:
        cursor = None
        new_dir_dict = {}
        new_scope_dict = {}

        if len(old_dir_dict) > 0:
            bar = Bar("Scanning cycle", max=req.get_request_count())
            req.request_count_reset()
        else:
            bar = Spinner("First scanning... ")

        while True:
            dir_parse = DirectoryParse(req.get_directories_json_data(cursor))
            bar.next()
            cursor = dir_parse.get_cursor()
            new_dir_dict.update(dir_parse.dir_dict)
            if dir_parse.cursor is None:
                break

        for name, handle in new_dir_dict.items():
            in_scope = InScopeParse(req.get_in_scope_json_data(handle))
            bar.next()
            if in_scope.get_list() is None:
                new_scope_dict.update({name: []})
            else:
                new_scope_dict.update({name: in_scope.get_list()})

        if not old_dir_dict and not old_scope_list:
            old_dir_dict = new_dir_dict
            old_scope_list = new_scope_dict
            bar.finish()
            continue

        dif_dir_dict = {}
        dif_scope_dict = {}

        for new_name, new_scope in new_scope_dict.items():
            old_scope = old_scope_list.get(new_name)
            if old_scope is None:
                dif_dir_dict.update({new_name: new_dir_dict.get(new_name)})
            else:
                dif_scope = list(set(new_scope) - set(old_scope))
                if len(dif_scope) > 0:
                    dif_scope_dict.update({new_name: dif_scope})

        bar.finish()

        for dif_name_elem, dif_handle_elem in dif_dir_dict.items():
            print("New directory: " + dif_name_elem, notify.url_prefix(new_dir_dict.get(dif_name_elem)))

            if config.get_telegram_mode():
                notify.send_message(notify.msg_combine(dif_name_elem,
                                                       notify.url_prefix(new_dir_dict.get(dif_name_elem))))

        for dif_name_elem, dif_scope_elem in dif_scope_dict.items():
            print('New scope: [' + ', '.join(dif_scope_elem) + '] in "'
                  + dif_name_elem + '" program.', notify.url_prefix(new_dir_dict.get(dif_name_elem)))

            if config.get_telegram_mode():
                notify.send_message(notify.msg_combine(dif_name_elem,
                                                       notify.url_prefix(new_dir_dict.get(dif_name_elem)),
                                                       dif_scope_elem))

        old_dir_dict = new_dir_dict
        old_scope_list = new_scope_dict


class Configuration:
    def __init__(self, file_name='config.ini'):
        self.file_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), file_name)
        self.config_obj = ConfigParser()
        if self.test() is False:
            exit()

    def create_file(self):
        self.config_obj.add_section("Mode")
        self.config_obj.set("Mode", "telegram", "false")
        self.config_obj.add_section("TelegramBot")
        self.config_obj.set("TelegramBot", "api_token", "")
        self.config_obj.set("TelegramBot", "chat_id", "")
        self.config_obj.add_section("HackerOneRequests")
        self.config_obj.set("HackerOneRequests", "pages_per_request", "100")
        self.config_obj.set("HackerOneRequests", "retry_time", "10")
        self.config_obj.set("HackerOneRequests", "request_timeout", "10")
        self.config_obj.set("HackerOneRequests", "requests_per_minute", '120')

        with open(self.file_name, 'w') as conf:
            self.config_obj.write(conf)
        print('"' + self.file_name + '" file create, you can edit settings.')

    def test(self):
        if not self.config_obj.read(self.file_name):
            self.create_file()
            self.config_obj.read(self.file_name)

        if self.config_obj.getboolean("Mode", "telegram"):
            if not self.config_obj.get("TelegramBot", "api_token"):
                print('Set Telegram Bot API Token in "' + self.file_name + '" file')
                return False

            if not self.config_obj.get("TelegramBot", "chat_id"):
                print('Set Telegram Chat Id in "' + self.file_name + '" file')
                TelegramNotify.chat_id_detect(self.get_api_token())
                return False

        return True

    def get_telegram_mode(self): return self.config_obj.getboolean("Mode", "telegram")

    def get_api_token(self): return self.config_obj.get("TelegramBot", "api_token")

    def get_chat_id(self): return self.config_obj.get("TelegramBot", "chat_id")

    def get_pages_per_req(self): return int(self.config_obj.get("HackerOneRequests", "pages_per_request"))

    def get_retry_time(self): return int(self.config_obj.get("HackerOneRequests", "retry_time"))

    def get_req_timeout(self): return int(self.config_obj.get("HackerOneRequests", "request_timeout"))

    def get_req_per_min(self): return int(self.config_obj.get("HackerOneRequests", "requests_per_minute"))


class TelegramNotify:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_message(self, message):
        requests.get("https://api.telegram.org/"
                     "bot" + self.bot_token + "/sendMessage?"
                                              "chat_id=" + self.chat_id + "&parse_mode=html&text=" + message)

    @staticmethod
    def msg_combine(program_name, program_handle, in_scope_dirs_list=None):
        msg = "<b>BountyHunt: New "
        if in_scope_dirs_list is not None:
            msg += "scope:</b>%0A[" + ", ".join(in_scope_dirs_list) + "]"
        else:
            msg += "directory:</b>"

        msg += "%0A<b>Name:</b> " + program_name
        msg += "%0A<b>Link:</b> " + program_handle

        return msg

    @staticmethod
    def url_prefix(handle):
        """Add https prefix to str"""
        return "https://hackerone.com/" + str(handle)

    @staticmethod
    def chat_id_detect(bot_token):
        """Method for auto detecting "for last message" chat id in telegram bot"""
        data = requests.get("https://api.telegram.org/bot" + bot_token + "/getUpdates")
        if not data.json()['result']:
            return None
        else:
            chat_id = data.json()['result'][-1]['message']['chat']['id']
            print('Potential Chat Id is "' + str(chat_id) + '"')
            return chat_id


class HackerOneRequests:
    def __init__(self, pages_per_req=100, retry_time_value=10, timeout=15, req_per_min=20):
        self.pages_per_req = pages_per_req
        self.retry_time_value = retry_time_value
        self.timeout = timeout
        self.delay = 60 / req_per_min
        self.previous_req_time = time.time()
        self._request_count = 0

    def get_directories_json_data(self, cursor=None):
        """Function for parsing directories"""
        return self.graphql_request(self._hql_directories_request_body(cursor))

    def get_in_scope_json_data(self, handle=None):
        """Function for parsing directories"""
        return self.graphql_request(self._hql_in_scope_request_body(handle))

    def graphql_request(self, hql_data):
        """POST request to hraphql script"""
        self.request_sleeper()
        while True:
            headers = {"content-type": "application/json"}
            content = requests.post("https://hackerone.com/graphql", json=hql_data,
                                    headers=headers, timeout=self.timeout)
            self.previous_req_time = time.time()
            self._request_count += 1
            if content.status_code == 200:
                break
            else:
                time.sleep(self.retry_time_value)
        return content

    def request_sleeper(self):
        """Limiting the number of requests per minute"""
        dif_time = time.time() - self.previous_req_time
        if dif_time < self.delay:
            time.sleep(self.delay - dif_time)

    def request_count_reset(self):
        """Reset total request count"""
        self._request_count = 0

    def get_request_count(self): return self._request_count

    def _hql_directories_request_body(self, cursor=None):
        """Contain graphql request body for directories parsing"""
        return {"operationName": "DirectoryQuery",
                "variables": {
                    "where": {
                        "_and": [{
                            "_or": [{
                                "offers_bounties": {
                                    "_eq": True}}, {
                                "external_program": {
                                    "offers_rewards":
                                        {"_eq": True}}}]}, {
                            "_or": [{
                                "submission_state": {
                                    "_eq": "open"}}, {
                                "submission_state": {
                                    "_eq": "api_only"}}, {
                                "external_program": {}}]}, {
                            "_not": {
                                "external_program": {}}}, {
                            "_or": [{
                                "_and": [{
                                    "state": {
                                        "_neq": "sandboxed"}}, {
                                    "state": {
                                        "_neq": "soft_launched"}}]}, {
                                "external_program": {}}]}]},
                    "first": self.pages_per_req,
                    "secureOrderBy": {
                        "started_accepting_at": {
                            "_direction": "DESC"}},
                    "cursor": cursor},
                "query": "query DirectoryQuery($cursor: String, $secureOrderBy: FiltersTeamFilterOrder, $where: FiltersTeamFilterInput) {\n  me {\n    id\n    edit_unclaimed_profiles\n    h1_pentester\n    __typename\n  }\n  teams(first: " + str(self.pages_per_req) + ", after: $cursor, secure_order_by: $secureOrderBy, where: $where) {\n    pageInfo {\n      endCursor\n      hasNextPage\n      __typename\n    }\n    edges {\n      node {\n        id\n        bookmarked\n        ...TeamTableResolvedReports\n        ...TeamTableAvatarAndTitle\n        ...TeamTableLaunchDate\n        ...TeamTableMinimumBounty\n        ...TeamTableAverageBounty\n        ...BookmarkTeam\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment TeamTableResolvedReports on Team {\n  id\n  resolved_report_count\n  __typename\n}\n\nfragment TeamTableAvatarAndTitle on Team {\n  id\n  profile_picture(size: medium)\n  name\n  handle\n  submission_state\n  triage_active\n  publicly_visible_retesting\n  state\n  allows_bounty_splitting\n  external_program {\n    id\n    __typename\n  }\n  ...TeamLinkWithMiniProfile\n  __typename\n}\n\nfragment TeamLinkWithMiniProfile on Team {\n  id\n  handle\n  name\n  __typename\n}\n\nfragment TeamTableLaunchDate on Team {\n  id\n  started_accepting_at\n  __typename\n}\n\nfragment TeamTableMinimumBounty on Team {\n  id\n  currency\n  base_bounty\n  __typename\n}\n\nfragment TeamTableAverageBounty on Team {\n  id\n  currency\n  average_bounty_lower_amount\n  average_bounty_upper_amount\n  __typename\n}\n\nfragment BookmarkTeam on Team {\n  id\n  bookmarked\n  __typename\n}\n"}

    @staticmethod
    def _hql_in_scope_request_body(handle):
        """Сontain graphql request body for in scope directories parsing"""
        return {"operationName": "TeamAssets",
                "variables": {
                    "handle": handle},
                "query": "query TeamAssets($handle: String!) {\n  me {\n    id\n    membership(team_handle: $handle) {\n      id\n      permissions\n      __typename\n    }\n    __typename\n  }\n  team(handle: $handle) {\n    id\n    handle\n    structured_scope_versions(archived: false) {\n      max_updated_at\n      __typename\n    }\n    in_scope_assets: structured_scopes(first: 500, archived: false, eligible_for_submission: true) {\n      edges {\n        node {\n          id\n          asset_type\n          asset_identifier\n          rendered_instruction\n          max_severity\n          eligible_for_bounty\n          labels(first: 100) {\n            edges {\n              node {\n                id\n                name\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    out_scope_assets: structured_scopes(first: 500, archived: false, eligible_for_submission: false) {\n      edges {\n        node {\n          id\n          asset_type\n          asset_identifier\n          rendered_instruction\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"}


class DirectoryParse:
    def __init__(self, row_json_data):
        self._row_to_final_data_(row_json_data)

    def get_cursor(self):
        """Shift cursor getter"""
        return None if not self.cursor else self.cursor

    def get_dict(self):
        """Getter for {name: handle} return"""
        return None if not self.dir_dict else self.dir_dict

    def _row_to_final_data_(self, data):
        """Function for parsing directories"""
        self.dir_dict = {}
        self.cursor = data.json()['data']['teams']['pageInfo']['endCursor']
        for edge in data.json()['data']['teams']['edges']:
            self.dir_dict[edge['node']['name']] = edge['node']['handle']


class InScopeParse:
    def __init__(self, row_json_data):
        self._row_to_final_data_(row_json_data)

    def _row_to_final_data_(self, json_data):
        """Function parsing "in scope" list"""
        self._in_scope_list = list(map(lambda x: x['node']['asset_identifier'],
                                       json_data.json()['data']['team']['in_scope_assets']['edges']))

    def get_list(self):
        """Get list of "in scope" elements"""
        return None if not self._in_scope_list else self._in_scope_list


if __name__ == '__main__':
    main()
