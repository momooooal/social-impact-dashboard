import argparse, json
from collector_core import collect_all, git_sync, import_content_file, import_private_messages, setup_browser

p=argparse.ArgumentParser()
p.add_argument('--collect', action='store_true')
p.add_argument('--headed', action='store_true')
p.add_argument('--git-sync', action='store_true')
p.add_argument('--setup-browser', choices=['facebook','instagram','threads'])
p.add_argument('--import-content')
p.add_argument('--platform', default='auto')
p.add_argument('--import-messages')
a=p.parse_args()

if a.setup_browser:
    setup_browser(a.setup_browser)
elif a.import_content:
    print(json.dumps(import_content_file(a.import_content,a.platform), ensure_ascii=False, indent=2))
elif a.import_messages:
    print(json.dumps(import_private_messages(a.import_messages,a.platform), ensure_ascii=False, indent=2))
elif a.git_sync:
    print(json.dumps(git_sync(), ensure_ascii=False, indent=2))
else:
    print(json.dumps(collect_all(headed=a.headed), ensure_ascii=False, indent=2))
