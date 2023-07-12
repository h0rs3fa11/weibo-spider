import os
import csv
from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings

settings = get_project_settings()

class CsvPipeline(object):
    def process_item(self, item, spider):
        keyword = settings.get('FILE_NAME')
        base_dir = 'results' + os.sep + keyword
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)
        file_path = base_dir + os.sep + keyword + '.csv'
        if not os.path.isfile(file_path):
            is_first_write = 1
        else:
            is_first_write = 0
        if item:
            with open(file_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                if is_first_write:
                    header = [
                        'id', 'user_id', '用户昵称', '用户主页', '微博正文',
                        '发布位置', '发布时间'
                    ]
                    writer.writerow(header)
                writer.writerow(
                    [item[key] for key in item.keys()])
        return item

class DuplicatesPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['id'] in self.ids_seen:
            raise DropItem("过滤重复微博: %s" % item)
        else:
            self.ids_seen.add(item['id'])
            return item